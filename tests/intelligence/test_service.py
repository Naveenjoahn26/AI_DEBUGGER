from pathlib import Path

from repository.intelligence.service import RepositoryIntelligenceService


class FakeIndexer:
    def __init__(self):
        self.indexed_files = None

    def index(self, file_paths):
        self.indexed_files = file_paths
        return ["fake_chunk"]


class FakeQuestionEngine:
    def __init__(self):
        self.asked_question = None
        self.top_k = None
        
    def ask(self, question, top_k=5):
        self.asked_question = question
        self.top_k = top_k
        return "fake_answer"


def test_service_index_repository():
    indexer = FakeIndexer()
    engine = FakeQuestionEngine()
    
    service = RepositoryIntelligenceService(
        indexer=indexer,
        question_engine=engine,
    )
    
    files = [Path("test.py")]
    
    result = service.index_repository(files)
    
    assert result == ["fake_chunk"]
    assert indexer.indexed_files == files


def test_service_ask():
    indexer = FakeIndexer()
    engine = FakeQuestionEngine()
    
    service = RepositoryIntelligenceService(
        indexer=indexer,
        question_engine=engine,
    )
    
    result = service.ask(
        question="Where is authentication?",
        top_k=10,
    )
    
    assert result == "fake_answer"
    assert engine.asked_question == "Where is authentication?"
    assert engine.top_k == 10
