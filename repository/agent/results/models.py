from typing import Optional
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    """Represents the outcome of a single tool execution."""
    tool_call_id: str = Field(description="The unique identifier of the tool call this result belongs to.")
    success: bool = Field(description="True if the tool executed successfully, False otherwise.")
    content: str = Field(default="", description="The output produced by the tool.")
    error: Optional[str] = Field(default=None, description="The error message if the tool failed.")
