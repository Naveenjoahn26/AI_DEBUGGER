from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field
@dataclass
class CodeChunk:
    content: str
    file_path: str
    chunk_type: str
    name: Optional[str]

    start_line: int
    end_line: int

    repository_id: Optional[str] = None
    language: Optional[str] = None
    parent_name: Optional[str] = None
    file_hash: Optional[str] = None

    decorators: list[str] | None = None
    docstring: str | None = None
    imports: list[str] | None = None


    
    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1

    def to_llm_format(self) -> str:
        parts = []
        parts.append(f"file: {self.file_path}")
        if self.language:
            parts.append(f"language: {self.language}")
        parts.append("")
        
        parts.append(f"type: {self.chunk_type}")
        if self.name:
            parts.append(f"name: {self.name}")
        if self.parent_name:
            parts.append(f"parent: {self.parent_name}")
        parts.append("")

        if self.decorators is not None:
            parts.append("decorators:")
            if not self.decorators:
                parts.append("  []")
            else:
                for d in self.decorators:
                    parts.append(f"  @{d}")
            parts.append("")

        if self.docstring is not None:
            parts.append("docstring:")
            doc = self.docstring.strip().replace('\n', '\\n')
            parts.append(f'  "{doc}"')
            parts.append("")

        if self.imports is not None:
            parts.append("imports:")
            if not self.imports:
                parts.append("  []")
            else:
                for i in self.imports:
                    parts.append(f"  {i}")
            parts.append("")

        parts.append("lines:")
        parts.append(f"  {self.start_line}-{self.end_line}")
        parts.append("")
        
        parts.append("content:")
        for line in self.content.splitlines():
            parts.append(f"  {line}" if line else "  ")

        return "\n".join(parts)