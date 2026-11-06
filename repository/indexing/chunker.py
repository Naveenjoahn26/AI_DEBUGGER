import ast
from pathlib import Path

from repository.models.code_chunk import CodeChunk
from repository.models.code_document import CodeDocument


class CodeChunker:
    """Create semantically meaningful chunks from source code."""

    def chunk(self, document: CodeDocument) -> list[CodeChunk]:
        if document.language.value != "python":
            return []

        try:
            tree = ast.parse(
                document.content,
                filename=str(document.path),
            )
        except SyntaxError:
            return []

        imports = self._get_imports(tree)

        chunks = self._extract_chunks(
            document=document,
            nodes=tree.body,
            parent_name=None,
            imports=imports,
        )

        # FIX 3: also emit module-level assignment chunks so global
        # constants and top-level variables are reachable by the retriever
        chunks.extend(
            self._extract_module_assignments(
                document=document,
                nodes=tree.body,
                imports=imports,
            )
        )

        return chunks

    def _extract_chunks(
        self,
        document: CodeDocument,
        nodes: list[ast.stmt],
        parent_name: str | None,
        imports: list[str],
    ) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []

        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunks.append(
                    self._create_function_chunk(
                        document=document,
                        node=node,
                        parent_name=parent_name,
                        imports=imports,
                    )
                )

            elif isinstance(node, ast.ClassDef):
                chunks.append(
                    self._create_class_chunk(
                        document=document,
                        node=node,
                        parent_name=parent_name,
                        imports=imports,
                    )
                )

                chunks.extend(
                    self._extract_chunks(
                        document=document,
                        nodes=node.body,
                        parent_name=node.name,
                        imports=imports,
                    )
                )

        return chunks

    def _extract_module_assignments(
        self,
        document: CodeDocument,
        nodes: list[ast.stmt],
        imports: list[str],
    ) -> list[CodeChunk]:
        """
        FIX 3: emit one chunk per top-level assignment/constant so that
        module-level bugs (e.g., wrong TAX_RATE) are visible to the retriever.
        """
        chunks: list[CodeChunk] = []

        for node in nodes:
            if not isinstance(
                node, (ast.Assign, ast.AnnAssign, ast.AugAssign)
            ):
                continue

            # Derive a readable name from the assignment target
            name: str | None = None
            if isinstance(node, ast.Assign):
                if node.targets and isinstance(node.targets[0], ast.Name):
                    name = node.targets[0].id
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    name = node.target.id
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    name = node.target.id

            chunks.append(
                CodeChunk(
                    content=self._get_source(document.content, node),
                    file_path=str(document.path),
                    chunk_type="module_variable",
                    name=name,
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                    parent_name=None,
                    language=document.language.value,
                    imports=imports,
                )
            )

        return chunks

    def _create_class_chunk(
        self,
        document: CodeDocument,
        node: ast.ClassDef,
        parent_name: str | None,
        imports: list[str],
    ) -> CodeChunk:
        return CodeChunk(
            content=self._get_source(document.content, node),
            file_path=str(document.path),
            chunk_type="class",
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno,
            parent_name=parent_name,
            language=document.language.value,
            decorators=self._get_decorators(node),
            docstring=self._get_docstring(node),
            imports=imports,
        )

    def _create_function_chunk(
        self,
        document: CodeDocument,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_name: str | None,
        imports: list[str],
    ) -> CodeChunk:
        return CodeChunk(
            content=self._get_source(document.content, node),
            file_path=str(document.path),
            chunk_type="method" if parent_name else "function",
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno,
            parent_name=parent_name,
            language=document.language.value,
            decorators=self._get_decorators(node),
            docstring=self._get_docstring(node),
            imports=imports,
        )

    def _get_source(
        self,
        content: str,
        node: ast.AST,
    ) -> str:
        lines = content.splitlines()

        return "\n".join(
            lines[node.lineno - 1 : node.end_lineno]
        )
    def _get_decorators(self, node: ast.AST) -> list[str]:
        decorators = getattr(node, "decorator_list", [])
        return [
            ast.unparse(decorator)
            for decorator in decorators
        ]

    def _get_docstring(self, node: ast.AST) -> str | None:
        return ast.get_docstring(node)

    def _get_imports(self, tree: ast.Module) -> list[str]:
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))
        return imports