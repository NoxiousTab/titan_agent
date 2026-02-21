from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from models import Ticket


@lru_cache(maxsize=1)
def _get_sentence_transformer():
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer("all-MiniLM-L6-v2")


def _embed_with_sentence_transformers(texts: List[str]) -> np.ndarray:
    model = _get_sentence_transformer()
    emb = model.encode(texts, normalize_embeddings=True)
    return np.asarray(emb, dtype=np.float32)


def _embed_with_gemini(texts: List[str]) -> np.ndarray:
    import google.generativeai as genai  # type: ignore

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    genai.configure(api_key=api_key)

    vectors: List[List[float]] = []
    for t in texts:
        res = genai.embed_content(
            model="models/text-embedding-004",
            content=t,
            task_type="retrieval_document",
        )
        vectors.append(res["embedding"])  # type: ignore[index]

    arr = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    return arr / norms


def embed_texts(texts: List[str]) -> np.ndarray:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            return _embed_with_gemini(texts)
        except Exception:
            return _embed_with_sentence_transformers(texts)
    return _embed_with_sentence_transformers(texts)


def detect_duplicate(
    db: Session,
    title: str,
    description: str,
    threshold: float = 0.85,
) -> Tuple[bool, Optional[int], float]:
    existing: List[Ticket] = db.query(Ticket).order_by(Ticket.created_at.desc()).limit(200).all()
    if not existing:
        return False, None, 0.0

    candidate_text = f"{title}\n{description}".strip()
    corpus_texts = [f"{t.title}\n{t.description}".strip() for t in existing]

    embeddings = embed_texts([candidate_text] + corpus_texts)
    cand_vec = embeddings[:1]
    corpus_vecs = embeddings[1:]

    sims = cosine_similarity(cand_vec, corpus_vecs)[0]
    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])
    best_ticket = existing[best_idx]

    if best_score >= threshold:
        return True, int(best_ticket.id), best_score
    return False, None, best_score
