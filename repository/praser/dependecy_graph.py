import sys
from collections import defaultdict
from pathlib import Path

# Add project root to sys.path to resolve 'repository' package when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from repository.models.symbol import Symbol, SymbolType
from repository.praser.module_resolver import ModuleResolver


class DependencyGraph:

    def __init__(self):
        self.graph: dict[str, set[str]] = defaultdict(set)

    def add_dependency(
        self,
        source_file: str,
        target_file: str,
    ) -> None:
        self.graph[source_file].add(target_file)

    def get_dependencies(
        self,
        source_file: str,
    ) -> set[str]:
        return self.graph.get(source_file, set())

    def get_dependents(
        self,
        target_file: str,
    ) -> set[str]:

        dependents = set()

        for source, targets in self.graph.items():
            if target_file in targets:
                dependents.add(source)

        return dependents

    def add_import(
        self,
        source_file: Path,
        symbols: list[Symbol],
        resolver: ModuleResolver,
    ) -> None:
        for symbol in symbols:
            if symbol.symbol_type != SymbolType.IMPORT:
                continue
            
            target = None
            if symbol.module:
                # E.g. `from a.b import c` might resolve to `a/b/c.py` or `a/b.py`
                target = resolver.resolve(f"{symbol.module}.{symbol.name}")
                if target is None:
                    target = resolver.resolve(symbol.module)
            else:
                target = resolver.resolve(symbol.name)

            if target is None:
                continue
            self.add_dependency(str(source_file), str(target))

    def has_cycle(self) -> bool:

        visited = set()
        visiting = set()

        def dfs(node: str) -> bool:

            if node in visiting:
                return True

            if node in visited:
                return False

            visiting.add(node)

            for dependency in self.graph.get(node, set()):
                if dfs(dependency):
                    return True

            visiting.remove(node)
            visited.add(node)
            
            return False

        for node in self.graph:
            if dfs(node):
                return True

        return False
if __name__ == "__main__":
    graph = DependencyGraph()

    graph.add_dependency("main.py", "api.py")
    graph.add_dependency("api.py", "service.py")
    graph.add_dependency("service.py", "database.py")


    print(graph.get_dependencies("main.py"))

    print(graph.get_dependents("service.py"))



    print(graph.has_cycle())
    graph.add_dependency("database.py", "main.py")
    print(graph.has_cycle())