from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    absolute_path: Path = Field(
        description="Absolute path to the file."
    )
    relative_path: Path = Field(
        description="Path relative to the repository root."
    )
    file_name: str = Field(
        description="Name of the file."
    )
    extension: str = Field(
        description="File extension."
    )
    size_bytes: int = Field(
        description="File size in bytes."
    )
    is_binary: bool
    encoding: str | None
    line_count: int

class RepositoryInfo(BaseModel):
    root_path: Path = Field(
        description="Absolute path to the repository."
    )
    is_git_repo: bool = False
    current_branch: Optional[str] = None
    latest_commit: Optional[str] = None
    has_uncommitted_changes: bool = False
    total_files: int = 0
    extension_breakdown: dict[str, int] = Field(default_factory=dict)
    files:list[FileMetadata] = Field(default_factory=list,description="Metadata for every discovered file")
    
    
