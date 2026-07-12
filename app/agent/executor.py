from app.agent.schemas import ExecutionPlan, ToolResult
from app.tools import execute_tool
import logging


logger = logging.getLogger(__name__)

async def execute_plan(plan: ExecutionPlan) -> list[ToolResult]:
    """
    Iterates through the tool calls in the execution plan and runs them.
    Supports output chaining: if a parameter value contains '{{previous_output}}',
    it is replaced with the result of the previous tool.
    """
    results = []
    previous_output = None

    for call in plan.tool_calls:
        try:
            # Replace {{previous_output}} placeholders in parameters
            resolved_params = {}
            for key, value in call.parameters.items():
                if isinstance(value, str) and "{{previous_output}}" in value:
                    if previous_output is not None:
                        resolved_params[key] = value.replace("{{previous_output}}", str(previous_output))
                    else:
                        resolved_params[key] = value
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

