"""
Continuous Evaluation Engine for OmniContext.
Computes deterministic Context Relevancy, Faithfulness (Hallucination Detection),
and Schema Adherence without relying on flaky, expensive external LLM judges in CI/CD.
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

TupleMetric = Tuple[float, Dict[str, Any]]

# [FDE-WHY]: Stopwords set filters common grammatical particles and conversational query
# filler words so they do not skew the lexical and semantic overlap calculations.
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "were", "weren't", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "won't", "would", "you", "your", "yours",
    "yourself", "yourselves", "happens", "handled", "returned"
}

def stem(word: str) -> str:
    """
    Lightweight deterministic suffix stemmer.
    Normalizes plurals and inflections ('limiting'/'limiter' -> 'limit', 'tokens' -> 'token').
    Preserves specialized technical words ending in 'is', 'us', 'ss' (e.g. 'redis', 'status').
    """
    w = word.lower()
    if w.endswith(('ss', 'is', 'us')):
        return w
    for suff in ['ation', 'ition', 'ment', 'ence', 'ance', 'ness', 'ing', 'ed', 'es', 'er', 'or', 's']:
        if w.endswith(suff) and len(w) - len(suff) >= 3:
            return w[:-len(suff)]
    return w

class EvalResult(BaseModel):
    """Evaluation result for a single query-context-response triplet."""
    query: str
    context_relevancy: float = Field(ge=0.0, le=1.0, description="Relevancy of context chunks to user query")
    faithfulness: float = Field(ge=0.0, le=1.0, description="Factual grounding of answer against context")
    schema_adherence: float = Field(ge=0.0, le=1.0, description="Compliance with Pydantic v2 data contract")
    overall_score: float = Field(ge=0.0, le=1.0, description="Harmonic mean of composite metrics")
    passed: bool = Field(description="Whether sample meets minimum enterprise threshold")
    latency_ms: float = Field(description="Evaluation calculation latency in ms")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic breakdown")

class BenchmarkReport(BaseModel):
    """Aggregated evaluation benchmark report across a test suite."""
    total_samples: int
    passed_samples: int
    pass_rate: float
    avg_context_relevancy: float
    avg_faithfulness: float
    avg_schema_adherence: float
    avg_overall_score: float
    avg_latency_ms: float
    results: List[EvalResult] = Field(default_factory=list)

class ContinuousEvalHarness:
    """
    Deterministic enterprise evaluation engine measuring Context Relevancy,
    Faithfulness, and Schema Adherence.
    """
    def __init__(
        self,
        relevancy_threshold: float = 0.45,
        faithfulness_threshold: float = 0.70,
        schema_threshold: float = 1.0
    ):
        self.relevancy_threshold = relevancy_threshold
        self.faithfulness_threshold = faithfulness_threshold
        self.schema_threshold = schema_threshold

    def _extract_keywords(self, text: str, apply_stem: bool = True) -> List[str]:
        """Extracts content-bearing lowercase alphanumeric tokens, filtering stopwords."""
        raw_tokens = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())
        filtered = [t for t in raw_tokens if t not in STOPWORDS and len(t) > 1]
        if apply_stem:
            return [stem(t) for t in filtered]
        return filtered

    def _extract_claims(self, text: str) -> List[str]:
        """
        Splits generated answer into discrete factual claims by sentence boundaries.
        """
        # [FDE-WHY]: Splitting by sentence boundaries and semi-colons provides atomic,
        # verifiable statements for claim-level grounding verification.
        sentences = re.split(r'[.!?;\n]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]

    def compute_context_relevancy(self, query: str, context_chunks: List[str]) -> TupleMetric:
        """
        Computes Context Relevancy: ratio of stemmed query keywords captured in retrieved context.
        Score = |Stemmed_Query_Keywords ∩ Stemmed_Context_Keywords| / |Stemmed_Query_Keywords|
        """
        query_words = set(self._extract_keywords(query, apply_stem=True))
        if not query_words:
            return 1.0, {"query_keywords": [], "found": []}

        all_context_text = " ".join(context_chunks).lower()
        context_words = set(self._extract_keywords(all_context_text, apply_stem=True))

        found = query_words.intersection(context_words)
        score = len(found) / len(query_words)
        
        # [FDE-WHY]: Boundary clamp ensures numerical stability even with extreme inputs.
        score = max(0.0, min(1.0, score))
        return score, {
            "query_keywords_count": len(query_words),
            "matched_keywords_count": len(found),
            "matched_keywords": sorted(list(found))
        }

    def compute_faithfulness(self, answer: str, context_chunks: List[str]) -> TupleMetric:
        """
        Computes Faithfulness: verifies that all assertions made in the answer are
        grounded in the retrieved context documents.
        """
        claims = self._extract_claims(answer)
        if not claims:
            return 1.0, {"claims_count": 0, "grounded_count": 0}

        all_context_text = " ".join(context_chunks).lower()
        context_tokens = set(self._extract_keywords(all_context_text, apply_stem=True))

        grounded_claims = []
        ungrounded_claims = []

        for claim in claims:
            claim_tokens = self._extract_keywords(claim, apply_stem=True)
            if not claim_tokens:
                grounded_claims.append(claim)
                continue

            # Check overlap between claim tokens and context tokens
            matched = [t for t in claim_tokens if t in context_tokens]
            overlap_ratio = len(matched) / len(claim_tokens)

            # [FDE-WHY]: Threshold of 0.50 requires at least half of the assertion's content words
            # to be attested in the retrieved context chunks to be deemed grounded.
            if overlap_ratio >= 0.50:
                grounded_claims.append(claim)
            else:
                ungrounded_claims.append(claim)

        score = len(grounded_claims) / len(claims) if claims else 1.0
        score = max(0.0, min(1.0, score))

        return score, {
            "total_claims": len(claims),
            "grounded_claims_count": len(grounded_claims),
            "ungrounded_claims": ungrounded_claims
        }

    def compute_schema_adherence(self, response_payload: Dict[str, Any]) -> TupleMetric:
        """
        Evaluates whether the payload satisfies enterprise Pydantic contracts.
        """
        from backend.app.guardrails import EnterpriseQueryResponse
        try:
            EnterpriseQueryResponse.model_validate(response_payload)
            return 1.0, {"status": "valid", "errors": None}
        except Exception as e:
            return 0.0, {"status": "invalid", "errors": str(e)}

    def evaluate_sample(
        self,
        query: str,
        context_chunks: List[str],
        answer: str,
        response_payload: Optional[Dict[str, Any]] = None
    ) -> EvalResult:
        """Evaluates a single sample with complete diagnostic breakdown."""
        start = time.perf_counter()

        rel_score, rel_meta = self.compute_context_relevancy(query, context_chunks)
        faith_score, faith_meta = self.compute_faithfulness(answer, context_chunks)

        payload = response_payload or {
            "query": query,
            "answer": answer,
            "confidence_score": 0.90,
            "cited_doc_ids": []
        }
        schema_score, schema_meta = self.compute_schema_adherence(payload)

        # [FDE-WHY]: Weighted composite score gives 40% weight to faithfulness (safety),
        # 30% to relevancy (accuracy), and 30% to schema adherence (interoperability).
        overall = (rel_score * 0.3) + (faith_score * 0.4) + (schema_score * 0.3)

        passed = (
            rel_score >= self.relevancy_threshold and
            faith_score >= self.faithfulness_threshold and
            schema_score >= self.schema_threshold
        )

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return EvalResult(
            query=query,
            context_relevancy=round(rel_score, 4),
            faithfulness=round(faith_score, 4),
            schema_adherence=round(schema_score, 4),
            overall_score=round(overall, 4),
            passed=passed,
            latency_ms=round(elapsed_ms, 2),
            details={
                "relevancy": rel_meta,
                "faithfulness": faith_meta,
                "schema": schema_meta
            }
        )

    def evaluate_benchmark(self, dataset: List[Dict[str, Any]]) -> BenchmarkReport:
        """Runs evaluation over a benchmark golden dataset and aggregates results."""
        results = []
        for item in dataset:
            res = self.evaluate_sample(
                query=item["query"],
                context_chunks=item.get("context_chunks", []),
                answer=item.get("answer", ""),
                response_payload=item.get("payload")
            )
            results.append(res)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        pass_rate = (passed / total) * 100.0 if total > 0 else 0.0

        avg_rel = sum(r.context_relevancy for r in results) / total if total > 0 else 0.0
        avg_faith = sum(r.faithfulness for r in results) / total if total > 0 else 0.0
        avg_schema = sum(r.schema_adherence for r in results) / total if total > 0 else 0.0
        avg_overall = sum(r.overall_score for r in results) / total if total > 0 else 0.0
        avg_lat = sum(r.latency_ms for r in results) / total if total > 0 else 0.0

        return BenchmarkReport(
            total_samples=total,
            passed_samples=passed,
            pass_rate=round(pass_rate, 2),
            avg_context_relevancy=round(avg_rel, 4),
            avg_faithfulness=round(avg_faith, 4),
            avg_schema_adherence=round(avg_schema, 4),
            avg_overall_score=round(avg_overall, 4),
            avg_latency_ms=round(avg_lat, 2),
            results=results
        )
