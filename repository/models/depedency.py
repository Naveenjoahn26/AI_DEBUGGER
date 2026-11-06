from dataclasses import dataclass


@dataclass
class Dependency:
    source_file: str
    target_module: str
    import_name: str