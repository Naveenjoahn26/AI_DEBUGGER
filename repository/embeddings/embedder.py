import hashlib
import logging
import math
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class CodeEmbedder:

    def __init__(
        self,
        model_name: str | None = None,
    ):
        self.token = os.getenv("HF_TOKEN")
        self.model_name = (
            model_name
            or os.getenv(
                "HF_EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2",
            )
        )

        if self.token:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(
                provider="hf-inference",
                api_key=self.token,
            )
        else:
            logger.warning(
                "HF_TOKEN environment variable is not configured. "
                "Local fallback embeddings enabled for offline/development mode."
            )
            self.client = None

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        if self.client:
            try:
                embeddings = self.client.feature_extraction(
                    texts,
                    model=self.model_name,
                    normalize=True,
                )
                if hasattr(embeddings, "tolist"):
                    return embeddings.tolist()
                return embeddings
            except Exception as e:
                logger.warning(
                    f"HuggingFace inference failed ({e}), falling back to local deterministic embeddings."
                )

        # Deterministic 384-dimensional normalized pseudo-embeddings fallback
        results = []
        for text in texts:
            vec = []
            for i in range(384):
                h = hashlib.sha256(f"{text}_{i}".encode("utf-8")).digest()
                val = int.from_bytes(h[:4], "big", signed=True) / (2**31)
                vec.append(val)
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            results.append([x / norm for x in vec])
        return results
