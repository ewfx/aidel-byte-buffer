import random
from typing import List, Dict, Optional
from faker import Faker
from datetime import datetime, timedelta
import uuid

from models.entity import Entity, EntityType, Transaction, Anomaly

class FakeDataGenerator:
    def __init__(self):
        """Initialize the fake data generator with Faker instance"""
        self.faker = Faker()
        self.fake_entity_db = {}  # Cache for generated entities
        
        # Risk parameters for different entity types
        self.entity_type_risk = {
            EntityType.SHELL_COMPANY: 0.8,
            EntityType.FINANCIAL_INTERMEDIARY: 0.6,
            EntityType.CORPORATION: 0.4,
            EntityType.NON_PROFIT: 0.3,
            EntityType.GOVERNMENT_AGENCY: 0.2,
            EntityType.UNKNOWN: 0.5
        }
        
        # Country risk scores (higher = more risky)
        self.country_risk = {
            "RU": 0.8,  # Russia
            "CN": 0.7,  # China
            "IR": 0.9,  # Iran
            "KP": 0.9,  # North Korea
            "SY": 0.8,  # Syria
            "VE": 0.7,  # Venezuela
            "MM": 0.7,  # Myanmar
            "ZW": 0.6,  # Zimbabwe
            "US": 0.2,  # United States
            "GB": 0.2,  # United Kingdom
            "DE": 0.2,  # Germany
            "FR": 0.2,  # France
            "CA": 0.2,  # Canada
        }
        
        # Default to medium risk for countries not in the list
        self.default_country_risk = 0.4

    def generate_fake_transaction(self) -> Dict:
        """Generate a fake transaction with realistic data"""
        # Generate a random amount with occasional large transactions
        amount = random.choice([
            random.randint(1000, 50000),  # Normal transaction
            random.randint(50000, 200000),  # Medium transaction
            random.randint(500000, 2000000)  # Large transaction (less frequent)
        ] + [random.randint(1000, 50000)] * 8)  # Weight toward normal transactions
        
        # Occasionally make perfectly round numbers (suspicious)
        if random.random() < 0.2:
            amount = round(amount, -3)  # Round to nearest thousand
        
        # Generate transaction description
        transaction_types = ["Payment", "Transfer", "Invoice", "Service fee", "Consulting fee"]
        transaction_type = random.choice(transaction_types)
        
        # Generate entity names
        sender = self._generate_entity_name()
        recipient = self._generate_entity_name()
        
        transaction_data = f"{transaction_type} from {sender} to {recipient}"
        
        return {
            "transaction_id": f"TXN{uuid.uuid4().hex[:8].upper()}",
            "transaction_data": transaction_data,
            "amount": amount,
            "currency": random.choice(["USD", "EUR", "GBP", "JPY", "CHF"]),
            "date": self.faker.date_time_between(start_date="-30d", end_date="now").strftime("%Y-%m-%d")
        }

    def _generate_entity_name(self) -> str:
        """Generate a realistic company name"""
        name_patterns = [
            lambda: f"{self.faker.company()}",
            lambda: f"{self.faker.last_name()} {random.choice(['Inc', 'LLC', 'Corp', 'Group'])}",
            lambda: f"{self.faker.last_name()} & {self.faker.last_name()} {random.choice(['Associates', 'Partners'])}",
            lambda: f"{self.faker.word().capitalize()} {random.choice(['Holdings', 'Investments', 'Capital', 'Industries'])}",
            lambda: f"{random.choice(['Global', 'International', 'United', 'National'])} {self.faker.word().capitalize()} {random.choice(['Corp', 'Inc', 'Co', 'Ltd'])}"
        ]
        
        return random.choice(name_patterns)()

    async def get_fake_entity_data(self, entity_name: str) -> Entity:
        """Generate fake but realistic entity data for a given name"""
        # Check if we've already generated this entity
        if entity_name in self.fake_entity_db:
            return self.fake_entity_db[entity_name]
        
        # Determine entity type based on name patterns
        entity_type = self._determine_entity_type(entity_name)
        
        # Generate registration data
        registration_data = self._generate_registration_data(entity_name, entity_type)
        
        # Create entity with appropriate attributes
        entity = Entity(
            name=entity_name,
            type=entity_type,
            confidence_score=random.uniform(0.7, 1.0),
            evidence_sources=self._generate_evidence_sources(),
            registration_number=registration_data.get("registration_number"),
            jurisdiction=registration_data.get("jurisdiction"),
            incorporation_date=registration_data.get("incorporation_date"),
            directors=registration_data.get("directors", []),
            shareholders=registration_data.get("shareholders", []),
            sanctions_status=self._determine_sanctions_status(entity_name, entity_type, registration_data.get("jurisdiction")),
            risk_factors=self._generate_risk_factors(entity_type),
            reputation_score=self._generate_reputation_score(entity_type)
        )
        
        # Cache the entity
        self.fake_entity_db[entity_name] = entity
        return entity

    def _determine_entity_type(self, entity_name: str) -> EntityType:
        """Determine entity type based on name patterns"""
        entity_name_lower = entity_name.lower()
        
        # Shell company indicators
        if any(word in entity_name_lower for word in ["holdings", "investments", "group", "capital", "partners"]):
            return EntityType.SHELL_COMPANY
        
        # Financial intermediary indicators
        if any(word in entity_name_lower for word in ["bank", "financial", "invest", "capital", "fund"]):
            return EntityType.FINANCIAL_INTERMEDIARY
        
        # Government agency indicators
        if any(word in entity_name_lower for word in ["government", "ministry", "agency", "department"]):
            return EntityType.GOVERNMENT_AGENCY
        
        # Non-profit indicators
        if any(word in entity_name_lower for word in ["foundation", "charity", "trust", "association"]):
            return EntityType.NON_PROFIT
        
        # Default to corporation
        return EntityType.CORPORATION
    
    def _generate_registration_data(self, entity_name: str, entity_type: EntityType) -> Dict:
        """Generate fake registration data"""
        # Generate a random country code
        country_code = random.choice(list(self.country_risk.keys()))
        
        # Higher risk jurisdictions for shell companies
        if entity_type == EntityType.SHELL_COMPANY:
            country_code = random.choice(["RU", "CN", "IR", "VE", "MM", "ZW", "KP", "SY"])
        
        # Generate directors and shareholders
        directors = [self.faker.name() for _ in range(random.randint(1, 5))]
        
        # Shell companies might have fewer shareholders or hidden ownership
        if entity_type == EntityType.SHELL_COMPANY:
            shareholders = [self.faker.name() for _ in range(random.randint(0, 2))]
        else:
            shareholders = [self.faker.name() for _ in range(random.randint(1, 8))]
        
        # Generate incorporation date
        years_ago = random.randint(1, 30)
        incorporation_date = (datetime.now() - timedelta(days=365 * years_ago)).strftime("%Y-%m-%d")
        
        # New shell companies are more suspicious
        if entity_type == EntityType.SHELL_COMPANY and random.random() < 0.4:
            incorporation_date = (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
        
        return {
            "registration_number": f"{country_code}{self.faker.bothify('#######')}",
            "jurisdiction": country_code,
            "incorporation_date": incorporation_date,
            "directors": directors,
            "shareholders": shareholders
        }
    
    def _determine_sanctions_status(self, entity_name: str, entity_type: EntityType, jurisdiction: str) -> bool:
        """Determine if entity is on sanctions list"""
        # Higher probability of sanctions for certain entity types or jurisdictions
        base_probability = 0.05  # 5% base probability
        
        if entity_type == EntityType.SHELL_COMPANY:
            base_probability += 0.1
        
        if jurisdiction in ["RU", "IR", "KP", "SY"]:
            base_probability += 0.2
        
        return random.random() < base_probability
    
    def _generate_evidence_sources(self) -> List[str]:
        """Generate evidence sources"""
        all_sources = [
            "Company Registry", 
            "SEC EDGAR", 
            "LEI Database", 
            "Wikipedia", 
            "News Analysis", 
            "Sanctions List"
        ]
        
        # Select a random number of sources
        num_sources = random.randint(1, len(all_sources))
        return random.sample(all_sources, num_sources)
    
    def _generate_risk_factors(self, entity_type: EntityType) -> Dict[str, float]:
        """Generate risk factors based on entity type"""
        risk_factors = {}
        
        if entity_type == EntityType.SHELL_COMPANY:
            risk_factors["shell_structure"] = random.uniform(0.6, 0.9)
            risk_factors["complex_ownership"] = random.uniform(0.5, 0.8)
        
        if entity_type == EntityType.FINANCIAL_INTERMEDIARY:
            risk_factors["high_volume"] = random.uniform(0.4, 0.7)
        
        # Add random risk factors with low probability
        if random.random() < 0.2:
            risk_factors["news_mention"] = random.uniform(0.3, 0.7)
        
        if random.random() < 0.1:
            risk_factors["regulatory_issue"] = random.uniform(0.5, 0.9)
            
        return risk_factors
    
    def _generate_reputation_score(self, entity_type: EntityType) -> float:
        """Generate reputation score based on entity type"""
        # Base reputation ranges by entity type
        if entity_type == EntityType.SHELL_COMPANY:
            base_range = (0.2, 0.5)
        elif entity_type == EntityType.FINANCIAL_INTERMEDIARY:
            base_range = (0.3, 0.7)
        elif entity_type == EntityType.GOVERNMENT_AGENCY:
            base_range = (0.5, 0.8)
        else:
            base_range = (0.4, 0.9)
        
        return random.uniform(base_range[0], base_range[1])
    
    def generate_fake_anomalies(self, amount: float, entities: List[Entity]) -> List[Anomaly]:
        """Generate fake anomalies based on transaction and entities"""
        anomalies = []
        
        # Large transaction anomaly
        if amount > 1000000:
            severity = min(amount / 1000000, 1.0)
            anomalies.append(Anomaly(
                type="large_transaction",
                severity=severity,
                description=f"Large transaction amount: {amount}",
                evidence=["Transaction amount exceeds threshold"]
            ))
        
        # Round number anomaly
        if amount % 1000 == 0 and amount > 10000:
            anomalies.append(Anomaly(
                type="round_amount",
                severity=0.7,
                description=f"Round number transaction: {amount}",
                evidence=["Transaction amount is a round number"]
            ))
        
        # Entity-based anomalies
        for entity in entities:
            # High-risk jurisdiction anomaly
            if entity.jurisdiction in self.country_risk and self.country_risk[entity.jurisdiction] > 0.6:
                anomalies.append(Anomaly(
                    type="high_risk_jurisdiction",
                    severity=self.country_risk[entity.jurisdiction],
                    description=f"Entity in high-risk jurisdiction: {entity.jurisdiction}",
                    evidence=[f"Entity jurisdiction is {entity.jurisdiction}"]
                ))
            
            # Shell company anomaly
            if entity.type == EntityType.SHELL_COMPANY:
                anomalies.append(Anomaly(
                    type="shell_company",
                    severity=0.8,
                    description=f"Entity appears to be a shell company: {entity.name}",
                    evidence=["Entity classification", "Structure analysis"]
                ))
            
            # Recently formed entity anomaly
            if entity.incorporation_date:
                try:
                    incorporation_date = datetime.strptime(entity.incorporation_date, "%Y-%m-%d")
                    days_since_incorporation = (datetime.now() - incorporation_date).days
                    if days_since_incorporation < 180:  # Less than 6 months
                        anomalies.append(Anomaly(
                            type="new_entity",
                            severity=0.6,
                            description=f"Recently formed entity: {entity.name}",
                            evidence=[f"Incorporation date: {entity.incorporation_date}"]
                        ))
                except ValueError:
                    pass  # Skip if date parsing fails 