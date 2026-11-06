# AI Debugger 🕵️‍♂️💻

AI Debugger is an autonomous, AI-powered developer tool that investigates and diagnoses bugs in public Git repositories. Simply provide a GitHub URL and a bug description, and the AI agent will clone the repository, index the codebase, and autonomously search through the code to pinpoint the root cause.

![AI Debugger UI](ChatGPT%20Image%20Sep%2014,%202026,%2012_01_55%20PM.png)

## 🚀 Features

- **Autonomous Agent Loop**: An LLM-powered agent that forms hypotheses, searches codebases using tools, and iterates until it finds the root cause of the bug.
- **Advanced Code Retrieval (RAG)**: Utilizes a **Hybrid Search** approach combining Semantic Search (ChromaDB + embeddings) and Lexical Search (BM25) with Reciprocal Rank Fusion (RRF) for highly accurate code chunk retrieval.
- **Real-Time Execution Streaming**: Connects via Server-Sent Events (SSE) to stream live terminal logs, agent activity timelines, and metric updates directly to the frontend.
- **Minimal Monochrome UI**: A sleek, zero-dependency HTML/CSS/JS frontend designed for a professional developer aesthetic (no neon, no gradients, purely engineered).
- **Built-in Evaluation Framework**: Includes an evaluation suite to benchmark the pipeline against test datasets and measure retrieval accuracy and diagnostic success rates.

## 🏗️ Architecture

- **Backend**: Python 3.12, FastAPI, Uvicorn
- **AI/LLM**: Groq API (or any OpenAI-compatible provider)
- **Vector Database**: ChromaDB (Local SQLite)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6)

## 🛠️ Quickstart

### 1. Prerequisites
- Python 3.10+
- Git installed on your system

### 2. Setup the Backend
Clone the repository and install the dependencies:
```bash
git clone https://github.com/Naveenjoahn26/AI_DEBUGGER.git
cd AI_DEBUGGER
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your API keys. By default, the system uses the Groq API for LLM inference.
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

### 4. Run the Application

**Start the Backend Server:**
```bash
python run.py
```
*The backend will run on `http://localhost:8000`.*

**Start the Frontend Client:**
In a new terminal window, serve the frontend directory:
```bash
python -m http.server 5173 -d frontend
```
*Open `http://localhost:5173` in your browser to access the AI Debugger UI.*

## 🧪 Testing

The repository contains a full `pytest` suite covering unit tests and end-to-end integration tests.

```bash
# Run the complete test suite
python -m pytest tests/

# Run the evaluation benchmark suite
python -m pytest tests/evaluation/
```

## 📂 Repository Structure

- `backend/app/`: FastAPI application, routes, schemas, and services.
- `frontend/`: The minimal monochrome UI client.
- `repository/`: Core business logic containing:
  - `agent/`: The autonomous loop, LLM adapters, memory, and tools.
  - `embeddings/`: Code chunk formatting and vector database integration.
  - `evaluation/`: The internal framework for benchmarking AI performance.
  - `ingestion/`: Git cloning and codebase AST indexing/chunking logic.
  - `retrieval/`: Semantic, BM25, and Hybrid search implementations.
- `tests/`: Comprehensive unit and integration test suite.

## 📝 License
This project is open-source and available under the MIT License.
