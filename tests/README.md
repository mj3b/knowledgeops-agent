# NAVO Tests

This directory contains comprehensive test suites for all NAVO components, ensuring reliability, performance, and correctness across the entire system.

## Directory Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── core/                   # Core component tests
│   │   ├── test_navo_engine.py
│   │   ├── test_memory_layer.py
│   │   ├── test_reasoning_engine.py
│   │   ├── test_query_processor.py
│   │   ├── test_response_generator.py
│   │   ├── test_cache_manager.py
│   │   └── test_permission_manager.py
│   ├── integrations/           # Integration tests
│   │   ├── test_confluence_client.py
│   │   ├── test_sharepoint_client.py
│   │   └── test_enterprise_gpt_client.py
│   └── api/                    # API tests
│       ├── test_query_routes.py
│       ├── test_memory_routes.py
│       ├── test_admin_routes.py
│       └── test_health_routes.py
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_end_to_end.py
│   ├── test_memory_learning.py
│   ├── test_reasoning_pipeline.py
│   └── test_multi_source_search.py
├── performance/                # Performance tests
│   ├── __init__.py
│   ├── test_load_performance.py
│   ├── test_memory_performance.py
│   └── test_concurrent_queries.py
├── fixtures/                   # Test data and fixtures
│   ├── __init__.py
│   ├── sample_documents.py
│   ├── mock_responses.py
│   └── test_data.json
└── utils/                      # Test utilities
    ├── __init__.py
    ├── mock_clients.py
    ├── test_helpers.py
    └── performance_utils.py
```

## Test Configuration (`conftest.py`)

### Global Fixtures
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.navo.core.navo_engine import NAVOEngine
from src.navo.core.memory_layer import NAVOMemoryLayer
from src.navo.core.reasoning_engine import NAVOReasoningEngine

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def memory_layer():
    """Create a test memory layer with in-memory database."""
    memory = NAVOMemoryLayer(database_url="sqlite:///:memory:")
    await memory.initialize_database()
    yield memory
    await memory.cleanup()

@pytest.fixture
async def reasoning_engine():
    """Create a test reasoning engine."""
    return NAVOReasoningEngine()

@pytest.fixture
async def navo_engine(memory_layer, reasoning_engine):
    """Create a test NAVO engine with mocked dependencies."""
    engine = NAVOEngine(memory=memory_layer, reasoning=reasoning_engine)
    yield engine
    await engine.cleanup()

@pytest.fixture
def mock_enterprise_gpt():
    """Mock Enterprise GPT client."""
    mock_client = AsyncMock()
    mock_client.generate_response.return_value = {
        "content": "Test response",
        "confidence": 0.85,
        "usage": {"tokens": 100}
    }
    return mock_client
```

### Test Database Setup
```python
@pytest.fixture(scope="function")
async def test_db():
    """Create a test database for each test function."""
    import tempfile
    import os
    
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Initialize test database
    memory = NAVOMemoryLayer(database_url=f"sqlite:///{db_path}")
    await memory.initialize_database()
    
    yield memory
    
    # Cleanup
    await memory.cleanup()
    os.unlink(db_path)
```

## Unit Tests

### Core Component Tests

#### NAVO Engine Tests (`unit/core/test_navo_engine.py`)
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.navo.core.navo_engine import NAVOEngine

class TestNAVOEngine:
    @pytest.mark.asyncio
    async def test_process_query_success(self, navo_engine):
        """Test successful query processing."""
        query = "What's the API versioning standard?"
        context = {"user_id": "test_user", "team": "engineering"}
        
        result = await navo_engine.process_query(query, context)
        
        assert result is not None
        assert result.query_id is not None
        assert isinstance(result.results, list)
        assert result.reasoning is not None
        assert result.metadata is not None
    
    @pytest.mark.asyncio
    async def test_process_query_with_memory(self, navo_engine):
        """Test query processing with memory integration."""
        query = "retry logic documentation"
        context = {"user_id": "test_user"}
        
        # First query
        result1 = await navo_engine.process_query(query, context)
        
        # Simulate feedback
        await navo_engine.memory.store_feedback(
            query_id=result1.query_id,
            result_id=result1.results[0].id if result1.results else "test",
            feedback="helpful",
            rating=5
        )
        
        # Second similar query should benefit from memory
        result2 = await navo_engine.process_query(query, context)
        
        assert result2 is not None
        # Memory should influence the results
    
    @pytest.mark.asyncio
    async def test_error_handling(self, navo_engine):
        """Test error handling in query processing."""
        with patch.object(navo_engine.query_processor, 'process_query', 
                         side_effect=Exception("Test error")):
            
            result = await navo_engine.process_query("test query", {})
            
            # Should handle error gracefully
            assert result is not None
            assert result.error is not None
