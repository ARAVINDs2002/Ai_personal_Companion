# Personal AI Companion

A production-ready, locally hosted AI companion web application. This project provides a persistent and personalized AI chat experience, leveraging local LLMs and vector memory for a seamless, natural, and emotionally expressive interaction without relying on external APIs.

## 🌟 Key Features

*   **Local & Private**: Powered by **Ollama**, ensuring all your conversations and data stay entirely on your local machine.
*   **Persistent Memory**: Uses **FAISS** (Facebook AI Similarity Search) to remember past conversations, facts, and context across sessions, making the AI feel genuinely personalized.
*   **Human-Like Interaction**: Deep architectural focus on prompt engineering to drop robotic responses and disclaimers, focusing on a natural conversational flow.
*   **Beautiful UI**: A responsive, custom frontend dashboard (HTML/CSS/JS) designed for a smooth chatting experience.
*   **One-Click Startup**: An automated bash/batch script handles setting up the environment, launching the server, and opening the interface in your browser.

## 🛠️ Architecture

*   **Backend**: 
    *   **FastAPI**: Blazing fast Python web framework handling local API endpoints.
    *   **Ollama**: Local interface for executing open-source large language models.
    *   **FAISS & SentenceTransformers**: For embedding and storing conversation history, effectively creating a "long-term memory" system locally.
*   **Frontend**: Vanilla HTML, CSS, and modern JavaScript for fetching responses and rendering the chat stream dynamically.

## 🚀 Getting Started

### Prerequisites

*   **Python 3.x** (Miniconda/Anaconda recommended)
*   **Ollama** installed on your system with a model downloaded (e.g., `ollama run llama3`)

### Installation & Execution

1.  **Clone** this repository.
2.  **Install Prerequisites**: Ensure you have [Ollama](https://ollama.com/) and [Miniconda/Anaconda](https://docs.anaconda.com/miniconda/) installed.
3.  **One-Click Start**: Double-click **`run.bat`**. 
    *   It will automatically create the environment on the first run.
    *   It will ensure Ollama and the `mistral` model are ready.
    *   It will launch both the backend and the browser interface.

> [!TIP]
> Keep the backend terminal window open while chatting. You can close the launcher window once the browser opens.

## 📁 Repository Structure

```text
ai_companion/
│
├── backend/               # Python FastAPI application
│   ├── main.py            # API routes and application setup
│   ├── memory.py          # FAISS memory management and vector store
│   └── llm.py             # Ollama API integration and prompt engineering
│
├── frontend/              # Web user interface
│   ├── index.html         # Main dashboard markup
│   ├── style.css          # Chat themes and animations
│   └── script.js          # Client-side state and backend fetching
│
├── avatar/                # Personalization and profile assets
├── memory.json            # Flat-file backup / structured active memory state
└── run.bat                # Automated launcher script
```

## 🎯 Future Roadmap

*   Voice integration (STT/TTS capabilities)
*   Enhanced emotion detection mechanics module
*   Support for multiple distinct AI personas/agents
