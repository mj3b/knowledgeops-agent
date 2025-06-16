# NAVO API

This directory contains the FastAPI application that provides RESTful and WebSocket APIs for NAVO's knowledge discovery capabilities.

## Directory Structure

```
api/
├── __init__.py                 # Package initialization
├── app.py                      # Main FastAPI application
├── routes/                     # API route definitions
│   ├── __init__.py
│   ├── query.py               # Query processing endpoints
│   ├── memory.py              # Memory and learning endpoints
│   ├── admin.py               # Administrative endpoints
│   └── health.py              # Health check endpoints
├── middleware/                 # Custom middleware
│   ├── __init__.py
│   ├── auth.py                # Authentication middleware
│   ├── cors.py                # CORS middleware
│   └── logging.py             # Request logging middleware
├── models/                     # Pydantic models
│   ├── __init__.py
│   ├── request.py             # Request models
│   ├── response.py            # Response models
│   └── common.py              # Common models
└── dependencies/               # FastAPI dependencies
    ├── __init__.py
    ├── auth.py                # Authentication dependencies
    └── database.py            # Database dependencies
```

## API Overview

### Main Application (`app.py`)
The central FastAPI application that configures all routes, middleware, and dependencies.

**Key Features:**
- Automatic OpenAPI documentation generation
- Request/response validation with Pydantic
- Comprehensive error handling and logging
- WebSocket support for real-time interactions
- CORS configuration for web clients
- Authentication and authorization middleware

### API Endpoints

#### Query Processing (`routes/query.py`)
Core endpoints for knowledge discovery and query processing.

**Endpoints:**
- `POST /api/v1/query` - Process natural language queries
- `GET /api/v1/query/{query_id}` - Retrieve query results
- `POST /api/v1/query/batch` - Process multiple queries
- `WebSocket /ws/query` - Real-time query processing

#### Memory and Learning (`routes/memory.py`)
Endpoints for memory management and learning capabilities.

**Endpoints:**
- `POST /api/v1/memory/feedback` - Submit user feedback
- `GET /api/v1/memory/patterns` - Retrieve learned patterns
- `GET /api/v1/memory/analytics` - Memory usage analytics
- `DELETE /api/v1/memory/cleanup` - Trigger memory cleanup

#### Administration (`routes/admin.py`)
Administrative endpoints for system management and monitoring.

**Endpoints:**
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/integrations` - Integration status
- `POST /api/v1/admin/cache/clear` - Clear system cache
- `GET /api/v1/admin/users` - User management

#### Health Monitoring (`routes/health.py`)
Health check and monitoring endpoints.

**Endpoints:**
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health information
- `GET /ready` - Readiness probe for Kubernetes
- `GET /metrics` - Prometheus metrics

## Request/Response Models

### Query Request Model
```python
from pydantic import BaseModel
from typing import Optional, Dict, List

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, str]] = None
    options: Optional[QueryOptions] = None
    user_id: Optional[str] = None

class QueryOptions(BaseModel):
    max_results: int = 5
    sources: Optional[List[str]] = None
    include_reasoning: bool = True
    include_metadata: bool = True
```

### Query Response Model
```python
class QueryResponse(BaseModel):
    query_id: str
    results: List[SearchResult]
    reasoning: Optional[ReasoningResult] = None
    metadata: QueryMetadata

class SearchResult(BaseModel):
    id: str
    title: str
    url: str
    source: str
    relevance_score: float
    freshness: str
    summary: str
    confidence: float

class ReasoningResult(BaseModel):
    summary: str
    confidence: float
    reasoning_id: str
    execution_time_ms: int
    steps: List[ReasoningStep]
```

## Authentication and Authorization

### JWT Authentication
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Role-Based Access Control
```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
```

## Middleware

### Request Logging Middleware
```python
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response
```

### CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourcompany.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## WebSocket Support

### Real-Time Query Processing
```python
from fastapi import WebSocket, WebSocketDisconnect
import json

@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_text()
            query_data = json.loads(data)
            
            # Process query with real-time updates
            async for update in process_query_stream(query_data):
                await websocket.send_text(json.dumps(update))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
```

### Connection Management
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
```

## Error Handling

### Custom Exception Handlers
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class NAVOException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

@app.exception_handler(NAVOException)
async def navo_exception_handler(request: Request, exc: NAVOException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": "NAVOException",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### Validation Error Handling
```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## API Documentation

### OpenAPI Configuration
```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="NAVO API",
        version="2.0.0",
        description="Enterprise Knowledge Discovery Platform API",
        routes=app.routes,
    )
    
    # Add custom schema elements
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### API Examples
```python
from fastapi import FastAPI
from pydantic import BaseModel

class QueryExample(BaseModel):
    query: str = "Where's the retry logic for project scripts?"
    context: dict = {"user_id": "user123", "team": "engineering"}
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Where's the retry logic for project scripts?",
                "context": {
                    "user_id": "user123",
                    "team": "engineering",
                    "project": "PROJECT01"
                },
                "options": {
                    "max_results": 5,
                    "include_reasoning": True,
                    "sources": ["confluence", "sharepoint"]
                }
            }
        }
```

## Performance Optimization

### Response Caching
```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=1000)
async def get_cached_query_result(query_hash: str):
    cached_result = redis_client.get(f"query:{query_hash}")
    if cached_result:
        return json.loads(cached_result)
    return None

async def cache_query_result(query_hash: str, result: dict, ttl: int = 3600):
    redis_client.setex(f"query:{query_hash}", ttl, json.dumps(result))
```

### Request Compression
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Background Tasks
```python
from fastapi import BackgroundTasks

async def log_query_analytics(query_data: dict):
    # Log analytics in background
    await analytics_service.log_query(query_data)

@app.post("/api/v1/query")
async def process_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks
):
    result = await query_processor.process(request)
    
    # Log analytics in background
    background_tasks.add_task(log_query_analytics, request.dict())
    
    return result
```

## Testing

### API Testing
```python
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

def test_query_endpoint():
    response = client.post(
        "/api/v1/query",
        json={
            "query": "test query",
            "context": {"user_id": "test_user"}
        }
    )
    assert response.status_code == 200
    assert "results" in response.json()

@pytest.mark.asyncio
async def test_websocket_query():
    with client.websocket_connect("/ws/query") as websocket:
        websocket.send_json({"query": "test query"})
        data = websocket.receive_json()
        assert "type" in data
```

### Load Testing
```python
import asyncio
import aiohttp
import time

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.post(
                "http://localhost:8000/api/v1/query",
                json={"query": f"test query {i}"}
            )
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"Processed {len(responses)} requests in {end_time - start_time:.2f}s")
```

## Deployment

### Production Configuration
```python
import os
from fastapi import FastAPI

app = FastAPI(
    title="NAVO API",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# Production-specific middleware
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
```

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.navo.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: navo-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: navo-api
  template:
    metadata:
      labels:
        app: navo-api
    spec:
      containers:
      - name: navo-api
        image: navo:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENTERPRISE_GPT_API_KEY
          valueFrom:
            secretKeyRef:
              name: navo-secrets
              key: enterprise-gpt-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

The API directory provides a comprehensive, production-ready FastAPI application that exposes NAVO's knowledge discovery capabilities through RESTful and WebSocket APIs, with full authentication, authorization, monitoring, and documentation support.

