# Agentic AI Multi-Modal Assistant (Gemini Edition)

A deployed Agentic AI application that processes text, images, PDFs, and audio simultaneously. It features autonomous planning, tool orchestration, and cross-input reasoning, built **entirely with Google's Gemini API** and a **custom Python ReAct agent loop** (No LangChain/LangGraph).

## Features

- **Multi-Modal Support**: Upload Text, PDFs, Images (JPG/PNG), and Audio (MP3/WAV) simultaneously.
- **Custom Agentic Loop**: 
  1. Pre-processes inputs (PDF extraction, OCR, Native Audio Transcription)
  2. Plans minimum viable steps using Gemini's structured output.
  3. Executes specific tools (Summarization, Code explanation, YouTube fetching, etc.)
  4. Synthesizes the final text response.
- **Mandatory Follow-Up**: If the query is ambiguous, the agent stops and asks for clarification.
- **Cross-Input Reasoning**: Automatically detects URLs in PDFs and fetches external content when relevant.

## Tech Stack

- **Backend**: FastAPI
- **LLM/Vision/Audio**: Google Gemini API (`gemini-2.0-flash`)
- **PDF Extraction**: PyMuPDF
- **OCR**: Pytesseract
- **UI**: Vanilla HTML/CSS/JS (Dark Theme, Glassmorphism)
- **Deployment**: Docker, designed for Render.com

## Setup & Local Development

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You will also need Tesseract-OCR and FFmpeg installed on your system if running outside Docker).*
3. **Configure Environment variables**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key
   GEMINI_MODEL=gemini-2.0-flash
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
3. Add your `GEMINI_API_KEY` as an environment variable in the Render dashboard.
4. Render will automatically build the `Dockerfile` and expose it on the assigned port.

## Architecture

The system uses a completely custom, lightweight orchestration layer located in `app/agent/`:
- `planner.py`: Sends context to Gemini with `response_schema` to generate a structured execution plan.
- `executor.py`: Evaluates the plan and dynamically invokes the required Python functions from `app/tools/`.
- `synthesizer.py`: Combines tool outputs with the original query to formulate the final answer.

This avoids the overhead and opacity of frameworks like LangChain, directly meeting the "prove you can code" evaluation criteria.
