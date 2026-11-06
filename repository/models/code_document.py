import sys
from pathlib import Path
from dataclasses import dataclass

# Add project root to sys.path to resolve 'repository' package when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from repository.language.language import Language

@dataclass
class CodeDocument:
    path: Path
    content: str
    encoding: str
    size: int
    file_hash: str
    language: Language


