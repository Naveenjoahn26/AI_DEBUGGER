from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class IterationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_TOOL = "awaiting_tool"
    COMPLETED = "completed"
    FAILED = "failed"
class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"
    ASSISTANT = "assistant"
class ToolCall(BaseModel):
    id: str = Field(description="unique identifier for tool")
    name: str = Field(description="name of the tool called")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="the keyword arguments")


class Observation(BaseModel):
    tool_call_id: str = Field(description="Matches the specific tool_call id this observation answers.")
    content: str = Field(description="The raw output or string representation of the tool excecution.")
    is_error: bool = Field(default=False, description="Flag indicating if the tool execution failed.")


class ChatMessage(BaseModel):
    """A individual entry in the conversation history."""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
class HandleToolCall(BaseModel):

    """ """
    tool_call_id: str = Field(description="unique identifier for tool")
    success:bool = Field(description="tool calling result is either true or false")
    content:str = Field(description="content of the tool call")
    
    error:str=Field(description="Error")
    max_iteration:int=Field(default=10, description="maximum number of iteration allowed")



from repository.agent.planning.models import Plan

class AgentState(BaseModel):
    """The central state machine tracking an active agent execution loop."""
    goal: str = Field(description="primary objective")
    messages: List[ChatMessage] = Field(default_factory=list, description="ordered log of messages")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="id to tool call mapping")
    observations: List[Observation] = Field(default_factory=list, description="observations from tools")
    plan: Optional[Plan] = Field(default=None, description="The current execution plan")
    iteration: int = Field(default=0)
    status: IterationStatus = Field(default=IterationStatus.PENDING)
    
    # 7.2 Token & Cost tracking
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost: float = Field(default=0.0)
    
    def add_message(self, message: ChatMessage):
        self.messages.append(message)

    def add_tool_call(self, tool_call: ToolCall):
        self.tool_calls.append(tool_call)

    def add_observation(self, observation: Observation):
        self.observations.append(observation)

    def increment_iteration(self):
        self.iteration += 1

    def add_usage(self, input_toks: int, output_toks: int, cost: float):
        self.input_tokens += input_toks
        self.output_tokens += output_toks
        self.total_tokens += (input_toks + output_toks)
        self.estimated_cost += cost
