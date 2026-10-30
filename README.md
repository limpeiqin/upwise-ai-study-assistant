# Upwise – AI Study Assistant

Upwise is an AI-powered study assistant built with Python and Streamlit. It helps students organize their study materials, revise lecture notes, practice quizzes, and monitor their learning progress.

## Features

- **AI Summary** – Summarize lecture notes.
- **AI Quiz** – Generate quizzes for practice.
- **Study Chatbot** – Ask questions to support learning.
- **AI Flashcards** – Create flashcards for revision.
- **AI Study Planner** – Organize study schedules.
- **AI Mind Map** – Organize concepts visually.
- **AI Weak Topic Detector** – Identify topics that need more revision.
- **Study Library** – Access study materials.
- **Quiz History** – Review previous quiz attempts, scores, and completion dates.
- **User Authentication** – Sign up and log in using Supabase.

## Technologies Used

- Python
- Streamlit
- Supabase
- Ollama
- Llama 3.2 1B
- Git and GitHub

## Installation and Setup

### Prerequisites

- Python
- Git
- An existing Supabase project
- Ollama, if using the local AI features

### 1. Clone the repository

```bash
git clone https://github.com/limpeiqin/upwise-ai-study-assistant.git
cd upwise-ai-study-assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root and configure the environment variables required by the application.

**Never upload your `.env` file or secret keys to GitHub.**

### 4. Run the application

```bash
python -m streamlit run app.py
```

If using local AI features, ensure Ollama is running and the model configured in the application is available.

## Security

- Keep credentials out of version control.
- Configure database access policies to protect user data.

## Future Improvements

- Improve the user interface and user experience.
- Expand application testing.
- Enhance learning progress tracking.

## 🎥 Project Demo

Watch the Upwise demonstration video:

[▶ Watch Upwise Demo on YouTube](https://youtu.be/E-J6_VpwFro?si=usBTCPoP0abT8TCQ)
