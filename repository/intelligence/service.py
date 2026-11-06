from pathlib import Path

from repository.intelligence.indexer import RepositoryIndexer
from repository.intelligence.question_engine import CodeQuestionEngine


class RepositoryIntelligenceService:

    def __init__(
        self,
        indexer: RepositoryIndexer,
        question_engine: CodeQuestionEngine,
    ):
        self.indexer = indexer
        self.question_engine = question_engine

    def index_repository(
        self,
        file_paths: list[Path],
    ):
        return self.indexer.index(file_paths)

    def ask(
        self,
        question: str,
        top_k: int = 5,
    ) -> str:

        return self.question_engine.ask(
            question=question,
            top_k=top_k,
        )
