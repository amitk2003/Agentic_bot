import json

from app.agent.schemas import UserInput, ExecutionPlan
from app.tools import get_all_tool_schemas
from app.groq_client import generate_content


async def create_plan(user_input: UserInput) -> ExecutionPlan:
    """
    Uses the LLM to create an execution plan.
    """

    context = ""

    # Include conversation history for multi-turn context
    if user_input.chat_history:
        context += "CONVERSATION HISTORY (previous messages):\n"
        for msg in user_input.chat_history[-10:]:  # Last 10 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            # Truncate very long messages to avoid token overflow
            content = msg["content"][:2000] if len(msg["content"]) > 2000 else msg["content"]
            context += f"{role}: {content}\n\n"
        context += "========================================\n\n"

    context += f"CURRENT User Query:\n{user_input.query}\n\n"

    if user_input.files:
        context += "Uploaded Files:\n"

        for f in user_input.files:
            # Truncate extracted text for the planner (it only needs enough to decide which tool to use)
            extracted_preview = f.extracted_text or ""
            if len(extracted_preview) > 15000:
                extracted_preview = extracted_preview[:15000] + "\n... [truncated for planning, full text will be passed to the tool]"
            context += f"""
Filename: {f.filename}
Content Type: {f.content_type}

Extracted Text:
{extracted_preview}

----------------------------------------
"""

    tools = get_all_tool_schemas()

    prompt = f"""
You are the planning engine of an autonomous AI Agent.

You NEVER answer the user's question.

Your ONLY responsibility is to create an execution plan.

The executor will execute every tool you return.

====================================================

AVAILABLE TOOLS

{json.dumps(tools, indent=2)}

====================================================

GENERAL RULES

1. Never answer directly.

2. Never ask the user for information if any tool can obtain it.

3. Use the minimum number of tools.

4. Use uploaded file contents whenever available.

5. Only ask follow-up questions if NO tool can solve the task.

====================================================

WHEN TO USE TOOLS

summarize_text
- summarize PDFs
- summarize images
- summarize OCR text
- summarize YouTube transcript
- summarize audio transcript

qa_tool
- answer questions from uploaded documents
- answer questions from extracted PDFs
- answer questions from OCR text

Parameters:
context = extracted text
question = user question

compare_documents
- compare two documents

analyze_sentiment
- user requests sentiment

explain_code
- uploaded code
- pasted code
- OCR extracted code

fetch_youtube_transcript
- whenever a YouTube URL exists

If YouTube URL exists:

DO NOT ask user for transcript.

Plan:

fetch_youtube_transcript

↓

summarize_text

Pass

"text":"{{previous_output}}"

fetch_web_content
- whenever the user provides an external URL (like LinkedIn, blogs, websites)
- whenever you need to fetch information from a link

If external URL exists:

Plan:

fetch_web_content

↓

summarize_text (or other relevant tool)

Pass

"text":"{{previous_output}}"



compare_documents
- compare two documents
- evaluate if an uploaded document agrees with a video or audio file

If comparing a video/audio URL and an uploaded file:

Plan:

fetch_youtube_transcript (or fetch_web_content)

↓

compare_documents

Pass

"text_a":"{{previous_output}}"
"text_b":"<extracted text from uploaded file>"
"query":"<user's comparison query>"

If comparing two uploaded files (e.g., Audio + PDF):

Plan:

compare_documents

Pass

"text_a":"{{file:<filename 1>}}"
"text_b":"{{file:<filename 2>}}"
"query":"<user's comparison query>"

NOTE: Use {{file:<filename>}} to automatically inject the file's extracted text. DO NOT copy-paste the long extracted text yourself.

direct_answer
- greetings (hello, hi, etc.)
- general knowledge questions with no file or URL
- follow-up questions that can be answered from conversation history alone

CONVERSATION HISTORY RULES

If the user refers to "the file I uploaded" or "the assignment" or "previously",
look at the conversation history for the relevant content.
If the content is in the history, use qa_tool with
context = the relevant text from conversation history
question = the user's current question.
If there is NO relevant history and NO uploaded file, set is_ambiguous = true.

====================================================

Return ONLY JSON.

Example:

{{
"is_ambiguous":false,
"follow_up_question":"",
"tool_calls":[
{{
"tool_name":"summarize_text",
"parameters":{{
"text":"hello"
}}
}}
],
"reasoning":"..."
}}

====================================================

INPUT

{context}

"""

    try:

        response = generate_content(prompt)

        response = response.strip()

        if response.startswith("```"):
            response = response.replace("```json", "").replace("```", "").strip()

        plan = json.loads(response)

        print("\n========== PLAN ==========")
        print(json.dumps(plan, indent=2))
        print("==========================\n")

        return ExecutionPlan(**plan)

    except Exception as e:

        import traceback

        traceback.print_exc()

        return ExecutionPlan(
            is_ambiguous=True,
            follow_up_question=f"I encountered an error trying to plan this task: {str(e)}. Could you try rephrasing or uploading a smaller file?",
            reasoning=f"Planner Error: {str(e)}"
        )