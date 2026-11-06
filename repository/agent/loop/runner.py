from typing import Any, Callable, Optional, Protocol

from repository.agent.state.models import (
    AgentState,
    ChatMessage,
    IterationStatus,
    Observation,
    ToolCall,
)
from repository.agent.tools.registry import ToolRegistry
from repository.agent.memory.store import MemoryStore
from repository.agent.prompts.builder import PromptBuilder
from repository.agent.cost import calculate_cost
import logging
import time

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Minimal interface required by AgentRunner."""

    def invoke(
        self,
        messages: list[ChatMessage],
    ) -> Any:
        ...


class AgentRunner:
    """Orchestrates the LLM -> tool -> observation loop."""

    def __init__(
        self,
        llm: LLMClient,
        tool_registry: ToolRegistry,
        memory_store: Optional[MemoryStore] = None,
        max_iterations: int = 5,
    ) -> None:
        self.llm = llm
        self.tool_registry = tool_registry
        self.memory_store = memory_store
        self.max_iterations = max_iterations

    def run(
        self,
        goal: str,
        on_event: Optional[Callable[[str, str, dict], None]] = None,
    ) -> AgentState:
        agent_start_time = time.time()
        logger.info("agent_started: Goal received", extra={"goal_length": len(goal)})

        if on_event:
            on_event("agent_started", "Agent started reasoning", {"goal_length": len(goal)})

        state = AgentState(
            goal=goal,
            status=IterationStatus.RUNNING,
        )

        state.messages.append(
            ChatMessage(
                role="user",
                content=goal,
            )
        )

        while state.iteration < self.max_iterations:
            state.iteration += 1

            memories = self.memory_store.search(state.goal) if self.memory_store else None
            
            system_content = PromptBuilder.build(
                goal=state.goal,
                tools=self.tool_registry.get_all_tools(),
                plan=state.plan,
                memories=memories
            )
            
            system_message = ChatMessage(role="system", content=system_content)

            try:
                start_time = time.time()
                response = self.llm.invoke(
                    [system_message] + state.messages
                )
                duration = time.time() - start_time
                
                # 7.2 Extract Token Usage & Calculate Cost
                input_toks, output_toks, model_name = self._extract_usage(response)
                cost = calculate_cost(model_name, input_toks, output_toks)
                state.add_usage(input_toks, output_toks, cost)
                
                logger.info("llm_response: Received response from LLM", extra={"iteration": state.iteration, "duration": round(duration, 3)})
                logger.info("token_usage: LLM call tokens", extra={
                    "model": model_name,
                    "input_tokens": input_toks,
                    "output_tokens": output_toks,
                    "total_tokens": input_toks + output_toks,
                    "estimated_cost": cost
                })
                if on_event:
                    on_event(
                        "llm_response",
                        f"LLM response (iteration {state.iteration})",
                        {
                            "iteration": state.iteration,
                            "duration": round(duration, 3),
                            "input_tokens": input_toks,
                            "output_tokens": output_toks,
                            "model": model_name,
                        },
                    )
                
            except Exception as exc:
                state.status = IterationStatus.FAILED
                logger.error(
                    "llm_error: LLM call raised exception",
                    exc_info=True,
                    extra={"iteration": state.iteration, "error": str(exc)},
                )
                state.observations.append(
                    Observation(
                        tool_call_id="llm_error",
                        content=str(exc),
                        is_error=True,
                    )
                )

                return state

            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                final_content = self._extract_content(response)

                state.messages.append(
                    ChatMessage(
                        role="assistant",
                        content=final_content,
                    )
                )

                state.status = IterationStatus.COMPLETED
                agent_duration = time.time() - agent_start_time
                logger.info("agent_completed: Final answer generated", extra={"iteration": state.iteration, "result_size": len(final_content), "duration": round(agent_duration, 3)})
                if on_event:
                    on_event(
                        "agent_completed",
                        "Final diagnosis generated",
                        {
                            "iteration": state.iteration,
                            "duration": round(agent_duration, 3),
                            "is_final": True,
                        },
                    )

                return state

            state.status = IterationStatus.AWAITING_TOOL

            # Record the assistant's tool-call decision in the message history.
            # The adapter needs this to correctly serialize the conversation for Groq
            # (Groq requires the assistant turn to include the tool_calls array).
            state.messages.append(
                ChatMessage(
                    role="assistant",
                    content=None,
                    tool_calls=tool_calls,
                )
            )

            for tool_call in tool_calls:
                state.tool_calls.append(tool_call)
                logger.info("tool_called: Requesting tool", extra={"iteration": state.iteration, "tool_name": tool_call.name, "tool_call_id": tool_call.id})
                if on_event:
                    on_event(
                        "tool_called",
                        f"Tool: {tool_call.name}",
                        {
                            "iteration": state.iteration,
                            "tool_name": tool_call.name,
                            "tool_call_id": tool_call.id,
                            "arguments": tool_call.arguments,
                        },
                    )

                try:
                    tool_start_time = time.time()
                    tool_result = self.tool_registry.execute(
                        tool_call.id,
                        tool_call.name,
                        **tool_call.arguments
                    )
                    tool_duration = time.time() - tool_start_time
                    
                    if tool_result.success:
                        logger.info("tool_completed: Tool execution successful", extra={"iteration": state.iteration, "tool_name": tool_call.name, "tool_call_id": tool_call.id, "duration": round(tool_duration, 3), "result_size": len(str(tool_result.content))})
                        if on_event:
                            on_event(
                                "tool_completed",
                                f"{tool_call.name} completed",
                                {
                                    "iteration": state.iteration,
                                    "tool_name": tool_call.name,
                                    "tool_call_id": tool_call.id,
                                    "duration": round(tool_duration, 3),
                                    "result_size": len(str(tool_result.content)),
                                },
                            )
                    else:
                        logger.error("tool_failed: Tool execution failed", extra={"iteration": state.iteration, "tool_name": tool_call.name, "tool_call_id": tool_call.id, "duration": round(tool_duration, 3), "error": str(tool_result.error)})
                        if on_event:
                            on_event(
                                "tool_failed",
                                f"{tool_call.name} failed",
                                {
                                    "iteration": state.iteration,
                                    "tool_name": tool_call.name,
                                    "tool_call_id": tool_call.id,
                                    "duration": round(tool_duration, 3),
                                    "error": str(tool_result.error),
                                },
                            )

                    observation = Observation(
                        tool_call_id=tool_result.tool_call_id,
                        content=tool_result.content if tool_result.success else str(tool_result.error),
                        is_error=not tool_result.success,
                    )

                except Exception as exc:
                    logger.error("tool_failed: Tool execution raised exception", extra={"iteration": state.iteration, "tool_name": tool_call.name, "tool_call_id": tool_call.id})
                    if on_event:
                        on_event(
                            "tool_failed",
                            f"{tool_call.name} failed",
                            {
                                "iteration": state.iteration,
                                "tool_name": tool_call.name,
                                "tool_call_id": tool_call.id,
                                "error": str(exc),
                            },
                        )
                    observation = Observation(
                        tool_call_id=tool_call.id,
                        content=str(exc),
                        is_error=True,
                    )

                state.observations.append(observation)

                state.messages.append(
                    ChatMessage(
                        role="tool",
                        content=observation.content,
                    )
                )

            state.status = IterationStatus.RUNNING

        # If loop exited without COMPLETED, perform a final synthesis step
        if state.status != IterationStatus.COMPLETED:
            try:
                synth_prompt = ChatMessage(
                    role="user",
                    content=(
                        "We have reached the maximum search iterations. Based on all the code snippets, "
                        "files, and observations retrieved above, synthesize your final diagnosis, "
                        "pinpoint the probable root cause, and provide fix recommendations now."
                    ),
                )
                final_resp = self.llm.invoke([system_message] + state.messages + [synth_prompt])
                synth_content = self._extract_content(final_resp)
                if synth_content and synth_content.strip():
                    state.messages.append(
                        ChatMessage(
                            role="assistant",
                            content=synth_content,
                        )
                    )
                    state.status = IterationStatus.COMPLETED
            except Exception as e:
                logger.warning(f"Synthesis step failed: {e}")

        if state.status != IterationStatus.COMPLETED:
            state.status = IterationStatus.FAILED
            agent_duration = time.time() - agent_start_time
            logger.error("agent_completed: Stopped due to max iterations", extra={"iteration": state.iteration, "duration": round(agent_duration, 3)})

            state.observations.append(
                Observation(
                    tool_call_id="max_iterations",
                    content=(
                        f"Agent stopped after reaching "
                        f"the maximum of {self.max_iterations} iterations."
                    ),
                    is_error=True,
                )
            )

        return state

    def _extract_tool_calls(
        self,
        response: Any,
    ) -> list[ToolCall]:
        """
        Convert the provider-specific response into our
        internal ToolCall representation.
        """

        raw_tool_calls = getattr(
            response,
            "tool_calls",
            None,
        )

        if not raw_tool_calls:
            return []

        tool_calls = []

        for index, raw_call in enumerate(raw_tool_calls):
            tool_calls.append(
                ToolCall(
                    id=getattr(
                        raw_call,
                        "id",
                        f"tool_call_{index}",
                    ),
                    name=raw_call.name,
                    arguments=raw_call.arguments or {},
                )
            )

        return tool_calls

    def _extract_content(
        self,
        response: Any,
    ) -> str:
        """Extract final textual content from the LLM response."""

        content = getattr(
            response,
            "content",
            response,
        )

        return str(content)

    def _extract_usage(self, response: Any) -> tuple[int, int, str]:
        """Extract input tokens, output tokens, and model name."""
        input_tokens = 0
        output_tokens = 0
        model = getattr(response, "model", "unknown")
        
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0)
            output_tokens = getattr(usage, "completion_tokens", 0)
            
        return input_tokens, output_tokens, model