from repository.models.code_chunk import CodeChunk


class CodeChunkFormatter:
    def format(self, chunk: CodeChunk) -> str:
        """
        Serialize a CodeChunk into a rich text string for embedding.

        FIX 8: now includes docstring and decorators so the embedding
        model gets full semantic signal beyond raw code tokens.
        """
        parts = [
            f"File: {chunk.file_path}",
            f"Type: {chunk.chunk_type}",
        ]
        if chunk.name:
            parts.append(f"Name: {chunk.name}")
        if chunk.parent_name:
            parts.append(f"Parent: {chunk.parent_name}")

        parts.append(
            f"Lines: {chunk.start_line}-{chunk.end_line}"
        )

        # Include docstring — high-quality natural-language semantic signal
        if chunk.docstring:
            parts.append(f"Docstring: {chunk.docstring[:400]}")

        # Include decorators — @route, @property, @staticmethod are meaningful
        if chunk.decorators:
            parts.append(f"Decorators: {', '.join(chunk.decorators)}")

        parts.append("")
        parts.append("Code:")
        parts.append(chunk.content)

        return "\n".join(parts)