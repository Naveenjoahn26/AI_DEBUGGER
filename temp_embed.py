from repository.embeddings.embedder import CodeEmbedder

def test_embed_code():
    embedder = CodeEmbedder()

    embeddings = embedder.embed(
        [
            "def calculate_total(items):",
            "class UserService:",
        ]
    )
    print(type(embeddings))
    print(len(embeddings))
    print(type(embeddings[0]))

if __name__ == "__main__":
    test_embed_code()
