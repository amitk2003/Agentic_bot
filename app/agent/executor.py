from app.agent.schemas import ExecutionPlan, ToolResult
from app.tools import execute_tool
import logging


logger = logging.getLogger(__name__)
import re

async def execute_plan(plan: ExecutionPlan, files: list = None) -> list[ToolResult]:
    """
    Iterates through the tool calls in the execution plan and runs them.
    Supports output chaining: if a parameter value contains '{{previous_output}}',
    it is replaced with the result of the previous tool.
    Also supports '{{file:filename}}' to inject extracted file text.
    """
    results = []
    previous_output = None

    for call in plan.tool_calls:
        try:
            # Replace placeholders in parameters
            resolved_params = {}
            for key, value in call.parameters.items():
                if isinstance(value, str):
                    val = value
                    if "{{previous_output}}" in val or "{previous_output}" in val:
                        if previous_output is not None:
                            val = val.replace("{{previous_output}}", str(previous_output))
                            val = val.replace("{previous_output}", str(previous_output))
                            
                    if files and ("{{file:" in val or "{file:" in val):
                        matches = re.findall(r'\{+file:([^}]+)\}+', val)
                        for match in matches:
                            filename = match.strip()
                            file_obj = next((f for f in files if f.filename == filename), None)
                            if file_obj and file_obj.extracted_text:
                                val = val.replace(f"{{{{file:{match}}}}}", file_obj.extracted_text)
                                val = val.replace(f"{{file:{match}}}", file_obj.extracted_text)
                                
                    resolved_params[key] = val
                else:
                    resolved_params[key] = value

            logger.info(f"Executing tool: {call.tool_name} with params: {list(resolved_params.keys())}")
            result_data = await execute_tool(call.tool_name, **resolved_params)
            previous_output = result_data
            results.append(ToolResult(
                tool_name=call.tool_name,
                result=result_data,
                status="success"
            ))
        except Exception as e:
            logger.error(f"Error executing {call.tool_name}: {str(e)}")
            results.append(ToolResult(
                tool_name=call.tool_name,
                result=f"Error: {str(e)}",
                status="error"
            ))
            previous_output = None

    return results

