from typing import Any, Dict
from repository.agent.results.models import ToolResult

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool: Any):
        """Register a tool by its name attribute."""
        if not hasattr(tool, 'name'):
            raise ValueError("Tool must have a 'name' attribute.")
        self._tools[tool.name] = tool

    def get_all_tools(self) -> list[Any]:
        """Returns a list of all registered tools."""
        return list(self._tools.values())

    def execute(self, tool_call_id: str, tool_name: str, **kwargs) -> ToolResult:
        """Find a tool, validate inputs, and execute it. Returns a ToolResult."""
        if tool_name not in self._tools:
            return ToolResult(
                tool_call_id=tool_call_id,
                success=False,
                error=f"Unknown tool: '{tool_name}'"
            )

        tool = self._tools[tool_name]
        
        try:
            if hasattr(tool, 'args_schema') and tool.args_schema is not None:
                # Validate input arguments against Pydantic schema
                validated_args = tool.args_schema(**kwargs)
                # Pass validated arguments to the execute method
                output = tool.execute(**validated_args.model_dump())
            else:
                output = tool.execute(**kwargs)
                
            return ToolResult(
                tool_call_id=tool_call_id,
                success=True,
                content=str(output)
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call_id,
                success=False,
                error=str(e)
            )
