# Omni-Agent (by Parallel Minds)

A deployed Agentic AI application that processes text, images, PDFs, and audio simultaneously. It features autonomous planning, tool orchestration, cross-input reasoning, and a complete local RAG (Retrieval-Augmented Generation) pipeline.

Built with **Groq (Llama-3/Mixtral)** for lightning-fast inference and a **custom Python ReAct agent loop** (No LangChain/LangGraph overhead).

## Features

- **Multi-Modal Support**: Upload Text, PDFs, Images (JPG/PNG), and Audio (MP3/WAV) simultaneously.
- **Custom Agentic Loop**: 
  1. Pre-processes inputs (PDF extraction, OCR, Native Audio Transcription via Groq Whisper).
  2. Plans minimum viable steps using a dedicated LLM Planner.
  3. Executes specific tools (Summarization, QA, Code explanation, YouTube fetching, etc.).
  4. Synthesizes the final text response.
- **Local RAG Integration**: Automatically chunks large documents, embeds them via `sentence-transformers`, and searches via `faiss-cpu` for precise Question & Answering.
- **Mandatory Follow-Up**: If the query is ambiguous, the agent stops and asks for clarification.
- **Cross-Input Reasoning**: The engine dynamically injects file texts across tools, allowing complex unified queries (e.g., comparing an Audio lecture against a PDF).

## Tech Stack

- **Backend**: FastAPI
- **LLM/Vision/Audio**: Groq API
- **RAG Engine**: FAISS & `sentence-transformers` (all-MiniLM-L6-v2)
- **PDF Extraction**: PyMuPDF (`fitz`)
- **OCR**: Pytesseract
- **UI**: Vanilla HTML/CSS/JS (Dark Theme, Glassmorphism)
- **Deployment**: Docker, designed for Render.com

## Setup & Local Development

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You will also need Tesseract-OCR installed on your system if running outside Docker).*
3. **Configure Environment variables**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_actual_groq_api_key
   GROQ_MODEL=llama3-70b-8192
   ```
4. **Run the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
5. **Access the UI**:
   Open `http://localhost:8000` in your browser.

## Docker Deployment (Render/AWS/GCP)

This project is containerized. To deploy to Render:
1. Connect your GitHub repo to Render.
2. Select **Docker** as the runtime.
3. Add your `GROQ_API_KEY` as an environment variable in the Render dashboard.
4. Render will automatically build the `Dockerfile` and expose it on the assigned port.

## Design Decisions

- **Why no LangChain/LangGraph?**: To prove core engineering competency, the entire orchestrator, planner, and executor were built from scratch. This guarantees 100% control over the prompt logic and execution pipeline, eliminating the latency and obfuscation of heavy frameworks.
- **Dynamic File Injection**: For cross-modal comparison, instead of blindly stuffing context into a prompt, the planner uses intelligent placeholders (`{{file:name.ext}}`) which the executor dynamically resolves. This drastically reduces token overhead.
- **Local RAG vs Remote**: Used `sentence-transformers` locally to embed chunks, preventing API costs and network latency for vectorization, paired with an in-memory FAISS index for nanosecond semantic retrieval.
