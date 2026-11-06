import json
from typing import Optional

from repository.ai.context_builder import RepositoryContextBuilder
from repository.llm.provider import LLMProvider
from repository.models.code_chunk import CodeChunk
from repository.debugging.models import DebugEvidence, DebugResult
from repository.debugging.schemas import DebugResponseSchema


class CodeDebuggingEngine:

    def __init__(
        self,
        retriever,
        context_builder: RepositoryContextBuilder,
        llm: LLMProvider,
    ):
        self.retriever = retriever
        self.context_builder = context_builder
        self.llm = llm

    def debug(self, problem: str, top_k: int = 5) -> DebugResult:
        if not problem.strip():
            return DebugResult(
                root_cause="Empty input",
                explanation="No problem description provided.",
                suggested_fix="Provide a valid problem description.",
            )

        chunks = self.retriever.search(problem, top_k=top_k)
        context_items = self.context_builder.build(chunks)
        context = self.context_builder.format(context_items)
        prompt = self._build_prompt(problem, context)

        response = self.llm.generate(prompt)

        return self._parse_response(response, chunks)

    def _find_matching_chunk(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        chunks: list[CodeChunk],
    ) -> Optional[CodeChunk]:
        """Find a retrieved chunk that matches the LLM-cited file/line range."""
        for chunk in chunks:
            if chunk.file_path != file_path:
                continue
            # Accept if ranges overlap meaningfully
            if chunk.start_line <= end_line and chunk.end_line >= start_line:
                return chunk
        return None

    def _parse_response(
        self,
        response: str,
        chunks: list[CodeChunk],
    ) -> DebugResult:
        # Strip markdown code fences LLMs often add
        clean = response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]

        data = json.loads(clean)
        validated = DebugResponseSchema.model_validate(data)

        evidence: list[DebugEvidence] = []

        for item in validated.evidence:
            matched_chunk = self._find_matching_chunk(
                file_path=item.file_path,
                start_line=item.start_line,
                end_line=item.end_line,
                chunks=chunks,
            )

            if matched_chunk is None:
                # LLM hallucinated a file/range not in retrieved chunks — skip
                continue

            evidence.append(
                DebugEvidence(
                    file_path=matched_chunk.file_path,
                    start_line=matched_chunk.start_line,
                    end_line=matched_chunk.end_line,
                    content=matched_chunk.content,
                    explanation=item.explanation,
                )
            )

        return DebugResult(
            root_cause=validated.root_cause,
            explanation=validated.explanation,
            suggested_fix=validated.suggested_fix,
            evidence=evidence,
            confidence=validated.confidence,
        )

    def _build_prompt(self, problem: str, context: str) -> str:
        return f"""
You are an AI software engineer debugging a code repository.

Analyze the user's problem using the provided repository context.

Rules:
- Do not invent files.
- Do not invent functions.
- Do not invent line numbers.
- Use repository context as the source of truth.
- If evidence is insufficient, say so.

Repository Context:
{context}

User Problem:
{problem}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "root_cause": "string",
    "explanation": "string",
    "evidence": [
        {{
            "file_path": "string",
            "start_line": 0,
            "end_line": 0,
            "explanation": "string"
        }}
    ],
    "suggested_fix": "string",
    "confidence": "low | medium | high"
}}
""".strip()
