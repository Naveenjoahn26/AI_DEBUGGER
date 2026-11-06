import sys
from pathlib import Path
# Add project root to sys.path to resolve 'repository' package when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dataclasses import dataclass, field
from repository.language.language import Language
from repository.models.code_document import CodeDocument
from repository.models.symbol import Symbol
from repository.praser.dependecy_graph import DependencyGraph


@dataclass
class RepositoryIndex:
    documents: list[CodeDocument] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    dependency_graph: DependencyGraph = field(
        default_factory=DependencyGraph
    )

    def add_documents(self, documents: list[CodeDocument]) -> None:
        self.documents.extend(documents)

    def add_symbols(self, symbols: list[Symbol]) -> None:
        self.symbols.extend(symbols)

    def find_symbol(self, name: str) -> list[Symbol]:
        return [
            symbol for symbol in self.symbols
            if symbol.name == name
        ]
        
    def get_documents_by_language(self, language: Language) -> list[CodeDocument]:
        return [
            document 
            for document in self.documents
            if document.language == language
        ]
