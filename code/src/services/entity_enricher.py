import aiohttp
import os
from typing import List, Optional
from bs4 import BeautifulSoup
import json
import re
from src.models.entity import Entity, EntityType

class EntityEnricher:
    def __init__(self):
        # Use free APIs instead of OpenCorporates
        self.news_api_key = os.getenv("NEWS_API_KEY", "")
        
        # Open-source sanctions list URLs
        self.sanctions_list_urls = [
            "https://www.treasury.gov/ofac/downloads/sdn.xml",  # US OFAC Sanctions
            "https://www.sanctionsmap.eu/api/v1/sanctions"      # EU Sanctions
        ]
        
        # Open data sources for company information
        self.company_data_sources = {
            "wikipedia": "https://en.wikipedia.org/wiki/",
            "sec_edgar": "https://data.sec.gov/submissions/",
            "open_corporates_web": "https://opencorporates.com/companies/", # Web scraping fallback
            "lei_lookup": "https://api.gleif.org/api/v1/lei-records?filter[lei]="
        }
        
        # Cache for API responses
        self.entity_cache = {}

    async def enrich_entity(self, entity: Entity) -> Entity:
        """
        Enrich entity with additional information from various sources
        """
        # Check cache first
        if entity.name in self.entity_cache:
            return self.entity_cache[entity.name]
        
        # Gather information from multiple sources
        async with aiohttp.ClientSession() as session:
            # Get company registry data from free sources
            registry_data = await self._get_registry_data(session, entity.name)
            if registry_data:
                entity.registration_number = registry_data.get("registration_number")
                entity.jurisdiction = registry_data.get("jurisdiction")
                entity.incorporation_date = registry_data.get("incorporation_date")
                entity.directors = registry_data.get("directors")
                entity.shareholders = registry_data.get("shareholders")
                entity.evidence_sources.append(registry_data.get("source", "Company Registry"))
            
            # Check sanctions lists
            sanctions_status = await self._check_sanctions(session, entity.name)
            entity.sanctions_status = sanctions_status
            if sanctions_status:
                entity.evidence_sources.append("Sanctions List")
            
            # Get news and reputation data
            reputation_data = await self._get_reputation_data(session, entity.name)
            if reputation_data:
                entity.reputation_score = reputation_data.get("reputation_score", 0.0)
                entity.risk_factors = reputation_data.get("risk_factors", {})
                entity.evidence_sources.append("News Analysis")
            
            # Update confidence score based on gathered evidence
            entity.confidence_score = self._update_confidence_score(entity)
        
        # Cache the enriched entity
        self.entity_cache[entity.name] = entity
        return entity

    async def _get_registry_data(self, session: aiohttp.ClientSession, entity_name: str) -> Optional[dict]:
        """
        Get company registry data from free and open sources
        """
        # Try to get data from LEI (Legal Entity Identifier) database - free API
        try:
            url = f"{self.company_data_sources['lei_lookup']}{entity_name}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data"):
                        company = data["data"][0]["attributes"]
                        return {
                            "registration_number": company.get("entity", {}).get("registrationNumber"),
                            "jurisdiction": company.get("entity", {}).get("jurisdiction"),
                            "incorporation_date": None,  # Not available in LEI data
                            "directors": [],
                            "shareholders": [],
                            "source": "LEI Database"
                        }
        except Exception as e:
            print(f"Error fetching LEI data: {str(e)}")
        
        # Try to get data from SEC EDGAR for US companies - free API
        try:
            # Clean entity name for URL
            clean_name = entity_name.lower().replace(" ", "")
            url = f"{self.company_data_sources['sec_edgar']}{clean_name}/index.json"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("cik"):
                        return {
                            "registration_number": data.get("cik"),
                            "jurisdiction": "US",
                            "incorporation_date": None,
                            "directors": [],
                            "shareholders": [],
                            "source": "SEC EDGAR"
                        }
        except Exception as e:
            print(f"Error fetching SEC data: {str(e)}")
        
        # Fallback to Wikipedia for basic information - web scraping
        try:
            # Clean entity name for URL
            clean_name = entity_name.replace(" ", "_")
            url = f"{self.company_data_sources['wikipedia']}{clean_name}"
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract basic info from infobox
                    infobox = soup.find('table', {'class': 'infobox'})
                    if infobox:
                        # Try to extract info from Wikipedia infobox
                        founded = None
                        headquarters = None
                        
                        rows = infobox.find_all('tr')
                        for row in rows:
                            header = row.find('th')
                            if header and 'Founded' in header.text:
                                founded = row.find('td').text.strip()
                            if header and ('Headquarters' in header.text or 'Location' in header.text):
                                headquarters = row.find('td').text.strip()
                        
                        return {
                            "registration_number": None,
                            "jurisdiction": headquarters,
                            "incorporation_date": founded,
                            "directors": [],
                            "shareholders": [],
                            "source": "Wikipedia"
                        }
        except Exception as e:
            print(f"Error fetching Wikipedia data: {str(e)}")
        
        return None

    async def _check_sanctions(self, session: aiohttp.ClientSession, entity_name: str) -> bool:
        """
        Check if entity is on sanctions lists using free data sources
        """
        # Try open-source sanctions lists
        for sanctions_url in self.sanctions_list_urls:
            try:
                async with session.get(sanctions_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Simple check for entity name in the content
                        if entity_name.lower() in content.lower():
                            return True
            except Exception as e:
                print(f"Error checking sanctions at {sanctions_url}: {str(e)}")
        
        # Fallback to the Consolidated Screening List API - free US government API
        try:
            url = f"https://api.trade.gov/consolidated_screening_list/search?name={entity_name}&api_key=DEMO_KEY"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("total") > 0
        except Exception as e:
            print(f"Error checking consolidated screening list: {str(e)}")
            
        return False

    async def _get_reputation_data(self, session: aiohttp.ClientSession, entity_name: str) -> Optional[dict]:
        """
        Get reputation data from news and other sources
        """
        # Try free tier of News API if key is available
        if self.news_api_key:
            try:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": entity_name,
                    "apiKey": self.news_api_key,
                    "language": "en",
                    "sortBy": "relevancy"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("articles", [])
                        
                        # Analyze sentiment and extract risk factors
                        risk_factors = {}
                        sentiment_scores = []
                        
                        for article in articles[:10]:  # Analyze top 10 articles
                            # Simple sentiment analysis
                            title = article.get("title", "").lower()
                            description = article.get("description", "").lower()
                            
                            # Check for negative keywords
                            negative_keywords = ["fraud", "scandal", "investigation", "lawsuit", "fine", "penalty"]
                            for keyword in negative_keywords:
                                if keyword in title or keyword in description:
                                    risk_factors[keyword] = risk_factors.get(keyword, 0) + 1
                            
                            # Simple sentiment scoring
                            sentiment = 0
                            if any(word in title or word in description for word in ["positive", "growth", "success"]):
                                sentiment += 1
                            if any(word in title or word in description for word in ["negative", "decline", "loss"]):
                                sentiment -= 1
                            sentiment_scores.append(sentiment)
                        
                        # Calculate average sentiment score
                        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                        
                        return {
                            "reputation_score": (avg_sentiment + 1) / 2,  # Normalize to 0-1
                            "risk_factors": risk_factors
                        }
            except Exception as e:
                print(f"Error getting news data: {str(e)}")
        
        # Fallback to Google News (web scraping) - free but rate limited
        try:
            # Format entity name for URL
            query = entity_name.replace(" ", "+")
            url = f"https://news.google.com/rss/search?q={query}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'xml')
                    
                    items = soup.find_all('item')
                    count = len(items)
                    
                    # Very simple reputation score based on number of news items
                    # More news usually means more scrutiny
                    reputation_score = 0.5
                    risk_factors = {"news_volume": min(count / 10, 1.0)}
                    
                    return {
                        "reputation_score": reputation_score,
                        "risk_factors": risk_factors
                    }
        except Exception as e:
            print(f"Error getting Google News data: {str(e)}")
        
        return None

    def _update_confidence_score(self, entity: Entity) -> float:
        """
        Update confidence score based on gathered evidence
        """
        base_score = entity.confidence_score
        
        # Add confidence based on evidence sources
        evidence_bonus = len(entity.evidence_sources) * 0.1
        base_score += evidence_bonus
        
        # Add confidence based on completeness of data
        if entity.registration_number:
            base_score += 0.1
        if entity.jurisdiction:
            base_score += 0.1
        if entity.incorporation_date:
            base_score += 0.1
        if entity.directors:
            base_score += 0.1
        if entity.shareholders:
            base_score += 0.1
        
        return min(base_score, 1.0)

    async def get_entity_details(self, entity_id: str) -> Optional[Entity]:
        """
        Get entity details from cache or fetch if not available
        """
        if entity_id in self.entity_cache:
            return self.entity_cache[entity_id]
        
        # Create a basic entity and enrich it
        entity = Entity(
            name=entity_id,
            type=EntityType.UNKNOWN,
            confidence_score=0.5,
            evidence_sources=[]
        )
        
        return await self.enrich_entity(entity) 