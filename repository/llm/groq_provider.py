import os

from groq import Groq

from repository.llm.provider import LLMProvider


class GroqProvider(LLMProvider):

    def __init__(
        self,
        model_name: str | None = None,
    ):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not configured"
            )

        self.model_name = (
            model_name
            or os.getenv(
                "GROQ_MODEL",
                "qwen/qwen3.6-27b",
            )
        )

        self.client = Groq(
            api_key=api_key
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        if not prompt.strip():
            return ""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content or ""
