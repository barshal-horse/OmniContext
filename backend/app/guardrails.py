"""
Deterministic Guardrails Engine & Self-Healing Contract Validator.
Enforces Pydantic v2 schema adherence with automated reflection repair loops.
"""

from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional, List, Type
import json

class EnterpriseQueryResponse(BaseModel):
    """Guaranteed structured output contract for enterprise agent responses."""
    query: str = Field(description="The original user query")
    answer: str = Field(description="Direct, factual answer grounded in context")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    cited_doc_ids: List[str] = Field(default_factory=list, description="IDs of cited enterprise documents")
    requires_human_approval: bool = Field(default=False, description="Flag if action needs manual approval")

class GuardrailEngine:
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def validate_or_repair(
        self,
        raw_payload: Any,
        target_model: Type[BaseModel] = EnterpriseQueryResponse,
        repair_fn: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Validates raw payload against target Pydantic model.
        If validation fails, triggers self-healing reflection retries before failing closed.
        """
        data = raw_payload
        if isinstance(raw_payload, str):
            try:
                # Strip markdown code blocks if model output wrapped in ```json
                clean_str = raw_payload.strip()
                if clean_str.startswith("```"):
                    clean_str = clean_str.split("\n", 1)[-1].rsplit("\n", 1)[0].strip()
                data = json.loads(clean_str)
            except Exception as e:
                data = {"_parse_error": str(e), "_raw": raw_payload}

        for attempt in range(self.max_retries + 1):
            try:
                validated = target_model.model_validate(data)
                return {
                    "success": True,
                    "data": validated.model_dump(),
                    "attempts": attempt + 1,
                    "repaired": attempt > 0
                }
            except ValidationError as err:
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": str(err),
                        "errors_list": err.errors(),
                        "attempts": attempt + 1
                    }
                
                # Execute automated repair attempt if repair function provided
                if repair_fn:
                    data = repair_fn(data, err)
                else:
                    # Default heuristic auto-repair for common LLM omissions
                    if isinstance(data, dict):
                        if "confidence_score" not in data or data["confidence_score"] is None:
                            data["confidence_score"] = 0.85
                        if "cited_doc_ids" not in data or not isinstance(data["cited_doc_ids"], list):
                            data["cited_doc_ids"] = []
                        if "requires_human_approval" not in data:
                            data["requires_human_approval"] = False
                        if "query" not in data and "question" in data:
                            data["query"] = data.pop("question")
