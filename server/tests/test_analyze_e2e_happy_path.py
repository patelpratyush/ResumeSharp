"""
End-to-end happy path test for /analyze endpoint.
Tests that the canonical response format is always returned correctly.
"""
import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAnalyzeE2EHappyPath:
    """End-to-end tests for analyze endpoint canonical output."""

    def test_analyze_happy_path_canonical_response(self):
        """Test that /analyze always returns canonical format with all required fields."""
        # Complete realistic request matching the OpenAPI example
        payload = {
            "resume": {
                "contact": {
                    "name": "John Smith",
                    "email": "john@email.com"
                },
                "skills": ["Python", "JavaScript", "React", "SQL"],
                "experience": [{
                    "company": "Tech Corp",
                    "role": "Software Engineer",
                    "start": "2023",
                    "end": "Present",
                    "bullets": [
                        "Built web applications using Python and React",
                        "Optimized database queries improving performance by 25%"
                    ]
                }]
            },
            "jd": {
                "title": "Senior Software Engineer",
                "required": ["Python", "JavaScript", "React", "Node.js"],
                "responsibilities": [
                    "Build scalable web applications",
                    "Optimize system performance"
                ]
            }
        }
        
        response = client.post("/api/analyze", json=payload)
        
        # Assert successful response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Assert canonical response structure - all fields must be present
        canonical_fields = ["score", "matched", "missing", "sections", "normalizedJD"]
        for field in canonical_fields:
            assert field in data, f"Missing required canonical field: {field}"
        
        # Assert field types are correct
        assert isinstance(data["score"], int), "Score must be integer"
        assert isinstance(data["matched"], list), "Matched must be list"
        assert isinstance(data["missing"], list), "Missing must be list"
        assert isinstance(data["sections"], dict), "Sections must be dict"
        assert isinstance(data["normalizedJD"], dict), "NormalizedJD must be dict"
        
        # Assert score is in valid range
        assert 0 <= data["score"] <= 100, f"Score {data['score']} must be 0-100"
        
        # Assert arrays are never null (even if empty)
        assert data["matched"] is not None, "Matched array must never be null"
        assert data["missing"] is not None, "Missing array must never be null"
        
        # Assert sections structure
        required_section_fields = ["skillsCoveragePct", "preferredCoveragePct", "domainCoveragePct"]
        for field in required_section_fields:
            assert field in data["sections"], f"Missing sections field: {field}"
            assert isinstance(data["sections"][field], int), f"Section {field} must be int"
            assert 0 <= data["sections"][field] <= 100, f"Section {field} must be percentage"
        
        # Assert normalizedJD structure
        assert "skills" in data["normalizedJD"], "NormalizedJD missing skills"
        assert "responsibilities" in data["normalizedJD"], "NormalizedJD missing responsibilities"
        assert isinstance(data["normalizedJD"]["skills"], list), "NormalizedJD skills must be list"
        assert isinstance(data["normalizedJD"]["responsibilities"], list), "NormalizedJD responsibilities must be list"
        
        # Assert normalizedJD arrays are never null
        assert data["normalizedJD"]["skills"] is not None, "NormalizedJD skills must never be null"
        assert data["normalizedJD"]["responsibilities"] is not None, "NormalizedJD responsibilities must never be null"

    def test_analyze_realistic_scoring_behavior(self):
        """Test that scoring behaves reasonably with realistic data."""
        # Perfect match scenario
        perfect_payload = {
            "resume": {
                "skills": ["Python", "JavaScript", "React", "Node.js", "SQL"],
                "experience": [{
                    "company": "Tech Corp",
                    "role": "Senior Software Engineer",
                    "start": "2024",
                    "end": "Present",
                    "bullets": [
                        "Built scalable web applications using Python and React",
                        "Implemented Node.js backend services with SQL databases",
                        "Optimized performance and deployed to production"
                    ]
                }]
            },
            "jd": {
                "title": "Senior Software Engineer",
                "required": ["Python", "JavaScript", "React", "Node.js"],
                "responsibilities": [
                    "Build scalable web applications",
                    "Optimize system performance"
                ]
            }
        }
        
        response = client.post("/api/analyze", json=perfect_payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Perfect match should score highly
        assert data["score"] >= 70, f"Perfect match should score highly, got {data['score']}"
        
        # Should have good matches
        assert len(data["matched"]) >= 3, "Perfect match should have multiple matched skills"
        
        # Should have minimal missing items for perfect match
        assert len(data["missing"]) <= 2, "Perfect match should have few missing items"
        
        # Skills coverage should be high
        assert data["sections"]["skillsCoveragePct"] >= 70, "Skills coverage should be high for perfect match"

    def test_analyze_partial_match_scoring(self):
        """Test scoring with partial skill matches."""
        partial_payload = {
            "resume": {
                "skills": ["Python", "Java", "C++"],  # Only Python matches
                "experience": [{
                    "company": "Different Corp",
                    "role": "Backend Developer",
                    "start": "2022",
                    "bullets": ["Built backend services with Java and Python"]
                }]
            },
            "jd": {
                "required": ["Python", "JavaScript", "React", "Node.js"],
                "responsibilities": ["Build web applications"]
            }
        }
        
        response = client.post("/api/analyze", json=partial_payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Partial match should score moderately
        assert 10 <= data["score"] <= 60, f"Partial match should score moderately, got {data['score']}"
        
        # Should have at least Python matched
        assert "Python" in [m.lower() for m in data["matched"]] or any("python" in m.lower() for m in data["matched"]), "Python should be matched"
        
        # Should have missing JavaScript/React/Node.js
        missing_lower = [m.lower() for m in data["missing"]]
        assert any("javascript" in m for m in missing_lower) or any("react" in m for m in missing_lower), "Should have missing frontend skills"

    def test_analyze_no_match_scoring(self):
        """Test scoring with no skill matches."""
        no_match_payload = {
            "resume": {
                "skills": ["Java", "C#", "PHP"],  # No matches
                "experience": [{
                    "company": "Different Corp",
                    "role": "Backend Developer",
                    "start": "2020",
                    "bullets": ["Built enterprise applications with Java and C#"]
                }]
            },
            "jd": {
                "required": ["Python", "JavaScript", "React"],
                "responsibilities": ["Build web applications"]
            }
        }
        
        response = client.post("/api/analyze", json=no_match_payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # No match should score low but not zero (due to minimum scoring)
        assert 0 <= data["score"] <= 30, f"No match should score low, got {data['score']}"
        
        # Should have few or no matches
        assert len(data["matched"]) <= 1, "No match scenario should have minimal matches"
        
        # Should have most requirements missing
        assert len(data["missing"]) >= 2, "No match should have multiple missing requirements"

    def test_analyze_response_deterministic(self):
        """Test that identical requests produce identical responses."""
        payload = {
            "resume": {
                "skills": ["Python", "JavaScript"],
                "experience": [{
                    "company": "Test Corp",
                    "role": "Developer",
                    "start": "2023",
                    "bullets": ["Built applications"]
                }]
            },
            "jd": {
                "required": ["Python", "React"],
                "responsibilities": ["Build apps"]
            }
        }
        
        # Make multiple identical requests
        responses = []
        for _ in range(3):
            response = client.post("/api/analyze", json=payload)
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should be identical
        first_response = responses[0]
        for i, response in enumerate(responses[1:], 1):
            assert response["score"] == first_response["score"], f"Score differs in call {i}"
            assert set(response["matched"]) == set(first_response["matched"]), f"Matched differs in call {i}"
            assert set(response["missing"]) == set(first_response["missing"]), f"Missing differs in call {i}"
            assert response["sections"] == first_response["sections"], f"Sections differ in call {i}"

    def test_analyze_canonical_format_edge_cases(self):
        """Test canonical format is maintained even in edge cases."""
        edge_cases = [
            # Empty resume
            {
                "resume": {},
                "jd": {"required": ["Python"]}
            },
            
            # Empty JD
            {
                "resume": {"skills": ["Python"]},
                "jd": {}
            },
            
            # Minimal data
            {
                "resume": {"skills": ["Python"]},
                "jd": {"required": ["JavaScript"]}
            }
        ]
        
        for i, payload in enumerate(edge_cases):
            response = client.post("/api/analyze", json=payload)
            assert response.status_code == 200, f"Edge case {i} should succeed"
            
            data = response.json()
            
            # Even edge cases must return canonical format
            canonical_fields = ["score", "matched", "missing", "sections", "normalizedJD"]
            for field in canonical_fields:
                assert field in data, f"Edge case {i} missing canonical field: {field}"
            
            # Arrays must never be null
            assert data["matched"] is not None, f"Edge case {i}: matched is null"
            assert data["missing"] is not None, f"Edge case {i}: missing is null"
            assert data["normalizedJD"]["skills"] is not None, f"Edge case {i}: normalizedJD.skills is null"
            assert data["normalizedJD"]["responsibilities"] is not None, f"Edge case {i}: normalizedJD.responsibilities is null"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])