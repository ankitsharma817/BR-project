"""
Wraps BAAI/bge-small-en-v1.5 for batch embedding and cosine similarity.
Models are loaded lazily once and kept in memory on GPU.
"""
import json
import hashlib
from typing import Optional
import numpy as np

_embedding_model = None
_reranker_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        from ..config import settings
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL, cache_folder=settings.MODEL_CACHE_DIR)
        try:
            import torch
            if torch.cuda.is_available():
                _embedding_model = _embedding_model.cuda()
        except ImportError:
            pass
    return _embedding_model


def _get_reranker_model():
    global _reranker_model
    if _reranker_model is None:
        from sentence_transformers import CrossEncoder
        from ..config import settings
        _reranker_model = CrossEncoder(settings.RERANKER_MODEL, max_length=512)
    return _reranker_model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    model = _get_embedding_model()
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


def rerank(query: str, candidates: list[str]) -> list[float]:
    """Returns cross-encoder scores for each (query, candidate) pair."""
    reranker = _get_reranker_model()
    pairs = [(query, c) for c in candidates]
    scores = reranker.predict(pairs, show_progress_bar=False)
    # Normalize to 0-1 range using sigmoid
    import torch
    scores_tensor = torch.tensor(scores)
    normalized = torch.sigmoid(scores_tensor).numpy()
    return normalized.tolist()


def batch_cosine_similarities(query_emb: list[float], candidate_embs: list[list[float]]) -> list[float]:
    q = np.array(query_emb, dtype=np.float32)
    C = np.array(candidate_embs, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm == 0:
        return [0.0] * len(candidate_embs)
    q = q / q_norm
    norms = np.linalg.norm(C, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    C_norm = C / norms
    return (C_norm @ q).tolist()
