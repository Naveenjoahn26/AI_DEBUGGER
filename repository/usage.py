from scanner import RepositoryScanner

scanner = RepositoryScanner()

info = scanner.scan("D:/Prograamming/RAG/ScholarAI-v2-main")

print(info.model_dump_json(indent=4))