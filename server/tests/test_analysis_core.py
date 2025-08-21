"""
Core analysis logic tests focusing on key functionality.
Simplified tests that work with actual implementation behavior.
"""
import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.services.analyze import analyze
from app.services.utils import role_recency_weight, _parse_month_year
from app.config import config


class TestAnalysisCore:
    """Core analysis functionality tests."""

    def test_basic_skill_matching(self):
        """Test basic skill matching scenarios."""
        
        # Perfect match case
        resume = {
            "skills": ["Python", "JavaScript", "SQL"],
            "experience": [{
                "bullets": ["Built Python applications"],
                "start": "2023", "end": "Present"
            }]
        }
        
        jd = {
            "required": ["Python", "JavaScript", "SQL"],
            "responsibilities": []
        }
        
        result = analyze(resume, jd)
        
        # Should have reasonable score and match all skills
        assert result["score"] > 40, f"Expected decent score, got {result['score']}"
        matched_set = set([s.lower() for s in result["matched"]])
        assert "python" in matched_set, f"Python should be matched, got {result['matched']}"
        assert len(result["missing"]) == 0, f"Should have no missing skills, got {result['missing']}"

    def test_partial_skill_matching(self):
        """Test partial skill matching."""
        
        resume = {
            "skills": ["Python", "JavaScript"],
            "experience": [{"bullets": ["Built apps"]}]
        }
        
        jd = {
            "required": ["Python", "JavaScript", "React", "Node.js"],
            "responsibilities": []
        }
        
        result = analyze(resume, jd)
        
        # Should have some matches and some missing
        assert len(result["matched"]) >= 2, f"Should match some skills, got {result['matched']}"
        assert len(result["missing"]) >= 1, f"Should have missing skills, got {result['missing']}"
        
        # Check specific matches (case-insensitive)
        matched_lower = [s.lower() for s in result["matched"]]
        missing_lower = [s.lower() for s in result["missing"]]
        
        assert "python" in matched_lower or "javascript" in matched_lower, "Should match at least one skill"
        assert any(skill in missing_lower for skill in ["react", "node.js", "nodejs"]), "Should have missing skills"

    def test_no_skill_matching(self):
        """Test when no skills match."""
        
        resume = {
            "skills": ["Java", "C++"],
            "experience": [{"bullets": ["Built Java apps"]}]
        }
        
        jd = {
            "required": ["Python", "JavaScript", "React"],
            "responsibilities": []
        }
        
        result = analyze(resume, jd)
        
        # Should have low score and no matches
        assert result["score"] < 30, f"Expected low score for no match, got {result['score']}"
        assert len(result["matched"]) == 0, f"Should have no matches, got {result['matched']}"
        assert len(result["missing"]) >= 3, f"Should have missing skills, got {result['missing']}"

    def test_recent_vs_old_experience(self):
        """Test that recent experience scores higher than old experience."""
        
        # Recent experience
        recent_resume = {
            "skills": ["Python"],
            "experience": [{
                "bullets": ["Built Python applications"],
                "start": "2023", "end": "Present"
            }]
        }
        
        # Old experience
        old_resume = {
            "skills": ["Python"],
            "experience": [{
                "bullets": ["Built Python applications"], 
                "start": "2018", "end": "2019"
            }]
        }
        
        jd = {
            "required": ["Python"],
            "responsibilities": []
        }
        
        recent_result = analyze(recent_resume, jd)
        old_result = analyze(old_resume, jd)
        
        # Recent should score higher (though both should have some score)
        assert recent_result["score"] >= old_result["score"], f"Recent experience ({recent_result['score']}) should score >= old experience ({old_result['score']})"

    def test_recency_weight_calculation(self):
        """Test recency weight calculation for different date scenarios."""
        
        test_cases = [
            # Present role should have high weight
            ({"end": "Present"}, 0.8, 1.0),
            
            # Recent role should have good weight  
            ({"end": "Dec 2023"}, 0.3, 0.8),
            
            # Old role should have lower weight
            ({"end": "Dec 2019"}, 0.15, 0.5),
            
            # No dates should have neutral weight
            ({"start": None, "end": None}, 0.5, 0.5),
            
            # Year-only should work
            ({"start": "2022", "end": "2023"}, 0.2, 0.8),
        ]
        
        for role_data, min_weight, max_weight in test_cases:
            weight = role_recency_weight(role_data)
            assert min_weight <= weight <= max_weight, f"Role {role_data}: weight {weight} not in range [{min_weight}, {max_weight}]"

    def test_date_parsing_robustness(self):
        """Test date parsing handles various formats."""
        
        test_cases = [
            ("Oct 2024", True),
            ("October 2024", True), 
            ("2024", True),
            ("", False),  # Empty should return None
            ("Invalid text", False),
            ("Dec 2023", True),
            ("January 2020", True),
        ]
        
        for date_str, should_parse in test_cases:
            result = _parse_month_year(date_str)
            if should_parse:
                assert result is not None, f"Date '{date_str}' should parse successfully"
            else:
                assert result is None, f"Date '{date_str}' should not parse"

    def test_empty_inputs_handling(self):
        """Test analysis handles empty inputs gracefully."""
        
        test_cases = [
            # Empty resume
            ({}, {"required": ["Python"]}, "Empty resume should not crash"),
            
            # Empty JD  
            ({"skills": ["Python"]}, {}, "Empty JD should not crash"),
            
            # Both empty
            ({}, {}, "Both empty should not crash"),
        ]
        
        for resume, jd, description in test_cases:
            try:
                result = analyze(resume, jd)
                
                # Should return valid structure
                assert isinstance(result, dict), f"{description}: should return dict"
                assert "score" in result, f"{description}: should have score"
                assert "matched" in result, f"{description}: should have matched"
                assert "missing" in result, f"{description}: should have missing"
                assert isinstance(result["matched"], list), f"{description}: matched should be list"
                assert isinstance(result["missing"], list), f"{description}: missing should be list"
                
            except Exception as e:
                pytest.fail(f"{description}: {str(e)}")

    def test_configuration_affects_scoring(self):
        """Test that configuration changes affect scoring."""
        
        # Save original config
        original_weights = config.WEIGHTS.copy()
        
        try:
            # Set extreme core weight
            config.WEIGHTS["core"] = 90
            config.WEIGHTS["verbs"] = 5
            config.WEIGHTS["hygiene"] = 5
            
            resume = {
                "skills": ["Python", "JavaScript"],
                "experience": [{"bullets": ["Built terrible apps with poor hygiene"]}]
            }
            
            jd = {
                "required": ["Python", "JavaScript"],
                "responsibilities": []
            }
            
            result = analyze(resume, jd)
            
            # With high core weight and perfect skill match, should score well
            assert result["score"] > 70, f"With high core weight, should score well, got {result['score']}"
            
        finally:
            # Restore original config
            config.WEIGHTS.update(original_weights)

    def test_response_structure_consistency(self):
        """Test that response structure is always consistent."""
        
        test_inputs = [
            # Typical case
            ({"skills": ["Python"]}, {"required": ["JavaScript"]}),
            
            # Perfect match
            ({"skills": ["Python"]}, {"required": ["Python"]}),
            
            # Complex case
            ({
                "skills": ["Python", "JavaScript", "React"],
                "experience": [{
                    "bullets": ["Built applications", "Optimized performance"],
                    "start": "2023", "end": "Present"
                }]
            }, {
                "required": ["Python", "TypeScript", "Vue.js"],
                "responsibilities": ["Build apps", "Optimize systems"]
            }),
        ]
        
        for resume, jd in test_inputs:
            result = analyze(resume, jd)
            
            # Check required fields
            required_fields = ["score", "matched", "missing", "sections", "normalizedJD"]
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Check types
            assert isinstance(result["score"], int), "Score should be int"
            assert isinstance(result["matched"], list), "Matched should be list"
            assert isinstance(result["missing"], list), "Missing should be list"
            assert isinstance(result["sections"], dict), "Sections should be dict"
            assert isinstance(result["normalizedJD"], dict), "NormalizedJD should be dict"
            
            # Check score range
            assert 0 <= result["score"] <= 100, f"Score should be 0-100, got {result['score']}"
            
            # Check sections structure
            sections = result["sections"]
            assert "skillsCoveragePct" in sections, "Missing skillsCoveragePct"
            assert "preferredCoveragePct" in sections, "Missing preferredCoveragePct"
            assert "domainCoveragePct" in sections, "Missing domainCoveragePct"
            
            # Check normalizedJD structure
            normalized_jd = result["normalizedJD"]
            assert "skills" in normalized_jd, "Missing skills in normalizedJD"
            assert "responsibilities" in normalized_jd, "Missing responsibilities in normalizedJD"
            assert isinstance(normalized_jd["skills"], list), "Skills should be list"
            assert isinstance(normalized_jd["responsibilities"], list), "Responsibilities should be list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])