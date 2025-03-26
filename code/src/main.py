from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime
import re
import os
from pathlib import Path

from services.entity_extractor import EntityExtractor
from services.risk_scorer import RiskScorer
from services.anomaly_detector import AnomalyDetector
from models.entity import Entity, Transaction, AnalysisResult
from services.fake_data_generator import FakeDataGenerator


# Get the current directory
current_dir = Path(__file__).parent

app = FastAPI(
    title="Entity Risk Assessment System",
    description="AI-powered system for automated entity risk assessment and verification using fake data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
entity_extractor = EntityExtractor()
risk_scorer = RiskScorer()
anomaly_detector = AnomalyDetector()
fake_data_generator = FakeDataGenerator()

class TransactionRequest(BaseModel):
    transaction_id: str
    transaction_data: str
    amount: float
    currency: str
    date: str

@app.get("/", include_in_schema=False)
async def root():
    print("Root called")
    """Generate a simple HTML index page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Entity Risk Assessment System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Entity Risk Assessment System</h1>
            <div class="alert alert-info mt-4">
                <h4>Welcome to the Entity Risk Assessment API</h4>
                <p>This system analyzes transaction data to identify and risk-score entities using synthetic data.</p>
            </div>
            
            <div class="card mt-4">
                <div class="card-header">
                    <h3>API Endpoints</h3>
                </div>
                <div class="card-body">
                    <ul class="list-group">
                        <li class="list-group-item">
                            <strong>POST /api/v1/analyze</strong> - Analyze transaction data
                        </li>
                        <li class="list-group-item">
                            <strong>GET /api/v1/generate-transaction</strong> - Generate a random transaction
                        </li>
                        <li class="list-group-item">
                            <strong>POST /api/v1/batch-analyze</strong> - Generate and analyze multiple transactions
                        </li>
                        <li class="list-group-item">
                            <strong>GET /api/v1/entity/{entity_id}</strong> - Get entity details
                        </li>
                        <li class="list-group-item">
                            <strong>GET /api/v1/risk-score/{entity_id}</strong> - Get entity risk score
                        </li>
                    </ul>
                </div>
            </div>
            
            <div class="mt-4">
                <a href="/docs" class="btn btn-primary">View API Documentation</a>
            </div>
            
            <footer class="mt-5 text-center text-muted">
                <p>Entity Risk Assessment System - Powered by FastAPI and synthetic data</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/v1/analyze", response_model=List[AnalysisResult])
async def analyze_transaction(request: TransactionRequest):
    try:
        # Extract entities from transaction data
        entities = entity_extractor.extract_entities(request.transaction_data)
        
        # Enrich entities with fake data
        enriched_entities = []
        for entity in entities:
            enriched_entity = await fake_data_generator.get_fake_entity_data(entity.name)
            enriched_entities.append(enriched_entity)
        
        # Generate fake anomalies
        anomalies = fake_data_generator.generate_fake_anomalies(
            request.amount,
            enriched_entities
        )
        
        # Calculate risk scores
        results = []
        for entity in enriched_entities:
            risk_score = risk_scorer.calculate_risk_score(
                entity,
                anomalies,
                request.amount
            )
            
            result = AnalysisResult(
                transaction_id=request.transaction_id,
                extracted_entity=[entity.name],
                entity_type=[entity.type],
                risk_score=risk_score,
                supporting_evidence=entity.evidence_sources,
                confidence_score=entity.confidence_score,
                reason=risk_scorer.generate_risk_reason(entity, risk_score, anomalies)
            )
            results.append(result)
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/entity/{entity_id}", response_model=Entity)
async def get_entity_details(entity_id: str):
    try:
        entity = await fake_data_generator.get_fake_entity_data(entity_id)
        return entity
    except Exception as e:
        raise HTTPException(status_code=404, detail="Entity not found")

@app.get("/api/v1/risk-score/{entity_id}")
async def get_entity_risk_score(entity_id: str):
    try:
        entity = await fake_data_generator.get_fake_entity_data(entity_id)
        risk_score = risk_scorer.calculate_risk_score(entity)
        return {"entity_id": entity_id, "risk_score": risk_score}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Entity not found")

@app.get("/api/v1/generate-transaction")
async def generate_transaction():
    """Generate a fake transaction for testing"""
    return fake_data_generator.generate_fake_transaction()

@app.post("/api/v1/batch-analyze", response_model=List[AnalysisResult])
async def batch_analyze():
    """Generate and analyze a batch of fake transactions for testing"""
    results = []
    
    # Generate 5 random transactions
    for _ in range(5):
        transaction = fake_data_generator.generate_fake_transaction()
        print("Fake transaction", transaction)
        request = TransactionRequest(**transaction)
        print("Request", request)
        transaction_results = await analyze_transaction(request)
        print("Transaction results", transaction_results)
        results.extend(transaction_results)
    
    return results

@app.get("/api/v1/extract-entities")
async def extract_entities(text: str):
    """Extract entities from text for testing"""
    entities = entity_extractor.extract_entities(text)
    return [{"name": entity.name, "type": entity.type, "confidence": entity.confidence_score} for entity in entities]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True) 