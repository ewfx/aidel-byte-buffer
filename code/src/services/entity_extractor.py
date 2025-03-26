import spacy
from typing import List
import re
from models.entity import Entity, EntityType

class EntityExtractor:
    def __init__(self):
        # Load English language model
        self.nlp = spacy.load("en_core_web_sm")
        
        # Common company suffixes
        self.company_suffixes = [
            r'inc\.?$', r'corp\.?$', r'corporation$', r'ltd\.?$', r'limited$',
            r'llc$', r'gmbh$', r's\.a\.$', r's\.p\.a\.$', r'plc$'
        ]
        
        # Common non-profit indicators
        self.nonprofit_indicators = [
            r'foundation$', r'charity$', r'ngo$', r'non-profit$', r'nonprofit$',
            r'association$', r'society$', r'trust$'
        ]
        
        # Common shell company indicators
        self.shell_indicators = [
            r'holdings$', r'investments$', r'group$', r'capital$', r'partners$',
            r'management$', r'consulting$', r'advisory$'
        ]

    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text using NLP and pattern matching
        """
        doc = self.nlp(text)
        entities = []
        
        # Extract organizations using spaCy
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entity_type = self._classify_entity_type(ent.text)
                confidence_score = self._calculate_confidence_score(ent.text, entity_type)
                
                entity = Entity(
                    name=ent.text,
                    type=entity_type,
                    confidence_score=confidence_score,
                    evidence_sources=["NLP Extraction"]
                )
                entities.append(entity)
        
        # Additional pattern matching for entities that might have been missed
        additional_entities = self._extract_entities_by_pattern(text)
        entities.extend(additional_entities)
        
        return entities

    def _classify_entity_type(self, entity_name: str) -> EntityType:
        """
        Classify entity type based on name patterns and indicators
        """
        entity_name = entity_name.lower()
        
        # Check for non-profit indicators
        if any(re.search(pattern, entity_name) for pattern in self.nonprofit_indicators):
            return EntityType.NON_PROFIT
        
        # Check for shell company indicators
        if any(re.search(pattern, entity_name) for pattern in self.shell_indicators):
            return EntityType.SHELL_COMPANY
        
        # Check for company suffixes
        if any(re.search(pattern, entity_name) for pattern in self.company_suffixes):
            return EntityType.CORPORATION
        
        # Check for government agency indicators
        if any(word in entity_name for word in ['government', 'ministry', 'department', 'agency']):
            return EntityType.GOVERNMENT_AGENCY
        
        # Check for financial intermediary indicators
        if any(word in entity_name for word in ['bank', 'financial', 'investment', 'fund']):
            return EntityType.FINANCIAL_INTERMEDIARY
        
        return EntityType.UNKNOWN

    def _calculate_confidence_score(self, entity_name: str, entity_type: EntityType) -> float:
        """
        Calculate confidence score based on entity name and type
        """
        base_score = 0.5
        
        # Add confidence based on entity type classification
        if entity_type != EntityType.UNKNOWN:
            base_score += 0.3
        
        # Add confidence based on name structure
        if re.search(r'[A-Z]', entity_name):  # Contains capital letters
            base_score += 0.1
        
        if any(char.isdigit() for char in entity_name):  # Contains numbers
            base_score += 0.1
        
        return min(base_score, 1.0)

    def _extract_entities_by_pattern(self, text: str) -> List[Entity]:
        """
        Extract entities using pattern matching for cases that might have been missed by NLP
        """
        entities = []
        
        # Pattern for company names with common suffixes
        company_pattern = r'\b[A-Z][a-zA-Z\s]+(?:' + '|'.join(self.company_suffixes) + r')\b'
        matches = re.finditer(company_pattern, text)
        
        for match in matches:
            entity_name = match.group()
            entity_type = self._classify_entity_type(entity_name)
            confidence_score = self._calculate_confidence_score(entity_name, entity_type)
            
            entity = Entity(
                name=entity_name,
                type=entity_type,
                confidence_score=confidence_score,
                evidence_sources=["Pattern Matching"]
            )
            entities.append(entity)
        
        return entities 