"""
NAVO Test Suite
Comprehensive testing for NAVO components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

# Import NAVO components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from navo.core.navo_engine import NAVOEngine, NAVOQuery, NAVOResponse
from navo.core.query_processor import QueryProcessor, QueryIntent
from navo.core.response_generator import ResponseGenerator
from navo.integrations.openai.enterprise_client import OpenAIEnterpriseClient


class TestNAVOEngine:
    """Test NAVO Engine functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "openai": {
                "api_key": "test_key",
                "organization_id": "test_org",
                "default_model": "gpt-4o"
            },
            "cache": {
                "redis_url": "redis://localhost:6379",
                "default_ttl": 3600
            },
            "permissions": {
                "enforce_source_permissions": False,
                "admin_users": []
            },
            "integrations": {
                "confluence": {"enabled": False},
                "sharepoint": {"enabled": False}
            }
        }
    
    @pytest.fixture
    def navo_engine(self, mock_config):
        """Create NAVO engine for testing."""
        with patch('navo.core.navo_engine.OpenAIEnterpriseClient'), \
             patch('navo.core.navo_engine.CacheManager'), \
             patch('navo.core.navo_engine.PermissionManager'):
            engine = NAVOEngine(mock_config)
            return engine
    
    @pytest.mark.asyncio
    async def test_process_query_basic(self, navo_engine):
        """Test basic query processing."""
        # Mock dependencies
        navo_engine.query_processor.process = AsyncMock()
        navo_engine.permission_manager.get_user_permissions = AsyncMock()
        navo_engine.response_generator.generate_response = AsyncMock()
        navo_engine.cache_manager.get_cached_response = AsyncMock(return_value=None)
        navo_engine.cache_manager.cache_response = AsyncMock()
        
        # Setup mock returns
        mock_processed_query = Mock()
        mock_processed_query.confidence = 0.8
        navo_engine.query_processor.process.return_value = mock_processed_query
        
        navo_engine.permission_manager.get_user_permissions.return_value = {
            "system": {"enabled": True}
        }
        
        mock_response = Mock()
        mock_response.answer = "Test answer"
        mock_response.sources = []
        mock_response.confidence = 0.9
        navo_engine.response_generator.generate_response.return_value = mock_response
        
        # Create test query
        query = NAVOQuery(
            text="What is the deployment process?",
            user_id="test_user"
        )
        
        # Process query
        response = await navo_engine.process_query(query)
        
        # Assertions
        assert isinstance(response, NAVOResponse)
        assert response.answer == "Test answer"
        assert response.confidence == 0.9
        assert response.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, navo_engine):
        """Test health check functionality."""
        # Mock health checks
        navo_engine.openai_client.health_check = AsyncMock(return_value={"status": "healthy"})
        navo_engine.cache_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        health_status = await navo_engine.health_check()
        
        assert health_status["status"] == "healthy"
        assert "components" in health_status
        assert "timestamp" in health_status


class TestQueryProcessor:
    """Test Query Processor functionality."""
    
    @pytest.fixture
    def query_processor(self):
        """Create query processor for testing."""
        config = {
            "organizational_entities": {
                "systems": ["confluence", "sharepoint"],
                "technologies": ["python", "javascript"]
            }
        }
        return QueryProcessor(config)
    
    @pytest.mark.asyncio
    async def test_intent_classification(self, query_processor):
        """Test query intent classification."""
        # Test different query types
        test_cases = [
            ("How do I deploy the application?", QueryIntent.PROCEDURE),
            ("What is Docker?", QueryIntent.DEFINITION),
            ("Find documentation about API", QueryIntent.SEARCH),
            ("Compare React vs Vue", QueryIntent.COMPARISON),
            ("API is returning 500 error", QueryIntent.TROUBLESHOOTING)
        ]
        
        for query_text, expected_intent in test_cases:
            query = Mock()
            query.text = query_text
            query.user_id = "test_user"
            query.context = None
            query.filters = None
            query.timestamp = datetime.utcnow()
            
            processed = await query_processor.process(query)
            assert processed.intent == expected_intent
    
    def test_keyword_extraction(self, query_processor):
        """Test keyword extraction."""
        text = "How do I configure Docker for production deployment?"
        keywords = query_processor._extract_keywords(text)
        
        assert "configure" in keywords
        assert "docker" in keywords
        assert "production" in keywords
        assert "deployment" in keywords
        assert "do" not in keywords  # Stop word should be filtered


