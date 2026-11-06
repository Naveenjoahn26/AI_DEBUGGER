from pathlib import Path


class ModuleResolver:

    def __init__(self, repository_root: Path):
        self.repository_root = repository_root

    def resolve(self, module_name: str) -> Path | None:
        module_path = Path(*module_name.split("."))

        candidates = [
            self.repository_root / f"{module_path}.py",
            self.repository_root / module_path / "__init__.py",
        ]

        for candidate in candidates:
            if candidate.is_file():
                return candidate

        return None