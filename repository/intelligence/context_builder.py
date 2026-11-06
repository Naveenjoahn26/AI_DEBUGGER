from dataclasses import dataclass

from repository.models.code_chunk import CodeChunk


@dataclass(frozen=True)
class ContextItem:
    file_path: str
    chunk_type: str
    name: str | None
    start_line: int
    end_line: int
    content: str


class RepositoryContextBuilder:

    def build(
        self,
        chunks: list[CodeChunk],
    ) -> list[ContextItem]:

        if not chunks:
            return []

        return [
            ContextItem(
                file_path=chunk.file_path,
                chunk_type=chunk.chunk_type,
                name=chunk.name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
            )
            for chunk in chunks
        ]