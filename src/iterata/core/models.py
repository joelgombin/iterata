from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class CorrectionType(str, Enum):
    FORMAT_ERROR = "format_error"
    BUSINESS_RULE = "business_rule"
    MODEL_LIMITATION = "model_limitation"
    CONTEXT_MISSING = "context_missing"
    OCR_ERROR = "ocr_error"
    OTHER = "other"


class ExplanationType(str, Enum):
    HUMAN_PROVIDED = "human_provided"
    LLM_INFERRED = "llm_inferred"
    VALIDATED = "validated"


class Correction(BaseModel):
    """Représente une correction unique"""

    correction_id: str = Field(default_factory=generate_uuid)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    document_id: str
    field_path: str
    original_value: Any
    corrected_value: Any
    confidence_before: Optional[float] = None
    corrector_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class Explanation(BaseModel):
    """Représente l'explication d'une correction"""

    explanation_id: str = Field(default_factory=generate_uuid)
    correction_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    explanation_type: ExplanationType
    category: CorrectionType
    subcategory: Optional[str] = None
    description: str
    confidence: Optional[float] = None
    explainer_id: str
    tags: List[str] = Field(default_factory=list)


class Pattern(BaseModel):
    """Représente un pattern identifié"""

    pattern_id: str
    category: CorrectionType
    description: str
    frequency: int
    first_seen: datetime
    last_seen: datetime
    correction_ids: List[str]
    impact: str  # "low", "medium", "high"
    automation_potential: float  # 0-1


class IterataConfig(BaseModel):
    """Configuration de CorrectionLoop"""

    base_path: str
    skill_path: Optional[str] = None
    auto_explain: bool = False
    backend: Optional[str] = None
    min_corrections_for_skill: int = 10
    explanation_confidence_threshold: float = 0.8
