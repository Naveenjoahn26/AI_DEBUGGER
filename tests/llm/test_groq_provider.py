import pytest

from repository.llm.groq_provider import GroqProvider


def test_groq_provider_requires_api_key(
    monkeypatch,
):

    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    with pytest.raises(ValueError):
        GroqProvider()
