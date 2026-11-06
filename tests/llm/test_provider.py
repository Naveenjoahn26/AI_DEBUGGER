from repository.llm.provider import LLMProvider


class FakeLLM(LLMProvider):

    def generate(
        self,
        prompt: str,
    ) -> str:

        return f"Generated: {prompt}"


def test_llm_provider_contract():

    llm = FakeLLM()

    result = llm.generate(
        "Explain authentication."
    )

    assert result == (
        "Generated: Explain authentication."
    )
