"""
repository/agent/llm_adapter.py

Thin adapter that wraps the Groq SDK client and makes it compatible
with the LLMClient Protocol expected by AgentRunner.

If GROQ_API_KEY is not configured, provides a local offline simulation agent
so that repository cloning, AST indexing, vector search, and UI streaming
can be explored end-to-end without crashing.
"""

import logging
import os
from types import SimpleNamespace
from typing import Any

from repository.agent.state.models import ChatMessage

logger = logging.getLogger(__name__)


class GroqAgentLLM:
    """
    Implements the LLMClient Protocol required by AgentRunner.

    Converts internal ChatMessage list → Groq SDK message dicts,
    calls the Groq chat completions API with tool support enabled,
    and returns a normalized response object.
    """

    def __init__(
        self,
        model_name: str | None = None,
        tools: list[Any] | None = None,
    ) -> None:
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = (
            model_name
            or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        )
        self.tools = tools or []

        if self.api_key:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        else:
            logger.warning(
                "GROQ_API_KEY is not set. Offline simulation agent activated for local demonstration."
            )
            self.client = None

    def invoke(self, messages: list[ChatMessage]) -> Any:
        if self.client is None:
            return self._invoke_offline_simulation(messages)

        import json as _json

        groq_messages = []
        pending_ids: list[str] = []
        id_index = 0

        for msg in messages:
            role = msg.role.value if hasattr(msg.role, "value") else msg.role

            if role == "assistant" and msg.tool_calls:
                pending_ids = [tc.id for tc in msg.tool_calls]
                id_index = 0
                groq_messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": _json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                })

            elif role == "tool":
                tcid = (
                    pending_ids[id_index]
                    if id_index < len(pending_ids)
                    else f"tool_result_{id_index}"
                )
                id_index += 1
                groq_messages.append({
                    "role": "tool",
                    "tool_call_id": tcid,
                    "content": msg.content or "",
                })

            else:
                groq_messages.append({
                    "role": role,
                    "content": msg.content or "",
                })

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": groq_messages,
        }

        if self.tools:
            groq_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": (
                            tool.args_schema.model_json_schema()
                            if hasattr(tool, "args_schema") and tool.args_schema
                            else {"type": "object", "properties": {}}
                        ),
                    },
                }
                for tool in self.tools
            ]
            kwargs["tools"] = groq_tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        return _GroqResponse(response)

    def _invoke_offline_simulation(self, messages: list[ChatMessage]) -> Any:
        """
        Offline fallback agent: executes realistic tool calls and synthesizes
        a diagnosis from real retrieved repository code without requiring an external API key.
        """
        # Check if we already received tool observations
        tool_messages = [
            m for m in messages
            if (m.role.value if hasattr(m.role, "value") else m.role) == "tool"
        ]

        user_messages = [
            m for m in messages
            if (m.role.value if hasattr(m.role, "value") else m.role) == "user"
        ]
        user_goal = user_messages[0].content if user_messages else "diagnose bug"

        if not tool_messages:
            # First turn: dispatch search_code tool call
            mock_tool = SimpleNamespace(
                id="call_offline_search",
                function=SimpleNamespace(
                    name="search_code",
                    arguments={"query": user_goal},
                )
            )
            return _MockResponse(
                tool_calls=[_ToolCallWrapper(mock_tool)],
                content="",
                model=f"{self.model_name} (simulation)",
                prompt_tokens=180,
                completion_tokens=32,
            )

        # Second turn: synthesize diagnosis from the real tool observation
        obs_text = tool_messages[0].content or ""
        import re
        files_found = list(set(re.findall(r"File:\s*([^\n]+)", obs_text)))
        files_str = ", ".join(f"`{f}`" for f in files_found[:3]) if files_found else "relevant codebase files"

        content = (
            f"> ℹ️ **Notice:** Running in local simulation mode. To enable live autonomous AI reasoning, "
            f"add your Groq API key to [`.env`](file:///c:/projects/AI%20DEBUGGER/.env).\n\n"
            f"### 🔍 Root Cause Analysis\n\n"
            f"**Investigated Issue:** {user_goal}\n\n"
            f"**Findings:**\n"
            f"Through hybrid BM25 and vector retrieval across the cloned repository, key code components in {files_str} "
            f"were identified as directly related to the reported behavior.\n\n"
            f"**Diagnosis:**\n"
            f"The logic in the retrieved routines either lacks boundary verification or fails to validate input state, "
            f"leading to the reported anomaly under the described execution condition.\n\n"
            f"**Recommended Fix:**\n"
            f"Review the extracted code segments shown below in the **Evidence** panel and ensure proper state checks and error handling are enforced."
        )

        return _MockResponse(
            tool_calls=None,
            content=content,
            model=f"{self.model_name} (simulation)",
            prompt_tokens=420,
            completion_tokens=185,
        )


class _GroqResponse:
    def __init__(self, completion) -> None:
        self._completion = completion
        self._message = completion.choices[0].message

    @property
    def tool_calls(self):
        raw = getattr(self._message, "tool_calls", None)
        if not raw:
            return None
        return [_ToolCallWrapper(tc) for tc in raw]

    @property
    def content(self) -> str | None:
        return self._message.content

    @property
    def usage(self):
        return self._completion.usage

    @property
    def model(self) -> str:
        return self._completion.model


class _ToolCallWrapper:
    def __init__(self, raw_tool_call) -> None:
        self._raw = raw_tool_call

    @property
    def id(self) -> str:
        return self._raw.id

    @property
    def name(self) -> str:
        return self._raw.function.name

    @property
    def arguments(self) -> dict:
        import json
        args = self._raw.function.arguments
        if isinstance(args, str):
            try:
                return json.loads(args)
            except json.JSONDecodeError:
                return {}
        return args or {}


class _MockResponse:
    def __init__(self, tool_calls, content: str, model: str, prompt_tokens: int, completion_tokens: int):
        self._tool_calls = tool_calls
        self._content = content
        self._model = model
        self.usage = SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    @property
    def tool_calls(self):
        return self._tool_calls

    @property
    def content(self) -> str:
        return self._content

    @property
    def model(self) -> str:
        return self._model
