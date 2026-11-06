import sys
import ast
from pathlib import Path

# Add project root to sys.path to resolve 'repository' package when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from repository.models.symbol import Symbol, SymbolType
from repository.praser.module_resolver import ModuleResolver
from repository.praser.dependecy_graph import DependencyGraph

class SymbolExtractor(ast.NodeVisitor):

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.symbols: list[Symbol] = []
        self.current_class: str | None = None

    def extract(self, tree: ast.AST) -> list[Symbol]:
        self.symbols = []
        self.current_class = None

        self.visit(tree)

        return self.symbols

    def visit_ClassDef(self, node: ast.ClassDef):

        self.symbols.append(
            Symbol(
                name=node.name,
                symbol_type=SymbolType.CLASS,
                file_path=self.file_path,
                line=node.lineno,
                end_line=node.end_lineno,
            )
        )

        previous_class = self.current_class
        self.current_class = node.name

        self.generic_visit(node)

        self.current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef):

        symbol_type = (
            SymbolType.METHOD
            if self.current_class
            else SymbolType.FUNCTION
        )

        self.symbols.append(
            Symbol(
                name=node.name,
                symbol_type=symbol_type,
                file_path=self.file_path,
                line=node.lineno,
                end_line=node.end_lineno,
                parent=self.current_class,
            )
        )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):

        for alias in node.names:

            self.symbols.append(
                Symbol(
                    name=alias.name,
                    symbol_type=SymbolType.IMPORT,
                    file_path=self.file_path,
                    line=node.lineno,
                    end_line=node.end_lineno,
                )
            )

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):

        module = node.module or ""

        for alias in node.names:

            self.symbols.append(
                Symbol(
                    name=alias.name,
                    symbol_type=SymbolType.IMPORT,
                    file_path=self.file_path,
                    line=node.lineno,
                    end_line=node.end_lineno,
                    module=module,
                )
            )

        self.generic_visit(node)


if __name__ == "__main__":
    from repository.praser.ast_parser import ASTParser

    test_code = """import os
from database import Session

class UserService:

    def create_user(self, name):
        return name

    def delete_user(self, user_id):
        pass

def health_check():
    return {"status": "ok"}
"""

    tree = ast.parse(test_code)
    extractor = SymbolExtractor("test_file.py")
    symbols = extractor.extract(tree)

    for symbol in symbols:
        print(symbol)
