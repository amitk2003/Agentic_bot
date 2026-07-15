from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import tempfile
import uuid
import asyncio

from app.config import Config
from app.agent.schemas import UserInput, FileMetadata
from app.agent.orchestrator import process_request
from app.utils.extractors import extract_text_from_pdf, extract_text_from_image
from app.utils.audio_extractor import extract_audio_transcript
from app import db
from app.groq_client import generate_content as groq_generate

async def generate_and_save_title(conversation_id: str, query: str):
    """Background task to generate a smart title using Groq."""
    try:
        title = groq_generate(
            f"Write a very short (3 to 5 words max) title summarizing this user request. Don't use quotes or punctuation. Just the title, nothing else. Request: {query}",
            system_prompt="You are a title generator. Output only the title.",
            temperature=0.7,
        )
        title = title.strip()[:50]
        await db.update_conversation_title(conversation_id, title)
    except Exception as e:
        print(f"Failed to generate title: {e}")

app = FastAPI(title="OmniAgent AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    print("Groq Model:", Config.GROQ_MODEL)
    print("Upload Directory:", Config.UPLOAD_DIR)
    await db.init_db()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# ===== Conversation CRUD =====

@app.get("/api/conversations")
async def list_conversations():
    convs = await db.list_conversations()
    return convs

@app.post("/api/conversations")
async def create_conversation():
    conv = await db.create_conversation()
    return conv

@app.get("/api/conversations/{conv_id}/messages")
async def get_messages(conv_id: str):
    msgs = await db.get_messages(conv_id)
    return msgs

@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    await db.delete_conversation(conv_id)
    return {"status": "deleted"}

@app.put("/api/conversations/{conv_id}/rename")
async def rename_conversation(conv_id: str, title: str = Form(...)):
    await db.rename_conversation(conv_id, title)
    return {"status": "renamed"}

# ===== Main Chat Endpoint =====

@app.post("/api/chat")
async def chat(
    query: str = Form(""),
    conversation_id: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):
    try:
        # Save user message to DB (include extracted file text for memory)
        processed_files = []
        if files:
            for file in files:
                if not file.filename:
                    continue

                # Read file contents and save to system temp directory to avoid uvicorn reload
                file_ext = file.filename.split(".")[-1].lower()
                temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.{file_ext}")

                with open(temp_path, "wb") as f:
                    f.write(await file.read())

                # Pre-processing extraction (run in thread to avoid blocking)
                extracted_text = None
                if file_ext == "pdf":
                    extracted_text = await asyncio.to_thread(extract_text_from_pdf, temp_path)
                elif file_ext in ["jpg", "jpeg", "png"]:
                    extracted_text = await asyncio.to_thread(extract_text_from_image, temp_path)
                elif file_ext in ["mp3", "wav", "m4a"]:
                    extracted_text = await asyncio.to_thread(extract_audio_transcript, temp_path)

                processed_files.append(
                    FileMetadata(
                        filename=file.filename,
                        content_type=file.content_type,
                        extracted_text=extracted_text,
                        file_path=temp_path
                    )
                )

        # Build the full user message content (include file extractions for memory)
        full_user_content = query
        for pf in processed_files:
            if pf.extracted_text:
                full_user_content += f"\n\n[Attached File: {pf.filename}]\n{pf.extracted_text}"

        await db.add_message(conversation_id, "user", full_user_content)

        # Auto-title the conversation from the first user message
        msgs = await db.get_messages(conversation_id)
        user_msgs = [m for m in msgs if m["role"] == "user"]
        # Only title if we have an actual query to summarize
        if len(user_msgs) == 1 and query.strip():
            temp_title = query[:50].strip() + ("..." if len(query) > 50 else "")
            await db.update_conversation_title(conversation_id, temp_title)
            asyncio.create_task(generate_and_save_title(conversation_id, query))

        # Build chat history for context (exclude the current message, limit to last 20)
        all_msgs = await db.get_messages(conversation_id)
        chat_history = [{"role": m["role"], "content": m["content"]} for m in all_msgs[:-1]][-20:]

        user_input = UserInput(query=query, files=processed_files, chat_history=chat_history)
        response = await process_request(user_input)

        # Save assistant response to DB
        answer_text = response.answer or response.follow_up_question or ""
        if answer_text:
            await db.add_message(conversation_id, "assistant", answer_text)

        result = response.model_dump()
        result["conversation_id"] = conversation_id
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))