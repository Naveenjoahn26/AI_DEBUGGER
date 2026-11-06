import sys
from pathlib import Path

# Add project root to sys.path to resolve 'repository' package when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from repository.language.constants import EXTENSION_LANGUAGE_MAP
from repository.language.language import Language

class LanguageDetector:
    def detect(self, path: Path) -> Language:
        return EXTENSION_LANGUAGE_MAP.get(path.suffix.lower(), Language.UNKNOWN)

    
