from dataclasses import dataclass, field


@dataclass
class DebugEvidence:
    file_path: str
    start_line: int
    end_line: int
    content: str
    explanation: str = ""


@dataclass
class DebugResult:
    root_cause: str
    explanation: str
    suggested_fix: str
    evidence: list[DebugEvidence] = field(
        default_factory=list
    )
    confidence: str = "unknown"