```

#### Memory Layer Tests (`unit/core/test_memory_layer.py`)
```python
import pytest
from src.navo.core.memory_layer import NAVOMemoryLayer

class TestNAVOMemoryLayer:
    @pytest.mark.asyncio
    async def test_store_and_retrieve_interaction(self, memory_layer):
        """Test storing and retrieving query interactions."""
        interaction_data = {
            "query_id": "test-query-1",
            "query_text": "API documentation",
            "user_id": "test_user",
            "results": [{"id": "doc1", "relevance": 0.9}],
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        # Store interaction
        await memory_layer.store_interaction(interaction_data)
        
        # Retrieve similar queries
        similar = await memory_layer.get_similar_queries("API documentation")
        
        assert len(similar) > 0
        assert similar[0]["query_text"] == "API documentation"
    
    @pytest.mark.asyncio
    async def test_feedback_learning(self, memory_layer):
        """Test feedback storage and learning."""
        # Store feedback
        await memory_layer.store_feedback(
            query_id="test-query-1",
            result_id="doc1",
            feedback="helpful",
            rating=5,
            comment="Exactly what I needed"
        )
        
        # Retrieve feedback
        feedback = await memory_layer.get_feedback("test-query-1")
        
        assert len(feedback) > 0
        assert feedback[0]["rating"] == 5
        assert feedback[0]["feedback"] == "helpful"
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self, memory_layer):
        """Test memory cleanup functionality."""
        # Store old interaction
        old_interaction = {
            "query_id": "old-query",
            "query_text": "old query",
            "user_id": "test_user",
            "timestamp": "2023-01-01T00:00:00Z"  # Old timestamp
        }
        
        await memory_layer.store_interaction(old_interaction)
        
        # Run cleanup
        cleaned_count = await memory_layer.cleanup_old_memories(max_age_days=30)
        
        assert cleaned_count > 0
```

#### Reasoning Engine Tests (`unit/core/test_reasoning_engine.py`)
```python
import pytest
from src.navo.core.reasoning_engine import NAVOReasoningEngine

class TestNAVOReasoningEngine:
    @pytest.mark.asyncio
    async def test_analyze_query(self, reasoning_engine):
        """Test query analysis with reasoning steps."""
        query = "How do I configure retry logic for synthetic scripts?"
        context = {"intent": "procedural", "domain": "testing"}
        
        result = await reasoning_engine.analyze_query(query, context)
        
        assert result is not None
        assert result.confidence > 0
        assert len(result.steps) == 5  # All reasoning steps
        assert result.execution_time_ms > 0
        
        # Check reasoning steps
        step_types = [step.type for step in result.steps]
        expected_types = ["analytical", "predictive", "diagnostic", "prescriptive", "comparative"]
        assert step_types == expected_types
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, reasoning_engine):
        """Test confidence scoring accuracy."""
        # High confidence query
        high_conf_query = "What's the API versioning standard?"
        high_result = await reasoning_engine.analyze_query(high_conf_query, {})
        
        # Low confidence query
        low_conf_query = "asdfghjkl random text"
        low_result = await reasoning_engine.analyze_query(low_conf_query, {})
        
        assert high_result.confidence > low_result.confidence
        assert high_result.confidence > 0.7
        assert low_result.confidence < 0.5
    
    @pytest.mark.asyncio
    async def test_reasoning_audit_trail(self, reasoning_engine):
        """Test reasoning audit trail generation."""
        query = "troubleshooting guide"
        result = await reasoning_engine.analyze_query(query, {})
        
        # Check audit trail
        assert result.reasoning_id is not None
        assert result.summary is not None
        assert len(result.steps) > 0
        
        # Each step should have required fields
        for step in result.steps:
            assert step.type is not None
            assert step.summary is not None
            assert step.confidence >= 0
            assert step.execution_time_ms >= 0
```

### Integration Tests

#### End-to-End Tests (`integration/test_end_to_end.py`)
```python
import pytest
from fastapi.testclient import TestClient
from src.navo.api.app import app

