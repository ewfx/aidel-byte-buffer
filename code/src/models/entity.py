from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum

class EntityType(str, Enum):
    CORPORATION = "Corporation"
    NON_PROFIT = "Non-Profit"
    SHELL_COMPANY = "Shell Company"
    GOVERNMENT_AGENCY = "Government Agency"
    FINANCIAL_INTERMEDIARY = "Financial Intermediary"
    UNKNOWN = "Unknown"

class Entity(BaseModel):
    name: str
    type: EntityType
    confidence_score: float
    evidence_sources: List[str]
    registration_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    incorporation_date: Optional[str] = None
    directors: Optional[List[str]] = None
    shareholders: Optional[List[str]] = None
    sanctions_status: Optional[bool] = False
    risk_factors: Optional[Dict[str, float]] = None
    reputation_score: Optional[float] = 0.0

class Transaction(BaseModel):
    transaction_id: str
    amount: float
    currency: str
    date: str
    description: str
    entities: List[Entity]

class AnalysisResult(BaseModel):
    transaction_id: str
    extracted_entity: List[str]
    entity_type: List[str]
    risk_score: float
    supporting_evidence: List[str]
    confidence_score: float
    reason: str

class Anomaly(BaseModel):
    type: str
    severity: float
    description: str
    evidence: List[str] 