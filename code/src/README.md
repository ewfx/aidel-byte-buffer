# Entity Risk Assessment System

An AI-powered system for automated entity risk assessment and verification using multi-source transaction data.

## Features

- Entity extraction from structured and unstructured transaction data
- Entity enrichment with synthetic data
- Anomaly detection for fraud identification
- Entity classification
- Risk scoring system
- RESTful API interface

## Implementation Approach

This system uses synthetic data generation with Faker to create realistic:
- Company information (names, registration numbers, jurisdictions)
- Transaction data
- Risk factors and anomalies
- Entity relationship data

The fake data is generated deterministically for given entity names, ensuring consistency while eliminating the need for external APIs.

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Download required NLP models:
```bash
python -m spacy download en_core_web_sm
```

## Configuration

Create a `.env` file in the root directory with the following variables:
```
# Free News API Key (optional)
NEWS_API_KEY=your_news_api_key

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Risk Assessment Parameters
LARGE_TRANSACTION_THRESHOLD=1000000
TRANSACTION_FREQUENCY_THRESHOLD=5
TRANSACTION_VELOCITY_THRESHOLD=100000
ROUND_AMOUNT_THRESHOLD=1000
NEW_ENTITY_THRESHOLD_DAYS=30
```

## Usage

1. Start the server:
```bash
uvicorn src.main:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

3. Use one of the testing endpoints:
   - `/api/v1/generate-transaction`: Generate a random transaction
   - `/api/v1/batch-analyze`: Generate and analyze a batch of random transactions
   - `/api/v1/extract-entities?text=Your text here`: Extract entities from text

4. Or send a custom transaction request:
```json
{
    "transaction_id": "TXN001",
    "transaction_data": "Payment from Acme Corporation to SovCo Capital Partners",
    "amount": 100000,
    "currency": "USD",
    "date": "2024-03-24"
}
```

## Risk Scoring Parameters

The risk score (0-1) is calculated based on:
- Entity type (shell company: +0.3, non-profit: +0.1)
- Sanctions list presence (+0.5)
- Transaction anomalies (+0.2)
- Entity reputation score (-0.2 to +0.2)
- Geographic risk factors (+0.1 to +0.3)

## API Endpoints

- GET `/api/v1/generate-transaction`: Generate a fake transaction
- POST `/api/v1/analyze`: Analyze transaction data
- POST `/api/v1/batch-analyze`: Generate and analyze multiple transactions
- GET `/api/v1/entity/{entity_id}`: Get entity details
- GET `/api/v1/risk-score/{entity_id}`: Get entity risk score
- GET `/api/v1/extract-entities`: Extract entities from text

## Sample Output

```json
[
  {
    "transaction_id": "TXN123ABC",
    "extracted_entity": ["SovCo Capital Partners"],
    "entity_type": ["Shell Company"],
    "risk_score": 0.75,
    "supporting_evidence": ["LEI Database", "News Analysis", "Pattern Matching"],
    "confidence_score": 0.92,
    "reason": "Entity is classified as a shell company | Entity is based in a high-risk jurisdiction (RU)"
  }
]
```

## Deployment Options

### Local Development
- Run on your local machine using uvicorn

### Docker Deployment
1. Build the Docker image:
```bash
docker build -t entity-risk-assessment:latest .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 entity-risk-assessment:latest
```

### Cloud Deployment

#### Heroku
```bash
heroku create
git push heroku main
```

#### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/entity-risk-assessment
gcloud run deploy --image gcr.io/PROJECT_ID/entity-risk-assessment --platform managed
```

## License

MIT License 