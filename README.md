# 📚 Bookinator V2

**The AI-Powered "Mind Reading" Book Guessing Game**

Bookinator is a local, privacy-focused web application designed for the **Kolkata Book Fair**. It acts like a "Literary Akinator," guessing the book you are thinking of through a series of Yes/No questions.

It specifically specializes in **Bengali Literature** (Feluda, Byomkesh, Tagore, etc.) but works for general books too.

---

## 🚀 Features

*   **Diffused Knowledge Engine**: Hybrid architecture combining a **Local LLM (Llama 3)**, **Vector Search** (CSV knowledge base), and **Web Search** (DuckDuckGo).
*   **Cultural Intelligence**: Specialized training for Bengali contexts (Kallol Jug, Ghoti/Bangal, Iconic Characters).
*   **"Mind Reader" UI**: Immersive, chat-free interface with a "Thinking..." state and strict 20-question "Sudden Death" mechanic.
*   **Privacy First**: Runs 100% locally using Ollama. No data leaves your machine unless a web search is strictly required.

---

## 🛠️ Prerequisites

1.  **Python 3.10+**: [Download Here](https://www.python.org/downloads/)
2.  **Ollama**: [Download Here](https://ollama.com/)
    *   *Required for the AI Brain.*
    *   After installing, pull the model:
        ```bash
        ollama pull llama3.2
        ```
    *   **Crucial Step**: You must start the Ollama server in a separate terminal before running the app:
        ```bash
        ollama serve
        ```

---

## 📦 Installation

1.  **Clone/Download** this repository.
2.  **Run the Setup Script** (Windows):
    Double-click `run.bat`.
    *   This will automatically create a virtual environment, install dependencies, and start the app.

    *Alternatively (Manual Setup):*
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py
    ```

---

## 🎮 How to Play

1.  Ensure `ollama serve` is running in the background.
2.  Start the app via `run.bat` or `python app.py`.
3.  Open your browser to `http://127.0.0.1:5000`.
4.  **Think of a book** (e.g., *Sonar Kella*).
5.  Answer the AI's questions with the buttons (Yes, No, Probably, etc.).
6.  **The Challenge**: The AI has **20 Questions** to guess it.
    *   If it guesses right -> Click "Yes, I Win!"
    *   If it fails after 20 -> You Win! (And you can teach it the answer).

---

## 🧠 Tech Stack

*   **Backend**: Flask (Python)
*   **AI Engine**: Ollama (Llama 3.2), DuckDuckGo Search (DDGS)
*   **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JS
*   **Data**: Local CSV Knowledge Base (~11k books)

---

## 📂 Project Structure

*   `app.py`: Flask backend server.
*   `llm_engine.py`: The brain. Handles Prompt Engineering, Context Management, and Hybrid Search logic.
*   `data/books.csv`: The local knowledge base.
*   `static/`: CSS and JS files.
*   `templates/`: HTML templates.

---

