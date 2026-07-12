from app.agent.schemas import UserInput, AgentResponse
from app.agent.planner import create_plan
from app.agent.executor import execute_plan
from app.agent.synthesizer import synthesize_response
import logging
import traceback

logger = logging.getLogger(__name__)

async def process_request(user_input: UserInput) -> AgentResponse:
    """
    Main orchestration loop:
    1. Plan
    2. Check Ambiguity
    3. Execute Tools
    4. Synthesize
    """
    plan_trace = []

    # 1. PLAN
    try:
        plan = await create_plan(user_input)
        plan_trace.append({"step": "Planning", "status": "completed", "details": plan.reasoning})
    except Exception as e:
        logger.error(f"Planning failed: {traceback.format_exc()}")
        return AgentResponse(
            answer=f"I'm sorry, the planning step failed: {str(e)}",
            plan_trace=[{"step": "Planning", "status": "stopped", "details": str(e)}],
            extracted_texts={}
        )
    
    # 2. CHECK AMBIGUITY
    if plan.is_ambiguous and plan.follow_up_question:
        plan_trace.append({"step": "Ambiguity Detected", "status": "stopped", "details": plan.follow_up_question})
        return AgentResponse(
            follow_up_question=plan.follow_up_question,
            plan_trace=plan_trace,
            extracted_texts={f.filename: f.extracted_text for f in user_input.files if f.extracted_text}
        )
        
    # 3. EXECUTE
    for call in plan.tool_calls:
        plan_trace.append({"step": f"Executing Tool: {call.tool_name}", "status": "running", "details": str(call.parameters)[:200]})
    
    try:
        tool_results = await execute_plan(plan, user_input.files)
        for res in tool_results:
            status = "completed" if res.status == "success" else "stopped"
            plan_trace.append({"step": f"Tool Result: {res.tool_name}", "status": status, "details": str(res.result)[:200]})
    except Exception as e:
        logger.error(f"Execution failed: {traceback.format_exc()}")
        return AgentResponse(
            answer=f"I'm sorry, tool execution failed: {str(e)}",
            plan_trace=plan_trace,
            extracted_texts={}
        )
    
    # 4. SYNTHESIZE
    try:
        final_answer = await synthesize_response(user_input, tool_results)
        plan_trace.append({"step": "Synthesis", "status": "completed", "details": "Final answer generated successfully."})
    except Exception as e:
        logger.error(f"Synthesis failed: {traceback.format_exc()}")
        final_answer = f"I'm sorry, I failed to synthesize the response: {str(e)}"
    
    return AgentResponse(
        answer=final_answer,
        plan_trace=plan_trace,
        extracted_texts={f.filename: f.extracted_text for f in user_input.files if f.extracted_text}
    )

