import html
import random
import socket
import ssl
import smtplib
from email.message import EmailMessage
from functools import wraps

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for, flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from db import get_db_connection

app = Flask(__name__)
app.config.from_object(Config)

SUBJECTS = {
    "math": {
        "name": "Math",
        "api_category": 19,
        "description": "Practice numbers, algebra, geometry, and problem solving.",
    },
    "physics": {
        "name": "Physics",
        "api_category": 17,
        "description": "Explore forces, motion, energy, waves, and simple experiments.",
    },
    "biology": {
        "name": "Biology",
        "api_category": 17,
        "description": "Learn about living things, cells, plants, animals, and the human body.",
    },
    "english": {
        "name": "English",
        "api_category": 10,
        "description": "Improve reading, vocabulary, grammar, and communication skills.",
    },
    "literature": {
        "name": "Literature",
        "api_category": 10,
        "description": "Read stories, poems, characters, themes, and author ideas.",
    },
    "music": {
        "name": "Music",
        "api_category": 12,
        "description": "Study rhythm, instruments, composers, songs, and music history.",
    },
}

GRADE_LABELS = [f"Grade {number}" for number in range(1, 13)]

LEVELS = [
    {"name": "Elementary", "price": "$10", "grades": "Grade 1 - Grade 5"},
    {"name": "Secondary", "price": "$15", "grades": "Grade 6 - Grade 9"},
    {"name": "High School", "price": "$20", "grades": "Grade 10 - Grade 12"},
]

FALLBACK_QUESTIONS = {
    "math": [
        {"question": "What is 12 × 8?", "answers": ["96", "86", "108", "88"], "correct_answer": "96"},
        {"question": "How many degrees are in a right angle?", "answers": ["90", "45", "180", "360"], "correct_answer": "90"},
    ],
    "physics": [
        {"question": "What force pulls objects toward Earth?", "answers": ["Gravity", "Friction", "Magnetism", "Sound"], "correct_answer": "Gravity"},
        {"question": "What is the unit of force?", "answers": ["Newton", "Joule", "Watt", "Volt"], "correct_answer": "Newton"},
    ],
    "biology": [
        {"question": "What part of a plant absorbs water?", "answers": ["Roots", "Flowers", "Leaves", "Fruit"], "correct_answer": "Roots"},
        {"question": "What do humans use to breathe?", "answers": ["Lungs", "Kidneys", "Stomach", "Bones"], "correct_answer": "Lungs"},
    ],
    "english": [
        {"question": "Which word is a noun?", "answers": ["Book", "Quickly", "Beautiful", "Run"], "correct_answer": "Book"},
        {"question": "Which sentence is correct?", "answers": ["She is reading.", "She are reading.", "She am reading.", "She be reading."], "correct_answer": "She is reading."},
    ],
    "literature": [
        {"question": "Who writes a poem?", "answers": ["A poet", "A pilot", "A doctor", "A builder"], "correct_answer": "A poet"},
        {"question": "What is the main person in a story called?", "answers": ["Character", "Chapter", "Setting", "Title"], "correct_answer": "Character"},
    ],
    "music": [
        {"question": "Which instrument has black and white keys?", "answers": ["Piano", "Drum", "Guitar", "Flute"], "correct_answer": "Piano"},
        {"question": "What do we call the speed of music?", "answers": ["Tempo", "Color", "Shape", "Chapter"], "correct_answer": "Tempo"},
    ],
}


def login_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "error")
            return redirect(url_for("login", next=request.path))
        return view_function(*args, **kwargs)
    return wrapper


def get_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def make_verify_token(email):
    return get_serializer().dumps(email, salt="email-verification")


def read_verify_token(token):
    return get_serializer().loads(
        token,
        salt="email-verification",
        max_age=app.config["TOKEN_MAX_AGE_SECONDS"],
    )


def send_verification_email(email, username):
    token = make_verify_token(email)
    verify_url = url_for("verify_email", token=token, _external=True)

    subject = "Verify your School Subjects account"
    body = f"""Hello {username},

Click this link to verify your account:
{verify_url}

This link expires in 24 hours.

If you did not register, ignore this email.
"""

    if not app.config["SMTP_USER"] or not app.config["SMTP_PASSWORD"]:
        print("\n--- EMAIL NOT SENT: SMTP is not configured ---")
        print(f"Verification link for {email}: {verify_url}")
        print("--------------------------------------------\n")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = app.config["MAIL_FROM"]
    message["To"] = email
    message.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(app.config["SMTP_HOST"], app.config["SMTP_PORT"], timeout=15) as server:
            server.starttls(context=context)
            server.login(app.config["SMTP_USER"], app.config["SMTP_PASSWORD"])
            server.send_message(message)
        return True
    except (socket.gaierror, smtplib.SMTPException, OSError) as error:
        print("\n--- EMAIL SEND FAILED ---")
        print("Reason:", error)
        print(f"Verification link for {email}: {verify_url}")
        print("-------------------------\n")
        return False


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email, is_verified FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user


