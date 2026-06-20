# School Subjects Flask Project

This project is based on the uploaded school-subject wireframe design.

It uses:

- HTML
- CSS
- JavaScript
- Flask backend
- XAMPP / MySQL database
- Email verification for registered accounts
- Open Trivia DB API for subject practice questions

## Pages

| Route | Purpose | Login needed |
|---|---|---|
| `/` | Home page with school subjects and pricing levels | No |
| `/contact` | Contact page | No |
| `/about` | About page | No |
| `/register` | Join community/register | No |
| `/login` | Login page | No |
| `/dashboard` | User dashboard | Yes |
| `/grades?subject=math` | Grade selection | Yes |
| `/subject/math/7` | Subject page for a selected grade | Yes |
| `/tips?subject=math` | Learning tips | Yes |
| `/api/subject/math/quiz` | API route that calls Open Trivia DB | Yes |

## 1. Setup database in XAMPP

1. Open XAMPP.
2. Start Apache and MySQL.
3. Open phpMyAdmin.
4. Import `schema.sql`.

The database name is:

```text
school_subjects
```

The default XAMPP database login is:

```text
DB_USER=root
DB_PASSWORD=
```

## 2. Install Python packages

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Run the project

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## 4. Email verification testing without Gmail SMTP

By default, SMTP is empty:

```python
SMTP_USER = ""
SMTP_PASSWORD = ""
```

When you register, Flask prints the verification link in the terminal.

Copy the link, paste it into the browser, then login.

## 5. Real Gmail SMTP setup

Use a Gmail App Password, not your normal Gmail password.

In Windows CMD:

```cmd
set SMTP_USER=yourgmail@gmail.com
set SMTP_PASSWORD=your16digitapppassword
set MAIL_FROM=yourgmail@gmail.com
python app.py
```

In PowerShell:

```powershell
$env:SMTP_USER="yourgmail@gmail.com"
$env:SMTP_PASSWORD="your16digitapppassword"
$env:MAIL_FROM="yourgmail@gmail.com"
python app.py
```

## 6. Protecting pages

The project currently protects:

- Dashboard
- Grade selection
- Subject pages
- Tips page
- API quiz route

The home/contact/about/register/login pages are public.
