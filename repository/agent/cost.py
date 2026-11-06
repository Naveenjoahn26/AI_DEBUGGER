from typing import Dict, Tuple

# Simple model pricing dictionary
# Key: model name, Value: (cost_per_1k_input, cost_per_1k_output)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    # Groq Models
    "llama-3.3-70b-versatile": (0.00059, 0.00079),
    "llama-3.1-8b-instant": (0.00005, 0.00008),
    "gpt-oss-120b": (0.00015, 0.00060),
    "gpt-oss-20b": (0.000075, 0.00030),
    "openai/gpt-oss-120b": (0.00015, 0.00060),
    "openai/gpt-oss-20b": (0.000075, 0.00030),
    "qwen/qwen3.8-27b": (0.00020, 0.00060),
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculates the estimated cost for a given model and token usage."""
    # Default to 0 cost if model is not recognized
    pricing = MODEL_PRICING.get(model, (0.0, 0.0))
    input_cost = (input_tokens / 1000.0) * pricing[0]
    output_cost = (output_tokens / 1000.0) * pricing[1]
    return input_cost + output_cost
