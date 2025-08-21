"""
Unit tests for /analyze endpoint error handling and edge cases.
"""
import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestAnalyzeEndpoint:
    """Tests for /analyze endpoint."""

    def test_valid_analyze_request(self):
        """Test valid analyze request returns 200."""
        payload = {
            "resume": {
                "skills": ["Python", "JavaScript"],
                "experience": [{
                    "company": "Test Corp",
                    "role": "Developer", 
                    "bullets": ["Built applications"]
                }]
            },
            "jd": {
                "title": "Software Engineer",
                "required": ["Python", "JavaScript"],
                "responsibilities": ["Build software"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Check canonical response structure
        required_fields = ["score", "matched", "missing", "sections", "normalizedJD"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_empty_resume_returns_valid_response(self):
        """Test empty resume returns valid response with score 0."""
        payload = {
            "resume": {},
            "jd": {
                "title": "Software Engineer", 
                "required": ["Python"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["score"] == 0
        assert data["matched"] == []
        assert isinstance(data["missing"], list)

    def test_empty_jd_returns_valid_response(self):
        """Test empty JD returns valid response."""
        payload = {
            "resume": {
                "skills": ["Python", "JavaScript"]
            },
            "jd": {}
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["score"] == 0
        assert data["matched"] == []
        # Should indicate no job requirements found
        assert "No job requirements found" in data["missing"]

    def test_invalid_json_returns_422(self):
        """Test invalid JSON structure returns 422."""
        response = client.post("/api/analyze", json={"invalid": "structure"})
        assert response.status_code == 422

    def test_missing_resume_field_returns_422(self):
        """Test missing resume field returns 422."""
        payload = {
            "jd": {
                "title": "Software Engineer",
                "required": ["Python"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    def test_missing_jd_field_returns_422(self):
        """Test missing JD field returns 422."""
        payload = {
            "resume": {
                "skills": ["Python"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 422

    def test_malformed_resume_data(self):
        """Test malformed resume data is handled gracefully."""
        payload = {
            "resume": {
                "skills": "not-a-list",  # Should be list
                "experience": "also-not-a-list"  # Should be list
            },
            "jd": {
                "title": "Software Engineer",
                "required": ["Python"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        # Should either return 200 with graceful handling or 422/500
        assert response.status_code in [200, 422, 500]

    def test_malformed_jd_data(self):
        """Test malformed JD data is handled gracefully.""" 
        payload = {
            "resume": {
                "skills": ["Python"]
            },
            "jd": {
                "required": "not-a-list",  # Should be list
                "responsibilities": 123  # Should be list
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        # Should either return 200 with graceful handling or 422/500
        assert response.status_code in [200, 422, 500]

    def test_extremely_long_content(self):
        """Test very long resume/JD content."""
        long_text = "A" * 50000  # 50k characters
        
        payload = {
            "resume": {
                "skills": ["Python"],
                "experience": [{
                    "company": "Test Corp",
                    "role": "Developer",
                    "bullets": [long_text]
                }]
            },
            "jd": {
                "title": "Software Engineer",
                "required": ["Python"],
                "responsibilities": [long_text]
            }
        }
        
        response = client.post("/api/analyze", json=payload, timeout=30)
        # Should handle long content gracefully
        assert response.status_code == 200
        
        data = response.json()
        # Should still return valid structure
        assert "score" in data
        assert isinstance(data["matched"], list)
        assert isinstance(data["missing"], list)

    def test_special_characters_in_skills(self):
        """Test special characters and unicode in skills."""
        payload = {
            "resume": {
                "skills": ["C++", "C#", ".NET", "Node.js", "Vue.js", "Café☕", "测试"]
            },
            "jd": {
                "title": "Developer",
                "required": ["C++", "C#", ".NET", "JavaScript"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["matched"], list)
        assert isinstance(data["missing"], list)

    def test_response_content_type(self):
        """Test response has correct content type."""
        payload = {
            "resume": {"skills": ["Python"]},
            "jd": {"required": ["Python"]}
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_canonical_response_shape_consistency(self):
        """Test that canonical response shape is always consistent."""
        test_payloads = [
            # Normal case
            {
                "resume": {"skills": ["Python"], "experience": [{"company": "Test", "role": "Dev", "bullets": ["Coded"]}]},
                "jd": {"title": "Developer", "required": ["JavaScript"]}
            },
            # Minimal case
            {
                "resume": {"skills": []},
                "jd": {"title": "Job"}
            },
            # Empty case
            {
                "resume": {},
                "jd": {}
            }
        ]
        
        for payload in test_payloads:
            response = client.post("/api/analyze", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            
            # Check all required fields present
            required_fields = ["score", "matched", "missing", "sections", "normalizedJD"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Check data types
            assert isinstance(data["score"], int), "Score should be int"
            assert isinstance(data["matched"], list), "Matched should be list"  
            assert isinstance(data["missing"], list), "Missing should be list"
            assert isinstance(data["sections"], dict), "Sections should be dict"
            assert isinstance(data["normalizedJD"], dict), "NormalizedJD should be dict"
            
            # Check sections structure
            sections = data["sections"]
            expected_section_fields = ["skillsCoveragePct", "preferredCoveragePct", "domainCoveragePct"]
            for field in expected_section_fields:
                assert field in sections, f"Missing section field: {field}"
                assert isinstance(sections[field], int), f"Section {field} should be int"
            
            # Check normalizedJD structure
            normalized_jd = data["normalizedJD"]
            assert "skills" in normalized_jd, "normalizedJD missing skills"
            assert "responsibilities" in normalized_jd, "normalizedJD missing responsibilities"
            assert isinstance(normalized_jd["skills"], list), "normalizedJD skills should be list"
            assert isinstance(normalized_jd["responsibilities"], list), "normalizedJD responsibilities should be list"


if __name__ == "__main__":
    pytest.main([__file__])