class TestEndToEnd:
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_complete_query_workflow(self):
        """Test complete query workflow from API to response."""
        # Submit query
        response = self.client.post(
            "/api/v1/query",
            json={
                "query": "Where's the retry logic for QLAB02 scripts?",
                "context": {
                    "user_id": "test_user",
                    "team": "engineering",
                    "project": "QLAB02"
                },
                "options": {
                    "max_results": 5,
                    "include_reasoning": True,
                    "sources": ["confluence", "sharepoint"]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "query_id" in data
        assert "results" in data
        assert "reasoning" in data
        assert "metadata" in data
        
        # Verify results
        assert isinstance(data["results"], list)
        if data["results"]:
            result = data["results"][0]
            assert "title" in result
            assert "url" in result
            assert "source" in result
            assert "relevance_score" in result
            assert "confidence" in result
        
        # Verify reasoning
        reasoning = data["reasoning"]
        assert "summary" in reasoning
        assert "confidence" in reasoning
        assert "reasoning_id" in reasoning
        assert "execution_time_ms" in reasoning
    
    def test_feedback_learning_workflow(self):
        """Test feedback and learning workflow."""
        # Submit query
        query_response = self.client.post(
            "/api/v1/query",
            json={"query": "API documentation", "context": {"user_id": "test_user"}}
        )
        
        assert query_response.status_code == 200
        query_data = query_response.json()
        query_id = query_data["query_id"]
        
        # Submit feedback
        if query_data["results"]:
            result_id = query_data["results"][0]["id"]
            feedback_response = self.client.post(
                "/api/v1/memory/feedback",
                json={
                    "query_id": query_id,
                    "result_id": result_id,
                    "feedback": "helpful",
                    "rating": 5,
                    "comment": "Exactly what I needed"
                }
            )
            
            assert feedback_response.status_code == 200
        
        # Check memory patterns
        patterns_response = self.client.get("/api/v1/memory/patterns?query=API")
        assert patterns_response.status_code == 200
        
        patterns_data = patterns_response.json()
        assert "patterns" in patterns_data
```

## Performance Tests

### Load Performance Tests (`performance/test_load_performance.py`)
```python
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from src.navo.api.app import app

class TestLoadPerformance:
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_concurrent_queries(self):
        """Test system performance under concurrent load."""
        def submit_query(query_id):
            response = self.client.post(
                "/api/v1/query",
                json={
                    "query": f"test query {query_id}",
                    "context": {"user_id": f"user_{query_id}"}
                }
            )
            return response.status_code, response.elapsed.total_seconds()
        
        # Submit 50 concurrent queries
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_query, i) for i in range(50)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = sum(1 for status, _ in results if status == 200)
        response_times = [duration for _, duration in results]
        avg_response_time = sum(response_times) / len(response_times)
        
        # Performance assertions
        assert successful_requests >= 45  # 90% success rate
        assert avg_response_time < 1.0  # Average response time under 1 second
        assert total_time < 10.0  # Total time under 10 seconds
        
        print(f"Concurrent Load Test Results:")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Successful Requests: {successful_requests}/50")
        print(f"  Average Response Time: {avg_response_time:.3f}s")
        print(f"  Max Response Time: {max(response_times):.3f}s")
    
    @pytest.mark.asyncio
    async def test_memory_performance(self):
        """Test memory layer performance under load."""
        from src.navo.core.memory_layer import NAVOMemoryLayer
        
        memory = NAVOMemoryLayer(database_url="sqlite:///:memory:")
        await memory.initialize_database()
        
        # Store many interactions
        start_time = time.time()
        
        tasks = []
        for i in range(100):
            interaction = {
                "query_id": f"query-{i}",
                "query_text": f"test query {i}",
                "user_id": f"user-{i % 10}",  # 10 different users
                "results": [{"id": f"doc-{i}", "relevance": 0.8}],
                "timestamp": "2024-01-15T10:30:00Z"
            }
            tasks.append(memory.store_interaction(interaction))
        
        await asyncio.gather(*tasks)
        store_time = time.time() - start_time
        
        # Retrieve similar queries
        start_time = time.time()
        
        retrieval_tasks = []
        for i in range(50):
            retrieval_tasks.append(memory.get_similar_queries(f"test query {i}"))
        
        results = await asyncio.gather(*retrieval_tasks)
        retrieval_time = time.time() - start_time
        
        # Performance assertions
        assert store_time < 5.0  # Store 100 interactions in under 5 seconds
        assert retrieval_time < 2.0  # Retrieve 50 queries in under 2 seconds
        
        print(f"Memory Performance Test Results:")
        print(f"  Store Time (100 interactions): {store_time:.2f}s")
        print(f"  Retrieval Time (50 queries): {retrieval_time:.2f}s")
        print(f"  Store Rate: {100/store_time:.1f} interactions/second")
        print(f"  Retrieval Rate: {50/retrieval_time:.1f} queries/second")
        
        await memory.cleanup()
```

## Test Utilities

### Mock Clients (`utils/mock_clients.py`)
```python
from unittest.mock import AsyncMock
import json

class MockConfluenceClient:
    """Mock Confluence client for testing."""
    
    def __init__(self):
        self.search_results = [
            {
                "id": "123456",
                "title": "API Versioning Standards",
                "url": "https://confluence.example.com/pages/123456",
                "content": "API versioning guidelines and best practices...",
                "space": "ENG",
                "lastModified": "2024-01-15T10:30:00Z"
            }
        ]
    
    async def search(self, query, context=None):
        """Mock search method."""
        return self.search_results
    
    async def get_content(self, content_id):
        """Mock content retrieval."""
        return self.search_results[0] if content_id == "123456" else None

class MockSharePointClient:
    """Mock SharePoint client for testing."""
    
    def __init__(self):
        self.documents = [
            {
                "id": "doc123",
                "title": "Retry Logic Configuration",
                "url": "https://sharepoint.example.com/doc123",
                "content": "Configuration guide for retry logic...",
                "site": "engineering",
                "lastModified": "2024-01-14T15:20:00Z"
            }
        ]
    
    async def search(self, query, context=None):
        """Mock search method."""
        return self.documents
    
    async def get_document(self, document_id):
        """Mock document retrieval."""
        return self.documents[0] if document_id == "doc123" else None

class MockEnterpriseGPTClient:
    """Mock Enterprise GPT client for testing."""
    
    async def generate_response(self, prompt, context=None):
        """Mock response generation."""
        return {
            "content": "This is a mock response from Enterprise GPT.",
            "confidence": 0.85,
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70
            }
        }
    
    async def analyze_query(self, query, context=None):
        """Mock query analysis."""
        return {
            "intent": "procedural",
            "entities": ["API", "versioning"],
            "confidence": 0.9
        }
```

### Test Helpers (`utils/test_helpers.py`)
```python
import json
import tempfile
import os
from typing import Dict, Any

def create_test_config() -> Dict[str, Any]:
    """Create test configuration."""
    return {
        "core": {
            "memory": {
                "database_url": "sqlite:///:memory:",
                "cleanup_interval": 3600,
                "max_memory_age": 2592000
            },
            "reasoning": {
                "confidence_threshold": 0.7,
                "max_reasoning_steps": 5,
                "enable_audit_trail": True
            },
            "cache": {
                "redis_url": "redis://localhost:6379",
                "default_ttl": 3600,
                "max_cache_size": "1GB"
            }
        },
        "integrations": {
            "enterprise_gpt": {
                "api_key": "test-key",
                "model": "gpt-4o",
                "max_tokens": 4000
            }
        }
    }

def create_temp_database():
    """Create temporary database for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    return db_path

def cleanup_temp_database(db_path: str):
    """Clean up temporary database."""
    if os.path.exists(db_path):
        os.unlink(db_path)

def assert_query_result_structure(result: Dict[str, Any]):
    """Assert that query result has correct structure."""
    required_fields = ["query_id", "results", "reasoning", "metadata"]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    # Check results structure
    if result["results"]:
        result_item = result["results"][0]
        result_fields = ["id", "title", "url", "source", "relevance_score", "confidence"]
        for field in result_fields:
            assert field in result_item, f"Missing result field: {field}"
    
    # Check reasoning structure
    reasoning = result["reasoning"]
    reasoning_fields = ["summary", "confidence", "reasoning_id", "execution_time_ms"]
    for field in reasoning_fields:
        assert field in reasoning, f"Missing reasoning field: {field}"
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only
pytest tests/performance/ -v             # Performance tests only

# Run with coverage
pytest tests/ --cov=src/navo --cov-report=html

# Run specific test file
pytest tests/unit/core/test_navo_engine.py -v

# Run specific test method
pytest tests/unit/core/test_navo_engine.py::TestNAVOEngine::test_process_query_success -v
```

### Test Configuration
```bash
# Run tests with different configurations
pytest tests/ -v --env=test              # Test environment
pytest tests/ -v --integration           # Include integration tests
pytest tests/ -v --performance           # Include performance tests
pytest tests/ -v --slow                  # Include slow tests

# Parallel test execution
pytest tests/ -v -n auto                 # Auto-detect CPU cores
pytest tests/ -v -n 4                    # Use 4 parallel workers
```

### Continuous Integration
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src/navo --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

The test suite provides comprehensive coverage of all NAVO components, ensuring reliability, performance, and correctness through unit tests, integration tests, and performance benchmarks. The modular structure allows for targeted testing of specific components while maintaining overall system validation.