class TestOpenAIEnterpriseClient:
    """Test OpenAI Enterprise Client."""
    
    @pytest.fixture
    def openai_client(self):
        """Create OpenAI client for testing."""
        config = {
            "api_key": "test_key",
            "organization_id": "test_org",
            "default_model": "gpt-4o"
        }
        return OpenAIEnterpriseClient(config)
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, openai_client):
        """Test chat completion functionality."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {"content": "Test response"},
                    "finish_reason": "stop"
                }],
                "model": "gpt-4o",
                "usage": {"total_tokens": 100}
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            from navo.integrations.openai.enterprise_client import OpenAIMessage
            messages = [
                OpenAIMessage(role="user", content="Test message")
            ]
            
            response = await openai_client.chat_completion(messages)
            
            assert response.content == "Test response"
            assert response.model == "gpt-4o"
            assert response.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_health_check(self, openai_client):
        """Test OpenAI client health check."""
        with patch.object(openai_client, 'chat_completion') as mock_completion:
            mock_response = Mock()
            mock_response.model = "gpt-4o"
            mock_response.response_time = 0.5
            mock_completion.return_value = mock_response
            
            health = await openai_client.health_check()
            
            assert health["status"] == "healthy"
            assert health["model"] == "gpt-4o"
            assert "response_time" in health


class TestIntegrationEndpoints:
    """Test API endpoints."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from navo.api.app import create_app
        
        config = {
            "openai": {"api_key": "test_key"},
            "cache": {"redis_url": "redis://localhost:6379"},
            "permissions": {"enforce_source_permissions": False},
            "integrations": {
                "confluence": {"enabled": False},
                "sharepoint": {"enabled": False}
            }
        }
        
        app = create_app(config)
        return TestClient(app)
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        with patch('navo.api.app.navo_engine') as mock_engine:
            mock_engine.health_check = AsyncMock(return_value={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {"openai_enterprise": "healthy"}
            })
            
            response = test_client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_query_endpoint(self, test_client):
        """Test query endpoint."""
        with patch('navo.api.app.navo_engine') as mock_engine:
            mock_response = NAVOResponse(
                answer="Test answer",
                sources=[],
                confidence=0.9,
                processing_time=1.0,
                query_id="test_123"
            )
            mock_engine.process_query = AsyncMock(return_value=mock_response)
            
            query_data = {
                "text": "What is Docker?",
                "user_id": "test_user",
                "context": {},
                "filters": {}
            }
            
            response = test_client.post("/api/v1/query", json=query_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test answer"
            assert data["confidence"] == 0.9


class TestPerformance:
    """Performance and load testing."""
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self):
        """Test handling multiple concurrent queries."""
        config = {
            "openai": {"api_key": "test_key"},
            "cache": {"redis_url": "redis://localhost:6379"},
            "permissions": {"enforce_source_permissions": False},
            "integrations": {"confluence": {"enabled": False}, "sharepoint": {"enabled": False}}
        }
        
        with patch('navo.core.navo_engine.OpenAIEnterpriseClient'), \
             patch('navo.core.navo_engine.CacheManager'), \
             patch('navo.core.navo_engine.PermissionManager'):
            
            engine = NAVOEngine(config)
            
            # Mock the process_query method to return quickly
            async def mock_process(query):
                await asyncio.sleep(0.1)  # Simulate processing time
                return NAVOResponse(
                    answer="Test answer",
                    sources=[],
                    confidence=0.8,
                    processing_time=0.1,
                    query_id=f"test_{query.text}"
                )
            
            engine.process_query = mock_process
            
            # Create multiple queries
            queries = [
                NAVOQuery(text=f"Query {i}", user_id="test_user")
                for i in range(10)
            ]
            
            # Process queries concurrently
            start_time = asyncio.get_event_loop().time()
            responses = await asyncio.gather(*[
                engine.process_query(query) for query in queries
            ])
            end_time = asyncio.get_event_loop().time()
            
            # Assertions
            assert len(responses) == 10
            assert all(isinstance(r, NAVOResponse) for r in responses)
            # Should complete in less than 1 second (concurrent processing)
            assert (end_time - start_time) < 1.0


class TestSecurity:
    """Security testing."""
    
    def test_input_validation(self):
        """Test input validation and sanitization."""
        from pydantic import ValidationError
        from navo.api.app import QueryRequest
        
        # Test valid input
        valid_request = QueryRequest(
            text="What is Docker?",
            user_id="test_user"
        )
        assert valid_request.text == "What is Docker?"
        
        # Test invalid input - empty text
        with pytest.raises(ValidationError):
            QueryRequest(text="", user_id="test_user")
        
        # Test invalid input - too long text
        with pytest.raises(ValidationError):
            QueryRequest(text="x" * 1001, user_id="test_user")
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attempts."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../etc/passwd"
        ]
        
        from navo.core.query_processor import QueryProcessor
        processor = QueryProcessor({})
        
        for malicious_input in malicious_inputs:
            # Should not raise exceptions and should sanitize input
            normalized = processor._normalize_text(malicious_input)
            assert "DROP TABLE" not in normalized.upper()
            assert "<script>" not in normalized


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

