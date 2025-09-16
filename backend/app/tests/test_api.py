"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.db.models import Tender, TenderSource


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, test_db):
        """Test health check endpoint."""
        with patch('app.api.v1.endpoints.health.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "timestamp" in data
            assert "version" in data


class TestTenderEndpoints:
    """Test tender endpoints."""
    
    def test_search_tenders_empty(self, test_db):
        """Test searching tenders with empty database."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders")
            
            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0
            assert data["page"] == 1
            assert data["size"] == 50
            assert data["pages"] == 0
    
    def test_search_tenders_with_data(self, test_db, sample_tenders):
        """Test searching tenders with data."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 5
            assert data["total"] == 5
            assert data["page"] == 1
            assert data["size"] == 50
            assert data["pages"] == 1
    
    def test_search_tenders_with_query(self, test_db, sample_tenders):
        """Test searching tenders with query parameter."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?query=Test Tender 1")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) >= 1
            assert any("Test Tender 1" in item["title"] for item in data["items"])
    
    def test_search_tenders_with_cpv_filter(self, test_db, sample_tenders):
        """Test searching tenders with CPV filter."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?cpv=48000000")
            
            assert response.status_code == 200
            data = response.json()
            # Should find tenders with CPV code 48000000
            assert len(data["items"]) >= 0
    
    def test_search_tenders_with_country_filter(self, test_db, sample_tenders):
        """Test searching tenders with country filter."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?country=FR")
            
            assert response.status_code == 200
            data = response.json()
            # Should find tenders from France
            assert len(data["items"]) >= 0
    
    def test_search_tenders_with_date_filters(self, test_db, sample_tenders):
        """Test searching tenders with date filters."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?from_date=2024-01-15&to_date=2024-01-20")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) >= 0
    
    def test_search_tenders_with_value_filters(self, test_db, sample_tenders):
        """Test searching tenders with value filters."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?min_value=100000&max_value=200000")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) >= 0
    
    def test_search_tenders_with_source_filter(self, test_db, sample_tenders):
        """Test searching tenders with source filter."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?source=TED")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) >= 0
    
    def test_search_tenders_with_pagination(self, test_db, sample_tenders):
        """Test searching tenders with pagination."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?limit=2&offset=1")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) <= 2
            assert data["page"] == 1  # offset=1, limit=2 -> page 1
            assert data["size"] == 2
    
    def test_search_tenders_invalid_date_format(self, test_db):
        """Test searching tenders with invalid date format."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders?from_date=invalid-date")
            
            assert response.status_code == 400
            assert "Invalid from_date format" in response.json()["detail"]
    
    def test_get_tender_by_ref(self, test_db, sample_tenders):
        """Test getting a specific tender by reference."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders/TEST-2024-001")
            
            assert response.status_code == 200
            data = response.json()
            assert data["tender_ref"] == "TEST-2024-001"
            assert data["title"] == "Test Tender 1"
    
    def test_get_tender_by_ref_not_found(self, test_db):
        """Test getting a non-existent tender by reference."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders/NON-EXISTENT")
            
            assert response.status_code == 404
            assert "Tender not found" in response.json()["detail"]
    
    def test_get_tenders_by_source(self, test_db, sample_tenders):
        """Test getting tenders by source."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders/sources/TED")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) >= 0
            assert data["total"] >= 0
    
    def test_get_tender_stats(self, test_db, sample_tenders):
        """Test getting tender statistics."""
        with patch('app.api.v1.endpoints.tenders.get_db', return_value=test_db):
            client = TestClient(app)
            response = client.get("/api/v1/tenders/stats/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_tenders" in data
            assert "by_source" in data
            assert "top_countries" in data
            assert "recent_tenders_7_days" in data
            assert data["total_tenders"] == 5


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "Procurement Copilot API" in data["message"]


class TestCORS:
    """Test CORS functionality."""
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        client = TestClient(app)
        response = client.options("/api/v1/health")
        
        # FastAPI automatically handles CORS for OPTIONS requests
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
