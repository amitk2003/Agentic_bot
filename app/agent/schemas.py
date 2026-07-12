from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class FileMetadata(BaseModel):
    filename: str
    content_type: str
    extracted_text: Optional[str] = None
    file_path: Optional[str] = None


class UserInput(BaseModel):
    query: str
    files: List[FileMetadata] = Field(default_factory=list)
    chat_history: List[Dict[str, Any]] = Field(default_factory=list)


class ToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class ExecutionPlan(BaseModel):
    is_ambiguous: bool = Field(
        description="True if the user intent is unclear or multiple tasks are equally plausible."
    )

    follow_up_question: Optional[str] = Field(
        default=None,
        description="Question to ask the user if the request is ambiguous."
    )

    tool_calls: List[ToolCall] = Field(
        default_factory=list,
        description="Ordered list of tools to execute."
    )

    reasoning: str = Field(
        description="Brief explanation of why this plan was chosen."
    )


class ToolResult(BaseModel):
    tool_name: str
    result: Any
    status: str = "success"


class AgentResponse(BaseModel):
    answer: Optional[str] = None
    follow_up_question: Optional[str] = None

    plan_trace: List[Dict[str, Any]] = Field(default_factory=list)

    extracted_texts: Dict[str, str] = Field(default_factory=dict)