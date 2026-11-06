import sys
import ast
from pathlib import Path

# Add project root to sys.path to resolve 'repository' package when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from repository.models.code_document import CodeDocument
from repository.language.language import Language

class ASTParser:
    def parse(self,document:CodeDocument) -> ast.AST:
        if document.language != Language.PYTHON:
            raise ValueError(f"AST parsing is not support for {document.language} files")

        try:
            return ast.parse(
                document.content,
                filename=str(document.path),
            )
        except SyntaxError as exc:
            raise ValueError(
                f"Failed to parse Python file: {document.path}"
            ) from exc
if __name__ == "__main__":
    from repository.language.detector import LanguageDetector
    from repository.reader.reader import CodeReader

    detector = LanguageDetector()
    reader = CodeReader(detector)
    parser = ASTParser()

    document = reader.read(Path("main.py"))

    tree = parser.parse(document)

    print(ast.dump(tree, indent=2))