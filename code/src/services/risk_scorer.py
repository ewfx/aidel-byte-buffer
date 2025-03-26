from typing import Dict, List, Optional
from models.entity import Entity, EntityType, Anomaly

class RiskScorer:
    def __init__(self):
        # Risk weights for different factors
        self.weights = {
            "entity_type": 0.3,
            "sanctions": 0.25,
            "reputation": 0.2,
            "anomalies": 0.15,
            "geographic": 0.1
        }
        
        # Risk scores for different entity types
        self.entity_type_risk = {
            EntityType.SHELL_COMPANY: 0.8,
            EntityType.FINANCIAL_INTERMEDIARY: 0.6,
            EntityType.CORPORATION: 0.4,
            EntityType.NON_PROFIT: 0.3,
            EntityType.GOVERNMENT_AGENCY: 0.2,
            EntityType.UNKNOWN: 0.5
        }
        
        # High-risk jurisdictions
        self.high_risk_jurisdictions = {
            "ru": 0.8,  # Russia
            "cn": 0.7,  # China
            "ir": 0.9,  # Iran
            "kp": 0.9,  # North Korea
            "sy": 0.8,  # Syria
            "ve": 0.7,  # Venezuela
            "mm": 0.7,  # Myanmar
            "zw": 0.6,  # Zimbabwe
        }

    def calculate_risk_score(
        self,
        entity: Entity,
        anomalies: Optional[List[Anomaly]] = None,
        transaction_amount: Optional[float] = None
    ) -> float:
        """
        Calculate overall risk score for an entity
        """
        risk_scores = {}
        
        # Entity type risk
        risk_scores["entity_type"] = self.entity_type_risk.get(entity.type, 0.5)
        
        # Sanctions risk
        risk_scores["sanctions"] = 0.8 if entity.sanctions_status else 0.0
        
        # Reputation risk (inverse of reputation score)
        risk_scores["reputation"] = 1.0 - entity.reputation_score if entity.reputation_score is not None else 0.5
        
        # Anomaly risk
        risk_scores["anomalies"] = self._calculate_anomaly_risk(anomalies, transaction_amount)
        
        # Geographic risk
        risk_scores["geographic"] = self._calculate_geographic_risk(entity.jurisdiction)
        
        # Calculate weighted average
        total_risk = sum(
            risk_scores[factor] * self.weights[factor]
            for factor in self.weights
        )
        
        return min(max(total_risk, 0.0), 1.0)

    def _calculate_anomaly_risk(
        self,
        anomalies: Optional[List[Anomaly]],
        transaction_amount: Optional[float]
    ) -> float:
        """
        Calculate risk score based on anomalies
        """
        if not anomalies:
            return 0.0
        
        # Calculate average anomaly severity
        severity_scores = [anomaly.severity for anomaly in anomalies]
        avg_severity = sum(severity_scores) / len(severity_scores)
        
        # Adjust for transaction amount if available
        if transaction_amount is not None:
            # Higher risk for larger transactions
            amount_factor = min(transaction_amount / 1000000, 1.0)  # Normalize to 0-1
            avg_severity = (avg_severity + amount_factor) / 2
        
        return avg_severity

    def _calculate_geographic_risk(self, jurisdiction: Optional[str]) -> float:
        """
        Calculate risk score based on jurisdiction
        """
        if not jurisdiction:
            return 0.5  # Neutral risk for unknown jurisdictions
        
        # Convert jurisdiction to lowercase for comparison
        jurisdiction = jurisdiction.lower()
        
        # Check if jurisdiction is in high-risk list
        return self.high_risk_jurisdictions.get(jurisdiction, 0.5)

    def generate_risk_reason(
        self,
        entity: Entity,
        risk_score: float,
        anomalies: Optional[List[Anomaly]] = None
    ) -> str:
        """
        Generate human-readable explanation of risk score
        """
        reasons = []
        
        # Entity type reason
        if entity.type == EntityType.SHELL_COMPANY:
            reasons.append("Entity is classified as a shell company")
        elif entity.type == EntityType.FINANCIAL_INTERMEDIARY:
            reasons.append("Entity is a financial intermediary")
        
        # Sanctions reason
        if entity.sanctions_status:
            reasons.append("Entity is on sanctions list")
        
        # Reputation reason
        if entity.reputation_score is not None and entity.reputation_score < 0.3:
            reasons.append("Entity has poor reputation based on news analysis")
        
        # Anomaly reasons
        if anomalies:
            for anomaly in anomalies:
                reasons.append(f"Anomaly detected: {anomaly.description}")
        
        # Geographic reason
        if entity.jurisdiction and entity.jurisdiction.lower() in self.high_risk_jurisdictions:
            reasons.append(f"Entity is based in a high-risk jurisdiction ({entity.jurisdiction})")
        
        # If no specific reasons, provide a general explanation
        if not reasons:
            reasons.append("Risk score based on standard entity assessment")
        
        return " | ".join(reasons) 