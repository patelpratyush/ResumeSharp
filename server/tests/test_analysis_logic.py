"""
Unit tests for analysis logic with golden test cases.
Tests scoring, coverage calculation, and recency edge cases.
"""
import pytest
import sys
import os
from datetime import date

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.services.analyze import analyze, extract_jd_buckets, extract_resume_terms, coverage, verb_alignment, hygiene, _recency_score_for_terms
from app.services.utils import role_recency_weight, _parse_month_year
from app.config import config


class TestAnalysisLogic:
    """Tests for core analysis logic."""

    def test_scoring_scenarios_golden_cases(self):
        """Golden test cases for different scoring scenarios."""
        
        test_cases = [
            {
                "name": "Perfect match",
                "resume": {
                    "skills": ["Python", "JavaScript", "React", "SQL"],
                    "experience": [{
                        "company": "Tech Corp",
                        "role": "Software Engineer", 
                        "bullets": ["Built applications", "Optimized performance"],
                        "start": "2023",
                        "end": "Present"
                    }]
                },
                "jd": {
                    "title": "Software Engineer",
                    "required": ["Python", "JavaScript", "React", "SQL"],
                    "responsibilities": ["Build applications", "Optimize systems"]
                },
                "expected_score_range": (85, 100),  # Should score very high
                "expected_matched": ["Python", "JavaScript", "React", "SQL"],
                "expected_missing": []
            },
            {
                "name": "Partial match",
                "resume": {
                    "skills": ["Python", "JavaScript"],
                    "experience": [{
                        "company": "Tech Corp",
                        "role": "Developer",
                        "bullets": ["Built web apps"],
                        "start": "2022",
                        "end": "2023"
                    }]
                },
                "jd": {
                    "title": "Full Stack Developer", 
                    "required": ["Python", "JavaScript", "React", "Node.js"],
                    "responsibilities": ["Build web applications"]
                },
                "expected_score_range": (40, 70),  # Moderate score
                "expected_matched": ["Python", "JavaScript"],
                "expected_missing_contains": ["React", "Node.js"]
            },
            {
                "name": "No match",
                "resume": {
                    "skills": ["Java", "C++"],
                    "experience": [{
                        "company": "Corp",
                        "role": "Developer",
                        "bullets": ["Maintained legacy systems"]
                    }]
                },
                "jd": {
                    "title": "Python Developer",
                    "required": ["Python", "Django", "PostgreSQL"],
                    "responsibilities": ["Build Django applications"]
                },
                "expected_score_range": (0, 25),  # Low score
                "expected_matched": [],
                "expected_missing_contains": ["Python", "Django", "PostgreSQL"]
            },
            {
                "name": "Strong verbs boost",
                "resume": {
                    "skills": ["Python"],
                    "experience": [{
                        "company": "Tech Corp",
                        "role": "Engineer",
                        "bullets": [
                            "Built scalable Python applications",
                            "Optimized database performance", 
                            "Deployed microservices architecture"
                        ],
                        "start": "2023",
                        "end": "Present"
                    }]
                },
                "jd": {
                    "title": "Python Engineer",
                    "required": ["Python"],
                    "responsibilities": ["Build applications", "Optimize systems", "Deploy services"]
                },
                "expected_score_range": (80, 100),  # High due to verb alignment
                "expected_matched": ["Python"],
                "expected_missing": []
            },
            {
                "name": "Old experience penalty",
                "resume": {
                    "skills": ["Python", "JavaScript", "React"],
                    "experience": [{
                        "company": "Old Corp",
                        "role": "Developer",
                        "bullets": ["Built Python applications"],
                        "start": "2018",
                        "end": "2019"  # Old experience
                    }]
                },
                "jd": {
                    "title": "Python Developer",
                    "required": ["Python", "JavaScript", "React"],
                    "responsibilities": ["Build applications"]
                },
                "expected_score_range": (40, 80),  # Lower due to old experience
                "expected_matched": ["Python", "JavaScript", "React"],
                "expected_missing": []
            }
        ]
        
        for case in test_cases:
            result = analyze(case["resume"], case["jd"])
            
            # Check score range
            score = result["score"]
            min_score, max_score = case["expected_score_range"]
            assert min_score <= score <= max_score, f"Case '{case['name']}': score {score} not in range {case['expected_score_range']}"
            
            # Check matched skills
            if "expected_matched" in case:
                matched = set(result["matched"])
                expected = set(case["expected_matched"])
                assert matched >= expected, f"Case '{case['name']}': missing matched skills. Got {matched}, expected to contain {expected}"
            
            # Check missing skills
            if "expected_missing" in case:
                missing = set(result["missing"])
                expected = set(case["expected_missing"])
                assert missing == expected, f"Case '{case['name']}': wrong missing skills. Got {missing}, expected {expected}"
            
            if "expected_missing_contains" in case:
                missing = set(result["missing"])
                expected_contains = set(case["expected_missing_contains"])
                assert missing >= expected_contains, f"Case '{case['name']}': missing should contain {expected_contains}, got {missing}"

    def test_coverage_calculation(self):
        """Test coverage calculation for different scenarios."""
        
        test_cases = [
            {
                "name": "Exact matches",
                "targets": ["Python", "JavaScript", "React"],
                "haystack": ["Python", "JavaScript", "React", "SQL"],
                "expected_present": ["Python", "JavaScript", "React"],
                "expected_missing": []
            },
            {
                "name": "Partial matches",
                "targets": ["Python", "JavaScript", "React", "Vue.js"],
                "haystack": ["Python", "React"],
                "expected_present": ["Python", "React"],
                "expected_missing": ["JavaScript", "Vue.js"]
            },
            {
                "name": "No matches",
                "targets": ["Python", "JavaScript"],
                "haystack": ["Java", "C++"],
                "expected_present": [],
                "expected_missing": ["Python", "JavaScript"]
            },
            {
                "name": "Fuzzy matches",
                "targets": ["JavaScript", "Node.js", "React"],
                "haystack": ["javascript", "nodejs", "react.js"],  # Different casing/formatting
                "expected_present": ["JavaScript", "Node.js", "React"],
                "expected_missing": []
            }
        ]
        
        for case in test_cases:
            present, missing = coverage(case["targets"], case["haystack"])
            
            assert set(present) == set(case["expected_present"]), f"Case '{case['name']}': wrong present skills"
            assert set(missing) == set(case["expected_missing"]), f"Case '{case['name']}': wrong missing skills"

    def test_verb_alignment_scoring(self):
        """Test verb alignment scoring."""
        
        test_cases = [
            {
                "name": "Perfect verb alignment",
                "jd_verbs": ["Build applications", "Optimize performance", "Deploy systems"],
                "resume_bullets": ["Built web applications", "Optimized database performance", "Deployed microservices"],
                "expected_score": 1.0
            },
            {
                "name": "Partial verb alignment", 
                "jd_verbs": ["Build applications", "Optimize performance", "Deploy systems"],
                "resume_bullets": ["Built web apps", "Maintained legacy code"],
                "expected_score": 0.33  # 1/3 verbs match
            },
            {
                "name": "No verb alignment",
                "jd_verbs": ["Build applications", "Optimize performance"],
                "resume_bullets": ["Managed team", "Attended meetings"],
                "expected_score": 0.0
            }
        ]
        
        for case in test_cases:
            score = verb_alignment(case["jd_verbs"], case["resume_bullets"])
            assert abs(score - case["expected_score"]) < 0.1, f"Case '{case['name']}': expected {case['expected_score']}, got {score}"

    def test_hygiene_scoring(self):
        """Test resume hygiene scoring."""
        
        test_cases = [
            {
                "name": "Good hygiene",
                "resume": {
                    "experience": [{
                        "bullets": [
                            "Built scalable web applications serving 10,000+ users",
                            "Optimized database queries resulting in 25% performance improvement", 
                            "Deployed microservices architecture reducing deployment time by 50%"
                        ]
                    }]
                },
                "expected_score_range": (0.8, 1.0)  # Good length + numbers
            },
            {
                "name": "Poor hygiene - short bullets",
                "resume": {
                    "experience": [{
                        "bullets": [
                            "Coded",
                            "Fixed bugs", 
                            "Did work"
                        ]
                    }]
                },
                "expected_score_range": (0.0, 0.3)  # Too short
            },
            {
                "name": "Poor hygiene - no numbers",
                "resume": {
                    "experience": [{
                        "bullets": [
                            "Built applications for the company",
                            "Worked on various projects and tasks",
                            "Collaborated with team members on development"
                        ]
                    }]
                },
                "expected_score_range": (0.0, 0.6)  # No quantification
            },
            {
                "name": "No experience",
                "resume": {"experience": []},
                "expected_score": 0.2
            }
        ]
        
        for case in test_cases:
            score = hygiene(case["resume"])
            
            if "expected_score" in case:
                assert score == case["expected_score"], f"Case '{case['name']}': expected {case['expected_score']}, got {score}"
            else:
                min_score, max_score = case["expected_score_range"]
                assert min_score <= score <= max_score, f"Case '{case['name']}': score {score} not in range {case['expected_score_range']}"

    def test_recency_edge_cases(self):
        """Test recency scoring edge cases."""
        
        test_cases = [
            {
                "name": "Present role",
                "role": {"start": "Jan 2023", "end": "Present"},
                "expected_weight_range": (0.9, 1.0)  # Very recent
            },
            {
                "name": "Recent role (1 year ago)",
                "role": {"start": "Jan 2022", "end": "Dec 2023"},
                "expected_weight_range": (0.7, 0.9)  # Still recent
            },
            {
                "name": "Old role (5 years ago)",
                "role": {"start": "Jan 2018", "end": "Dec 2019"},
                "expected_weight_range": (0.15, 0.4)  # Much older
            },
            {
                "name": "Year-only dates",
                "role": {"start": "2022", "end": "2023"},
                "expected_weight_range": (0.5, 0.9)  # Should handle year-only
            },
            {
                "name": "Missing end date",
                "role": {"start": "Jan 2023", "end": None},
                "expected_weight_range": (0.4, 0.6)  # Neutral fallback
            },
            {
                "name": "Missing dates entirely",
                "role": {"start": None, "end": None},
                "expected_weight": 0.5  # Neutral
            }
        ]
        
        for case in test_cases:
            weight = role_recency_weight(case["role"])
            
            if "expected_weight" in case:
                assert weight == case["expected_weight"], f"Case '{case['name']}': expected {case['expected_weight']}, got {weight}"
            else:
                min_weight, max_weight = case["expected_weight_range"]
                assert min_weight <= weight <= max_weight, f"Case '{case['name']}': weight {weight} not in range {case['expected_weight_range']}"

    def test_date_parsing_edge_cases(self):
        """Test date parsing handles various formats."""
        
        test_cases = [
            ("Oct 2024", date(2024, 10, 1)),
            ("October 2024", date(2024, 10, 1)),
            ("2024", date(2024, 6, 1)),  # Mid-year fallback
            ("", None),
            ("Invalid", None),
            ("Dec 2023", date(2023, 12, 1)),
            ("January 2020", date(2020, 1, 1))
        ]
        
        for date_str, expected in test_cases:
            result = _parse_month_year(date_str)
            assert result == expected, f"Date '{date_str}': expected {expected}, got {result}"

    def test_recency_scoring_with_terms(self):
        """Test recency scoring combines with term matching."""
        
        # Recent role with matching terms
        recent_roles = [{
            "company": "Tech Corp",
            "role": "Python Developer", 
            "bullets": ["Built Python applications", "Used React framework"],
            "start": "2023",
            "end": "Present"
        }]
        
        old_roles = [{
            "company": "Old Corp",
            "role": "Python Developer",
            "bullets": ["Built Python applications", "Used React framework"], 
            "start": "2018",
            "end": "2019"
        }]
        
        core_terms = ["Python", "React"]
        
        recent_score, recent_details = _recency_score_for_terms(core_terms, recent_roles)
        old_score, old_details = _recency_score_for_terms(core_terms, old_roles)
        
        # Recent experience should score higher
        assert recent_score > old_score, f"Recent score {recent_score} should be higher than old score {old_score}"
        assert recent_score > 0.8, f"Recent score should be high, got {recent_score}"
        assert old_score < 0.5, f"Old score should be lower, got {old_score}"

    def test_scoring_weights_configuration(self):
        """Test that scoring uses configurable weights."""
        
        # Save original weights
        original_weights = config.WEIGHTS.copy()
        
        try:
            # Test with extreme weights
            config.WEIGHTS = {
                "core": 100,  # Only core skills matter
                "preferred": 0,
                "verbs": 0, 
                "domain": 0,
                "recency": 0,
                "hygiene": 0
            }
            
            resume = {
                "skills": ["Python", "JavaScript"],
                "experience": [{
                    "bullets": ["Did some work"],
                    "start": "2018", "end": "2019"  # Old + poor hygiene
                }]
            }
            
            jd = {
                "required": ["Python", "JavaScript"],
                "responsibilities": []
            }
            
            result = analyze(resume, jd)
            
            # With 100% core weight and perfect match, should score very high
            assert result["score"] >= 90, f"With 100% core weight, perfect match should score high, got {result['score']}"
            
        finally:
            # Restore original weights
            config.WEIGHTS = original_weights

    def test_edge_case_empty_inputs(self):
        """Test analysis handles empty/minimal inputs gracefully."""
        
        test_cases = [
            {
                "name": "Empty resume",
                "resume": {},
                "jd": {"required": ["Python"]},
                "expected_score_range": (0, 5)  # Very low but not zero
            },
            {
                "name": "Empty JD",
                "resume": {"skills": ["Python"]},
                "jd": {},
                "expected_score_range": (0, 5)  # Very low but not zero
            },
            {
                "name": "Both empty",
                "resume": {},
                "jd": {},
                "expected_score_range": (0, 5)  # Very low but not zero
            },
            {
                "name": "Minimal valid input",
                "resume": {"skills": ["Python"]},
                "jd": {"required": ["Python"]},
                "expected_score_range": (35, 50)  # Moderate score for minimal match
            }
        ]
        
        for case in test_cases:
            result = analyze(case["resume"], case["jd"])
            
            # Should always return valid structure
            assert isinstance(result, dict)
            assert "score" in result
            assert "matched" in result
            assert "missing" in result
            assert isinstance(result["matched"], list)
            assert isinstance(result["missing"], list)
            
            if "expected_score" in case:
                assert result["score"] == case["expected_score"], f"Case '{case['name']}': wrong score"
            elif "expected_score_range" in case:
                min_score, max_score = case["expected_score_range"]
                assert min_score <= result["score"] <= max_score, f"Case '{case['name']}': score {result['score']} not in range {case['expected_score_range']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])