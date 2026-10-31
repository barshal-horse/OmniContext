"""
Hybrid Retrieval Engine: Dense Vector Embeddings + Sparse BM25 + Reciprocal Rank Fusion (RRF)
Follows Cormack et al. RRF standard (k=60) for scale-invariant ranking aggregation.
"""

import math
import json
import os
import re
from typing import List, Dict, Any, Tuple
from collections import Counter

class HybridRetriever:
    def __init__(self, seed_path: str = None):
        self.documents: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_freqs: Dict[str, int] = Counter()
        self.k1 = 1.5
        self.b = 0.75
        self.rrf_k = 60
        
        if seed_path and os.path.exists(seed_path):
            self.load_corpus(seed_path)

    def _tokenize(self, text: str) -> List[str]:
        """Simple, deterministic lowercase regex tokenizer."""
        return re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())

    def load_corpus(self, file_path: str):
        """Loads corpus from JSON seed file and builds BM25 index."""
        with open(file_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        total_length = 0
        self.doc_lengths = []
        self.doc_freqs.clear()

        for doc in self.documents:
            full_text = f"{doc.get('title', '')} {doc.get('content', '')} {' '.join(doc.get('tags', []))}"
            tokens = self._tokenize(full_text)
            doc["_tokens"] = tokens
            doc["_vector"] = self._compute_deterministic_vector(full_text)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_length += length

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] += 1

        N = len(self.documents)
        self.avg_doc_length = total_length / N if N > 0 else 1.0

    def _compute_deterministic_vector(self, text: str, dims: int = 64) -> List[float]:
        """
        Deterministic lightweight vector projection for zero-credential offline mode.
        Simulates dense embeddings via FNV-1a hash bucket distribution.
        """
        vec = [0.0] * dims
        tokens = self._tokenize(text)
        for token in tokens:
            h = 2166136261
            for char in token:
                h = (h ^ ord(char)) * 16777619
            bucket = h % dims
            vec[bucket] += 1.0
        
        # Normalize to unit length (L2 norm)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two unit vectors."""
        return sum(a * b for a, b in zip(v1, v2))

    def _score_bm25(self, query_tokens: List[str]) -> List[Tuple[int, float]]:
        """Scores all documents against query tokens using Okapi BM25."""
        N = len(self.documents)
        scores = []

        for idx, doc in enumerate(self.documents):
            score = 0.0
            doc_len = self.doc_lengths[idx]
            token_counts = Counter(doc["_tokens"])

            for token in query_tokens:
                if token not in self.doc_freqs:
                    continue
                df = self.doc_freqs[token]
                idf = math.log(1.0 + (N - df + 0.5) / (df + 0.5))
                tf = token_counts.get(token, 0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_length))
                score += idf * ((tf * (self.k1 + 1.0)) / denom)

            scores.append((idx, score))

        # Sort descending by score
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _score_dense(self, query_vector: List[float]) -> List[Tuple[int, float]]:
        """Scores all documents against query vector using cosine similarity."""
        scores = []
        for idx, doc in enumerate(self.documents):
            sim = self._cosine_similarity(query_vector, doc["_vector"])
            scores.append((idx, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Executes Hybrid Search: BM25 (sparse) + Cosine (dense) -> Reciprocal Rank Fusion (RRF).
        """
        if not self.documents:
            return []

        query_tokens = self._tokenize(query_text)
        query_vector = self._compute_deterministic_vector(query_text)

        bm25_ranks = self._score_bm25(query_tokens)
        dense_ranks = self._score_dense(query_vector)

        # Compute RRF score: 1 / (60 + rank)
        rrf_scores: Dict[int, float] = Counter()

        for rank, (doc_idx, _) in enumerate(bm25_ranks, start=1):
            rrf_scores[doc_idx] += 1.0 / (self.rrf_k + rank)

        for rank, (doc_idx, _) in enumerate(dense_ranks, start=1):
            rrf_scores[doc_idx] += 1.0 / (self.rrf_k + rank)

        sorted_indices = sorted(rrf_scores.keys(), key=lambda idx: rrf_scores[idx], reverse=True)

        results = []
        for idx in sorted_indices[:top_k]:
            doc = self.documents[idx]
            results.append({
                "id": doc.get("id"),
                "title": doc.get("title"),
                "category": doc.get("category"),
                "content": doc.get("content"),
                "tags": doc.get("tags", []),
                "rrf_score": round(rrf_scores[idx], 5)
            })

        return results
