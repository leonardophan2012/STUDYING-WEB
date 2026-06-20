document.addEventListener("DOMContentLoaded", () => {
    const quizButton = document.getElementById("loadQuizBtn");
    if (!quizButton) return;

    quizButton.addEventListener("click", async () => {
        const subject = quizButton.dataset.subject;
        const status = document.getElementById("quizStatus");
        const list = document.getElementById("quizList");

        status.textContent = "Loading questions...";
        list.innerHTML = "";

        try {
            const response = await fetch(`/api/subject/${encodeURIComponent(subject)}/quiz?amount=6`);
            if (!response.ok) {
                throw new Error("API request failed");
            }

            const data = await response.json();
            const questions = data.questions || [];

            if (!questions.length) {
                status.textContent = "No questions found.";
                return;
            }

            status.textContent = data.fallback
                ? "Using local fallback questions because the external API failed."
                : `Loaded ${questions.length} questions from API.`;

            questions.forEach((question, index) => {
                const card = document.createElement("article");
                card.className = "quiz-card";

                const title = document.createElement("h3");
                title.textContent = `${index + 1}. ${question.question}`;
                card.appendChild(title);

                const answers = document.createElement("ul");
                question.answers.forEach((answer) => {
                    const item = document.createElement("li");
                    item.textContent = answer;
                    answers.appendChild(item);
                });
                card.appendChild(answers);

                const correct = document.createElement("p");
                correct.innerHTML = `<strong>Correct answer:</strong> ${question.correct_answer}`;
                card.appendChild(correct);

                list.appendChild(card);
            });
        } catch (error) {
            status.textContent = "Could not load questions. Please try again later.";
        }
    });
});