@app.context_processor
def inject_common_data():
    return {
        "current_user": get_current_user(),
        "subjects": SUBJECTS,
    }


@app.route("/")
def home():
    return render_template("home.html", levels=LEVELS, title="Home")


@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact Us")


@app.route("/about")
def about():
    return render_template("about.html", title="About Us")


@app.route("/grades")
@login_required
def grades():
    subject = request.args.get("subject", "math").lower()
    if subject not in SUBJECTS:
        subject = "math"
    return render_template("grades.html", grades=GRADE_LABELS, selected_subject=subject, title="Choose Grade")


@app.route("/subject/<subject>/<int:grade>")
@login_required
def subject_page(subject, grade):
    subject = subject.lower()
    if subject not in SUBJECTS:
        flash("Subject not found.", "error")
        return redirect(url_for("home"))
    if grade < 1 or grade > 12:
        flash("Grade not found.", "error")
        return redirect(url_for("grades", subject=subject))
    return render_template("subject.html", subject_key=subject, grade=grade, title=SUBJECTS[subject]["name"])


@app.route("/tips")
@login_required
def tips():
    subject = request.args.get("subject", "math").lower()
    if subject not in SUBJECTS:
        subject = "math"
    return render_template("tips.html", subject_key=subject, title="Tips for Learning")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html", title="Join Our Community")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html", title="Join Our Community")

        password_hash = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            connection.close()
            flash("This email is already registered.", "error")
            return render_template("register.html", title="Join Our Community")

        cursor.execute(
            "INSERT INTO users (username, email, password_hash, is_verified) VALUES (%s, %s, %s, 0)",
            (username, email, password_hash),
        )
        connection.commit()
        cursor.close()
        connection.close()

        email_sent = send_verification_email(email, username)
        if email_sent:
            flash("Account created. Please check your email to verify your account.", "success")
        else:
            flash("Account created. Email was not sent, so use the verification link printed in the Flask terminal.", "warning")
        return redirect(url_for("login"))

    return render_template("register.html", title="Join Our Community")


@app.route("/verify/<token>")
def verify_email(token):
    try:
        email = read_verify_token(token)
    except SignatureExpired:
        flash("Verification link expired. Please request a new one.", "error")
        return redirect(url_for("resend_verification"))
    except BadSignature:
        flash("Invalid verification link.", "error")
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        connection.close()
        flash("Account not found.", "error")
        return redirect(url_for("register"))

    if not user["is_verified"]:
        cursor.execute(
            "UPDATE users SET is_verified = 1, verified_at = CURRENT_TIMESTAMP WHERE email = %s",
            (email,),
        )
        connection.commit()

    cursor.close()
    connection.close()
    flash("Email verified. You can login now.", "success")
    return redirect(url_for("login"))


@app.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT username, is_verified FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if not user:
            flash("Email not found.", "error")
        elif user["is_verified"]:
            flash("This account is already verified.", "success")
        else:
            email_sent = send_verification_email(email, user["username"])
            if email_sent:
                flash("Verification email sent.", "success")
            else:
                flash("Email was not sent. Use the verification link printed in the Flask terminal.", "warning")
        return redirect(url_for("login"))

    return render_template("resend_verification.html", title="Resend Verification")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html", title="Login")

        if not user["is_verified"]:
            flash("Please verify your email before logging in.", "error")
            return redirect(url_for("resend_verification"))

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard"))

    return render_template("login.html", title="Login")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/api/subject/<subject>/quiz")
@login_required
def api_subject_quiz(subject):
    subject = subject.lower()
    if subject not in SUBJECTS:
        return jsonify({"error": "Subject not found"}), 404

    category_id = SUBJECTS[subject]["api_category"]
    amount = request.args.get("amount", 6, type=int)
    amount = max(1, min(amount, 10))

    try:
        response = requests.get(
            f"{app.config['OPENTDB_BASE_URL']}/api.php",
            params={"amount": amount, "category": category_id, "type": "multiple"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        questions = []

        for item in data.get("results", []):
            correct_answer = html.unescape(item.get("correct_answer", ""))
            answers = [html.unescape(answer) for answer in item.get("incorrect_answers", [])]
            answers.append(correct_answer)
            random.shuffle(answers)

            questions.append({
                "question": html.unescape(item.get("question", "")),
                "answers": answers,
                "correct_answer": correct_answer,
                "difficulty": item.get("difficulty", "mixed"),
                "source": "Open Trivia DB",
            })

        if questions:
            return jsonify({"subject": SUBJECTS[subject]["name"], "questions": questions})
    except requests.RequestException as error:
        print("OpenTDB API failed:", error)

    return jsonify({
        "subject": SUBJECTS[subject]["name"],
        "questions": FALLBACK_QUESTIONS.get(subject, []),
        "fallback": True,
    })


if __name__ == "__main__":
    app.run(debug=True)
