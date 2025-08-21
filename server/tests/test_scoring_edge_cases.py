"""
Unit tests for scoring edge cases and analyze function.
"""
import pytest
import sys
import os

# Add the app directory to Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.analyze import analyze


class TestScoringEdgeCases:
    """Tests for scoring edge cases."""

    def test_empty_resume(self):
        """Test scoring with completely empty resume."""
        resume = {}
        jd = {
            "title": "Software Engineer",
            "required": ["Python", "JavaScript"],
            "responsibilities": ["Build APIs"]
        }
        
        result = analyze(resume, jd)
        
        # Should return valid response with low score
        assert "score" in result
        assert "matched" in result
        assert "missing" in result
        assert result["score"] >= 0
        assert isinstance(result["matched"], list)
        assert isinstance(result["missing"], list)
        # With empty resume, should have no matches
        assert len(result["matched"]) == 0

    def test_resume_no_skills_or_experience(self):
        """Test resume with no skills or experience sections."""
        resume = {
            "contact": {"name": "John Doe", "email": "john@example.com"},
            "summary": "A great developer"
        }
        jd = {
            "title": "Software Engineer",
            "required": ["Python", "JavaScript"],
        }
        
        result = analyze(resume, jd)
        
        assert result["score"] >= 0
        assert isinstance(result["matched"], list)
        assert isinstance(result["missing"], list)
        # Should still return skills as missing
        assert len(result["missing"]) > 0

    def test_empty_jd(self):
        """Test with empty job description."""
        resume = {
            "skills": ["Python", "JavaScript", "React"],
            "experience": [{"company": "Test", "role": "Developer", "bullets": ["Built apps"]}]
        }
        jd = {}
        
        result = analyze(resume, jd)
        
        # Should handle gracefully
        assert result["score"] >= 0
        assert isinstance(result["matched"], list)
        assert isinstance(result["missing"], list)

    def test_no_matches_between_resume_and_jd(self):
        """Test case where resume and JD have no overlapping skills."""
        resume = {
            "skills": ["Python", "Django", "PostgreSQL"],
            "experience": [{"company": "Test", "role": "Backend Developer", "bullets": ["Built APIs with Django"]}]
        }
        jd = {
            "title": "Frontend Developer",
            "required": ["JavaScript", "React", "CSS"],
            "responsibilities": ["Build user interfaces"]
        }
        
        result = analyze(resume, jd)
        
        # Should have low score but valid structure
        assert result["score"] >= 0
        assert result["score"] < 30  # Should be low score
        assert isinstance(result["matched"], list)
        assert isinstance(result["missing"], list)
        assert len(result["missing"]) > 0  # Should show missing skills

    def test_perfect_matches(self):
        """Test case where resume perfectly matches JD requirements."""
        resume = {
            "skills": ["Python", "JavaScript", "React", "FastAPI", "Docker"],
            "experience": [{
                "company": "Test Corp", 
                "role": "Full Stack Developer",
                "bullets": [
                    "Built REST APIs using Python and FastAPI",
                    "Developed frontend applications with React and JavaScript", 
                    "Deployed applications using Docker containers"
                ]
            }]
        }
        jd = {
            "title": "Full Stack Developer",
            "required": ["Python", "JavaScript", "React"],
            "preferred": ["FastAPI", "Docker"],
            "responsibilities": ["Build APIs", "Develop frontend applications"]
        }
        
        result = analyze(resume, jd)
        
        # Should have high score
        assert result["score"] > 50  # Should be reasonably high
        assert isinstance(result["matched"], list)
        assert isinstance(result["missing"], list)
        assert len(result["matched"]) > 0  # Should have matches
        # Check that key skills are matched
        matched_lower = [skill.lower() for skill in result["matched"]]
        assert "python" in matched_lower
        assert "javascript" in matched_lower
        assert "react" in matched_lower

    def test_partial_matches_with_aliases(self):
        """Test partial matches including skill aliases."""
        resume = {
            "skills": ["JS", "React.js", "Node.js"],
            "experience": [{"company": "Test", "role": "Developer", "bullets": ["Built apps with JS"]}]
        }
        jd = {
            "title": "JavaScript Developer", 
            "required": ["JavaScript", "React", "NodeJS"],
        }
        
        result = analyze(resume, jd)
        
        # Should recognize aliases and have matches
        assert result["score"] > 20  # Should have some score due to aliases
        assert len(result["matched"]) > 0
        # Should match aliases: JS->JavaScript, React.js->React, Node.js->NodeJS
        matched_lower = [skill.lower() for skill in result["matched"]]
        assert "javascript" in matched_lower or "js" in matched_lower

    def test_response_structure_consistency(self):
        """Test that response structure is always consistent."""
        test_cases = [
            # Empty resume
            ({}, {"required": ["Python"]}),
            # Empty JD  
            ({"skills": ["Python"]}, {}),
            # Normal case
            ({"skills": ["Python"]}, {"required": ["JavaScript"]}),
            # Both empty
            ({}, {}),
        ]
        
        for resume, jd in test_cases:
            result = analyze(resume, jd)
            
            # Check required fields always present
            required_fields = ["score", "matched", "missing", "sections", "normalizedJD"]
            for field in required_fields:
                assert field in result, f"Missing field {field} in result"
            
            # Check data types
            assert isinstance(result["score"], int), "Score should be integer"
            assert isinstance(result["matched"], list), "Matched should be list"
            assert isinstance(result["missing"], list), "Missing should be list"
            assert isinstance(result["sections"], dict), "Sections should be dict"
            assert isinstance(result["normalizedJD"], dict), "NormalizedJD should be dict"
            
            # Check score range
            assert 0 <= result["score"] <= 100, f"Score {result['score']} out of range"
            
            # Check normalizedJD structure
            normalized_jd = result["normalizedJD"]
            assert "skills" in normalized_jd, "normalizedJD missing skills"
            assert "responsibilities" in normalized_jd, "normalizedJD missing responsibilities"
            assert isinstance(normalized_jd["skills"], list), "normalizedJD skills should be list"
            assert isinstance(normalized_jd["responsibilities"], list), "normalizedJD responsibilities should be list"


if __name__ == "__main__":
    pytest.main([__file__])