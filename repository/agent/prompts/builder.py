from typing import Any, Dict, List, Optional

from repository.agent.prompts.system import SYSTEM_PROMPT, TOOL_USAGE_TEMPLATE
from repository.agent.state.models import ChatMessage
from repository.agent.planning.models import Plan, PlanStepStatus
from repository.agent.memory.models import Memory


class PromptBuilder:
    """Builds and manages prompts for the Agent."""

    @staticmethod
    def build(
        goal: str, 
        tools: List[Any] = None, 
        conversation: List[ChatMessage] = None,
        plan: Optional[Plan] = None,
        memories: Optional[List[Memory]] = None
    ) -> str:
        """
        Constructs the complete prompt including system directives,
        project memory, tool descriptions, the current goal, plan progress, 
        and conversation history.
        """
        # 1. System Prompt
        prompt = SYSTEM_PROMPT.strip()

        # 2. Project Memory
        if memories:
            prompt += "\n\n# Project Memory"
            for mem in memories:
                prompt += f"\n- {mem.content}"

        # 3. Tool Usage
        if tools:
            tool_descriptions = PromptBuilder._format_tools(tools)
            tool_section = TOOL_USAGE_TEMPLATE.format(tool_descriptions=tool_descriptions)
            prompt += f"\n\n{tool_section.strip()}"

        # 4. Goal
        prompt += f"\n\n# Goal\n{goal}"

        # 5. Plan
        if plan and plan.steps:
            prompt += "\n\n# Current Plan"
            for idx, step in enumerate(plan.steps):
                status_str = step.status.value
                prompt += f"\n{idx + 1}. [{status_str}] {step.description}"
            
            if 0 <= plan.current_step < len(plan.steps):
                prompt += f"\n\n# Current Step\n{plan.steps[plan.current_step].description}"

        # 6. Conversation History
        if conversation:
            prompt += "\n\n# Conversation History"
            for msg in conversation:
                role_label = msg.role.value.upper() if hasattr(msg.role, "value") else str(msg.role).upper()
                content = msg.content or ""
                prompt += f"\n**{role_label}**:\n{content}"

        return prompt.strip()

    @staticmethod
    def _format_tools(tools: List[Any]) -> str:
        """Formats a list of tool objects into a readable string."""
        formatted = []
        for tool in tools:
            name = getattr(tool, "name", "UnknownTool")
            desc = getattr(tool, "description", "No description provided.")
            
            args_str = ""
            if hasattr(tool, "args_schema") and tool.args_schema:
                schema_props = tool.args_schema.model_json_schema().get("properties", {})
                args = [f"{k} ({v.get('type', 'any')})" for k, v in schema_props.items()]
                args_str = f"\n  Arguments: {', '.join(args)}"

            formatted.append(f"- **{name}**: {desc}{args_str}")
            
        return "\n".join(formatted)