import subprocess
from pathlib import Path
import logging

from models import RepositoryInfo
from metadata import FileMetadata, MetadataCollector

class RepositoryScanner:

    IGNORED_DIRECTORIES = {
        ".git",
        "__pycache__",
        ".venv",
        "node_modules",
        ".pytest_cache",
        "dist",
        "build",
    }
    EXTENSION_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".cpp": "C++",
        ".html": "HTML"
    }

    def scan(self, repository_path: str | Path) -> RepositoryInfo:

        root = Path(repository_path).resolve()

        self._validate_repository(root)

        git_info = self._collect_git_metadata(root)

        files, extension_breakdown = self._discover_files(root)

        return RepositoryInfo(
            root_path=root,
            is_git_repo=git_info["is_git_repo"],
            current_branch=git_info["current_branch"],
            latest_commit=git_info["latest_commit"],
            has_uncommitted_changes=git_info["has_uncommitted_changes"],
            total_files=len(files),
            extension_breakdown=extension_breakdown,
            files=files,
        )

    def _validate_repository(self, root: Path) -> None:

        if not root.exists():
            raise FileNotFoundError(f"{root} does not exist.")

        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a directory.")

    def _collect_git_metadata(self, root: Path) -> dict:

        git_info = {
            "is_git_repo": False,
            "current_branch": None,
            "latest_commit": None,
            "has_uncommitted_changes": False,
        }

        try:

            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            git_info["is_git_repo"] = True

            git_info["current_branch"] = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=root,
                text=True,
            ).strip()

            git_info["latest_commit"] = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                text=True,
            ).strip()

            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=root,
                text=True,
            )

            git_info["has_uncommitted_changes"] = bool(status.strip())

        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning("Not a git repository")

        return git_info

    def _discover_files(
        self,
        root: Path,
        ) -> tuple[list[FileMetadata], dict[str, int]]:

        files: list[FileMetadata] = []
        extension_breakdown: dict[str, int] = {}

        for path in root.rglob("*"):

            if any(part in self.IGNORED_DIRECTORIES for part in path.parts):
                continue

            if not path.is_file():
                continue
            metadata = MetadataCollector.collect(path,root)
            files.append(metadata)
            extension = metadata.extension
            language = self.EXTENSION_MAP.get(extension, "Unknown")
            extension_breakdown[language] = (
                extension_breakdown.get(language, 0) + 1
            )
        return files, extension_breakdown