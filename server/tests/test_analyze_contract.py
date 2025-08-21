"""
Contract tests for /analyze endpoint.
Tests API contract, edge cases, and response consistency.
"""
import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAnalyzeContract:
    """Contract tests for /analyze endpoint."""

    def test_analyze_endpoint_exists(self):
        """Test that /analyze endpoint exists and accepts POST."""
        # Invalid request should return 422, not 404
        response = client.post("/api/analyze", json={})
        assert response.status_code != 404, "Endpoint should exist"

    def test_analyze_valid_request_structure(self):
        """Test valid request returns correct response structure."""
        payload = {
            "resume": {
                "skills": ["Python", "JavaScript"],
                "experience": [{
                    "company": "Tech Corp",
                    "role": "Developer",
                    "bullets": ["Built applications"],
                    "start": "2023",
                    "end": "Present"
                }]
            },
            "jd": {
                "title": "Software Engineer",
                "required": ["Python", "JavaScript", "React"],
                "responsibilities": ["Build software"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields exist
        required_fields = ["score", "matched", "missing", "sections", "normalizedJD"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check data types
        assert isinstance(data["score"], int), "Score should be int"
        assert isinstance(data["matched"], list), "Matched should be list"
        assert isinstance(data["missing"], list), "Missing should be list"
        assert isinstance(data["sections"], dict), "Sections should be dict"
        assert isinstance(data["normalizedJD"], dict), "NormalizedJD should be dict"

    def test_analyze_score_range_constraint(self):
        """Test that score is always in 0-100 range."""
        test_cases = [
            # Perfect match case
            {
                "resume": {
                    "skills": ["Python", "JavaScript", "React"],
                    "experience": [{
                        "company": "Tech Corp",
                        "role": "Developer",
                        "start": "2023",
                        "end": "Present",
                        "bullets": ["Built Python applications with React"]
                    }]
                },
                "jd": {"required": ["Python", "JavaScript", "React"]}
            },
            # No match case
            {
                "resume": {
                    "skills": ["Java", "C++"],
                    "experience": [{
                        "company": "Corp",
                        "role": "Developer", 
                        "start": "2022",
                        "bullets": ["Built Java apps"]
                    }]
                },
                "jd": {"required": ["Python", "JavaScript"]}
            },
            # Partial match case
            {
                "resume": {
                    "skills": ["Python"],
                    "experience": [{
                        "company": "Company",
                        "role": "Dev",
                        "start": "2023",
                        "bullets": ["Used Python"]
                    }]
                },
                "jd": {"required": ["Python", "JavaScript", "React", "Node.js"]}
            }
        ]
        
        for i, payload in enumerate(test_cases):
            response = client.post("/api/analyze", json=payload)
            assert response.status_code == 200, f"Test case {i} failed"
            
            data = response.json()
            score = data["score"]
            assert 0 <= score <= 100, f"Score {score} out of range for test case {i}"

    def test_analyze_arrays_never_null(self):
        """Test that matched and missing arrays are never null."""
        test_cases = [
            # Empty resume
            {"resume": {}, "jd": {"required": ["Python"]}},
            
            # Empty JD
            {"resume": {"skills": ["Python"]}, "jd": {}},
            
            # Both with content
            {
                "resume": {"skills": ["Python"]},
                "jd": {"required": ["JavaScript"]}
            }
        ]
        
        for payload in test_cases:
            response = client.post("/api/analyze", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["matched"] is not None, "Matched array should not be null"
            assert data["missing"] is not None, "Missing array should not be null"
            assert isinstance(data["matched"], list), "Matched should be list"
            assert isinstance(data["missing"], list), "Missing should be list"

    def test_analyze_sections_structure(self):
        """Test sections object has correct structure."""
        payload = {
            "resume": {"skills": ["Python", "JavaScript"]},
            "jd": {"required": ["Python", "React"], "preferred": ["JavaScript"]}
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        sections = data["sections"]
        
        # Check required section fields
        required_section_fields = ["skillsCoveragePct", "preferredCoveragePct", "domainCoveragePct"]
        for field in required_section_fields:
            assert field in sections, f"Missing section field: {field}"
            assert isinstance(sections[field], int), f"Section {field} should be int"
            assert 0 <= sections[field] <= 100, f"Section {field} should be percentage"

    def test_analyze_normalized_jd_structure(self):
        """Test normalizedJD object has correct structure."""
        payload = {
            "resume": {"skills": ["Python"]},
            "jd": {
                "required": ["Python", "JavaScript"],
                "responsibilities": ["Build apps", "Write code"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        normalized_jd = data["normalizedJD"]
        
        # Check required fields
        assert "skills" in normalized_jd, "NormalizedJD missing skills"
        assert "responsibilities" in normalized_jd, "NormalizedJD missing responsibilities"
        
        # Check types
        assert isinstance(normalized_jd["skills"], list), "Skills should be list"
        assert isinstance(normalized_jd["responsibilities"], list), "Responsibilities should be list"

    def test_analyze_empty_resume_edge_case(self):
        """Test analysis handles completely empty resume."""
        payload = {
            "resume": {},
            "jd": {
                "title": "Software Engineer",
                "required": ["Python", "JavaScript"],
                "responsibilities": ["Build software"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["score"] == 0, "Empty resume should score 0"
        assert data["matched"] == [], "Empty resume should have no matches"
        assert isinstance(data["missing"], list), "Missing should be list"

    def test_analyze_empty_jd_edge_case(self):
        """Test analysis handles completely empty job description."""
        payload = {
            "resume": {
                "skills": ["Python", "JavaScript"],
                "experience": [{
                    "company": "Tech Corp",
                    "role": "Developer",
                    "start": "2023",
                    "bullets": ["Built apps"]
                }]
            },
            "jd": {}
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["score"] == 0, "Empty JD should score 0"
        assert data["matched"] == [], "Empty JD should have no matches"

    def test_analyze_prose_only_jd_edge_case(self):
        """Test analysis handles JD with only prose (no extractable requirements)."""
        payload = {
            "resume": {"skills": ["Python", "JavaScript"]},
            "jd": {
                "title": "Great Job",
                "company": "Amazing Corp",
                # No requirements, responsibilities, or skills - just metadata
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["score"] <= 5, "Prose-only JD should score very low"
        assert data["matched"] == [], "Prose-only JD should have no matches"
        # Missing should explain the issue
        missing_text = " ".join(data["missing"]).lower()
        assert "extract" in missing_text or "requirements" in missing_text

    def test_analyze_malformed_resume_graceful_handling(self):
        """Test analysis handles malformed resume data gracefully."""
        malformed_payloads = [
            # Skills as string instead of list
            {
                "resume": {"skills": "Python, JavaScript"},
                "jd": {"required": ["Python"]}
            },
            
            # Experience as string instead of list
            {
                "resume": {"experience": "Worked at company"},
                "jd": {"required": ["Python"]}
            },
            
            # Nested objects with wrong types
            {
                "resume": {
                    "experience": [{
                        "bullets": "Single bullet string",  # Should be list
                        "company": 123  # Should be string
                    }]
                },
                "jd": {"required": ["Python"]}
            }
        ]
        
        for i, payload in enumerate(malformed_payloads):
            response = client.post("/api/analyze", json=payload)
            # Should either handle gracefully (200) or return proper error (422)
            assert response.status_code in [200, 422], f"Malformed case {i} should handle gracefully"
            
            if response.status_code == 200:
                data = response.json()
                # If handled gracefully, should still return valid structure
                assert "score" in data
                assert isinstance(data["matched"], list)
                assert isinstance(data["missing"], list)

    def test_analyze_malformed_jd_graceful_handling(self):
        """Test analysis handles malformed JD data gracefully."""
        malformed_payloads = [
            # Required as string instead of list
            {
                "resume": {"skills": ["Python"]},
                "jd": {"required": "Python, JavaScript"}
            },
            
            # Responsibilities as number
            {
                "resume": {"skills": ["Python"]},
                "jd": {"responsibilities": 123}
            },
            
            # Mixed types in arrays
            {
                "resume": {"skills": ["Python"]},
                "jd": {"required": ["Python", 123, {"invalid": "object"}]}
            }
        ]
        
        for i, payload in enumerate(malformed_payloads):
            response = client.post("/api/analyze", json=payload)
            assert response.status_code in [200, 422], f"Malformed JD case {i} should handle gracefully"

    def test_analyze_large_content_handling(self):
        """Test analysis handles large content appropriately."""
        # Create large but reasonable content
        large_skills = [f"Skill{i}" for i in range(100)]
        large_bullets = [f"Built application {i} with various technologies" for i in range(50)]
        
        payload = {
            "resume": {
                "skills": large_skills,
                "experience": [{
                    "company": "Big Corp",
                    "role": "Developer",
                    "start": "2023",
                    "bullets": large_bullets
                }]
            },
            "jd": {
                "required": large_skills[:50],
                "responsibilities": [f"Responsibility {i}" for i in range(30)]
            }
        }
        
        response = client.post("/api/analyze", json=payload, timeout=30)
        assert response.status_code == 200, "Should handle large content"
        
        data = response.json()
        assert "score" in data
        assert isinstance(data["matched"], list)
        assert isinstance(data["missing"], list)

    def test_analyze_unicode_content_handling(self):
        """Test analysis handles unicode content properly."""
        payload = {
            "resume": {
                "skills": ["Python", "JavaScript", "Развитие", "编程"],
                "experience": [{
                    "company": "Международная компания",
                    "role": "Разработчик софтвера",
                    "start": "2023",
                    "bullets": ["Построил веб-приложения", "Создал系统架构"]
                }]
            },
            "jd": {
                "title": "Инженер программного обеспечения",
                "required": ["Python", "JavaScript", "软件开发"],
                "responsibilities": ["Создавать приложения", "維護系統"]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200, "Should handle unicode content"
        
        data = response.json()
        assert isinstance(data["score"], int)
        assert isinstance(data["matched"], list)
        assert isinstance(data["missing"], list)

    def test_analyze_response_consistency_across_calls(self):
        """Test that identical requests return identical responses."""
        payload = {
            "resume": {
                "skills": ["Python", "JavaScript"],
                "experience": [{
                    "company": "Tech Corp",
                    "role": "Developer",
                    "start": "2023",
                    "end": "Present",
                    "bullets": ["Built web applications"]
                }]
            },
            "jd": {
                "required": ["Python", "JavaScript", "React"],
                "responsibilities": ["Build applications"]
            }
        }
        
        # Make multiple identical requests
        responses = []
        for _ in range(3):
            response = client.post("/api/analyze", json=payload)
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should be identical (deterministic)
        first_response = responses[0]
        for i, response in enumerate(responses[1:], 1):
            assert response["score"] == first_response["score"], f"Score differs in call {i}"
            assert set(response["matched"]) == set(first_response["matched"]), f"Matched differs in call {i}"
            assert set(response["missing"]) == set(first_response["missing"]), f"Missing differs in call {i}"

    def test_analyze_request_validation(self):
        """Test request validation returns proper errors."""
        invalid_requests = [
            # Missing resume
            {"jd": {"required": ["Python"]}},
            
            # Missing JD
            {"resume": {"skills": ["Python"]}},
            
            # Both missing
            {},
            
            # Wrong field names
            {"resumeData": {"skills": ["Python"]}, "jobDescription": {"required": ["Python"]}}
        ]
        
        for i, payload in enumerate(invalid_requests):
            response = client.post("/api/analyze", json=payload)
            assert response.status_code == 422, f"Invalid request {i} should return 422"
            
            # Should return error in standard format
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                assert "detail" in error_data, f"Error response {i} should have detail"

    def test_analyze_content_type_validation(self):
        """Test that endpoint requires JSON content type."""
        # Valid JSON data but wrong content type
        response = client.post(
            "/api/analyze",
            data="invalid text data",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422, "Should reject non-JSON content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])