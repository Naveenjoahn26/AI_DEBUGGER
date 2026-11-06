from dataclasses import dataclass
from enum import Enum


class SymbolType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"


@dataclass
class Symbol:
    name: str
    symbol_type: SymbolType
    file_path: str
    line: int
    end_line: int | None = None
    parent: str | None = None
    module: str | None = None
