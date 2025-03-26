from typing import List, Optional
from models.entity import Entity, Anomaly
import numpy as np
from datetime import datetime, timedelta

class AnomalyDetector:
    def __init__(self):
        # Thresholds for different types of anomalies
        self.thresholds = {
            "amount": 1000000,  # Large transaction threshold
            "frequency": 5,     # Number of transactions per day
            "velocity": 100000, # Amount per day
            "round_amount": 1000,  # Round number threshold
            "new_entity": 30    # Days threshold for new entity
        }
        
        # Transaction history (in-memory storage)
        self.transaction_history = {}

    def detect_anomalies(
        self,
        amount: float,
        currency: str,
        entities: List[Entity]
    ) -> List[Anomaly]:
        """
        Detect anomalies in transaction data
        """
        anomalies = []
        
        # Check for large transactions
        if amount > self.thresholds["amount"]:
            anomalies.append(
                Anomaly(
                    type="large_transaction",
                    severity=min(amount / self.thresholds["amount"], 1.0),
                    description=f"Large transaction amount: {amount} {currency}",
                    evidence=["Transaction amount exceeds threshold"]
                )
            )
        
        # Check for round numbers
        if self._is_round_number(amount):
            anomalies.append(
                Anomaly(
                    type="round_amount",
                    severity=0.7,
                    description=f"Round number transaction: {amount} {currency}",
                    evidence=["Transaction amount is a round number"]
                )
            )
        
        # Check transaction frequency and velocity
        for entity in entities:
            # Update transaction history
            self._update_transaction_history(entity.name, amount, currency)
            
            # Check frequency
            if self._check_transaction_frequency(entity.name):
                anomalies.append(
                    Anomaly(
                        type="high_frequency",
                        severity=0.8,
                        description=f"High transaction frequency for {entity.name}",
                        evidence=["Transaction frequency exceeds threshold"]
                    )
                )
            
            # Check velocity
            if self._check_transaction_velocity(entity.name):
                anomalies.append(
                    Anomaly(
                        type="high_velocity",
                        severity=0.8,
                        description=f"High transaction velocity for {entity.name}",
                        evidence=["Transaction velocity exceeds threshold"]
                    )
                )
            
            # Check for new entity
            if self._is_new_entity(entity.name):
                anomalies.append(
                    Anomaly(
                        type="new_entity",
                        severity=0.6,
                        description=f"New entity detected: {entity.name}",
                        evidence=["Entity is new to the system"]
                    )
                )
        
        return anomalies

    def _is_round_number(self, amount: float) -> bool:
        """
        Check if amount is a round number
        """
        return amount % self.thresholds["round_amount"] == 0

    def _update_transaction_history(
        self,
        entity_name: str,
        amount: float,
        currency: str
    ):
        """
        Update transaction history for an entity
        """
        current_time = datetime.now()
        
        if entity_name not in self.transaction_history:
            self.transaction_history[entity_name] = {
                "transactions": [],
                "daily_amounts": {},
                "first_seen": current_time
            }
        
        # Add transaction
        self.transaction_history[entity_name]["transactions"].append({
            "time": current_time,
            "amount": amount,
            "currency": currency
        })
        
        # Update daily amounts
        date_key = current_time.date()
        if date_key not in self.transaction_history[entity_name]["daily_amounts"]:
            self.transaction_history[entity_name]["daily_amounts"][date_key] = 0
        self.transaction_history[entity_name]["daily_amounts"][date_key] += amount
        
        # Clean up old transactions (keep last 30 days)
        self._cleanup_transaction_history(entity_name)

    def _cleanup_transaction_history(self, entity_name: str):
        """
        Remove transactions older than 30 days
        """
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(days=30)
        
        self.transaction_history[entity_name]["transactions"] = [
            t for t in self.transaction_history[entity_name]["transactions"]
            if t["time"] > cutoff_time
        ]
        
        # Clean up daily amounts
        cutoff_date = cutoff_time.date()
        self.transaction_history[entity_name]["daily_amounts"] = {
            date: amount
            for date, amount in self.transaction_history[entity_name]["daily_amounts"].items()
            if date > cutoff_date
        }

    def _check_transaction_frequency(self, entity_name: str) -> bool:
        """
        Check if transaction frequency exceeds threshold
        """
        if entity_name not in self.transaction_history:
            return False
        
        current_time = datetime.now()
        today = current_time.date()
        
        # Count transactions today
        today_transactions = sum(
            1 for t in self.transaction_history[entity_name]["transactions"]
            if t["time"].date() == today
        )
        
        return today_transactions > self.thresholds["frequency"]

    def _check_transaction_velocity(self, entity_name: str) -> bool:
        """
        Check if transaction velocity exceeds threshold
        """
        if entity_name not in self.transaction_history:
            return False
        
        current_time = datetime.now()
        today = current_time.date()
        
        # Get total amount for today
        today_amount = self.transaction_history[entity_name]["daily_amounts"].get(today, 0)
        
        return today_amount > self.thresholds["velocity"]

    def _is_new_entity(self, entity_name: str) -> bool:
        """
        Check if entity is new (first seen within threshold days)
        """
        if entity_name not in self.transaction_history:
            return True
        
        current_time = datetime.now()
        first_seen = self.transaction_history[entity_name]["first_seen"]
        
        return (current_time - first_seen).days < self.thresholds["new_entity"] 