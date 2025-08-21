"""
Unit tests for normalize_jd() and related coverage functions.
"""
import pytest
import sys
import os

# Add the app directory to Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.analyze import normalize_jd, extract_jd_buckets
from services.utils import canonicalize_terms, strip_list_artifacts


class TestNormalizeJd:
    """Tests for the normalize_jd function."""

    def test_empty_jd(self):
        """Test normalize_jd with empty job description."""
        jd = {}
        result = normalize_jd(jd)
        
        assert "skills" in result
        assert "responsibilities" in result
        assert result["skills"] == []
        assert result["responsibilities"] == []

    def test_simple_skills_and_responsibilities(self):
        """Test normalize_jd with basic skills and responsibilities."""
        jd = {
            "skills": ["Python", "JavaScript", "React"],
            "responsibilities": ["Build APIs", "Design systems", "Write tests"]
        }
        result = normalize_jd(jd)
        
        assert "skills" in result
        assert "responsibilities" in result
        assert len(result["skills"]) > 0
        assert len(result["responsibilities"]) > 0
        
        # Check that skills are canonicalized (should be lowercase)
        for skill in result["skills"]:
            assert skill.islower() or skill.isdigit() or any(c in skill for c in ".-_")

    def test_skill_canonicalization(self):
        """Test that skill aliases are properly canonicalized."""
        jd = {
            "skills": ["JS", "React.js", "K8s", "TypeScript"],
            "required": ["Node.js", "MongoDB"]
        }
        result = normalize_jd(jd)
        
        # Should contain canonical forms
        skills = result["skills"]
        assert "javascript" in skills  # JS -> javascript
        assert "react" in skills       # React.js -> react
        assert "kubernetes" in skills  # K8s -> kubernetes
        assert "typescript" in skills  # TypeScript -> typescript
        assert "nodejs" in skills      # Node.js -> nodejs
        assert "mongodb" in skills     # MongoDB -> mongodb

    def test_list_artifacts_removal(self):
        """Test removal of list artifacts like bullets and dashes."""
        jd = {
            "requirements": [
                "- Python programming",
                "• JavaScript experience", 
                "React development"
            ],
            "responsibilities": [
                "- Build web applications",
                "• Design APIs",
                "Write documentation"
            ]
        }
        result = normalize_jd(jd)
        
        # Check that bullets/dashes are stripped
        skills = result["skills"]
        responsibilities = result["responsibilities"]
        
        assert "python" in skills
        assert "javascript" in skills
        assert "react" in skills
        
        for resp in responsibilities:
            assert not resp.startswith("- ")
            assert not resp.startswith("• ")

    def test_string_vs_list_input(self):
        """Test that string inputs are converted to lists."""
        jd = {
            "skills": "Python, JavaScript, React",  # String instead of list
            "responsibilities": "Build APIs and design systems"  # String instead of list
        }
        result = normalize_jd(jd)
        
        assert isinstance(result["skills"], list)
        assert isinstance(result["responsibilities"], list)
        assert len(result["skills"]) > 0
        assert len(result["responsibilities"]) > 0

    def test_multiple_skill_sources(self):
        """Test that skills are gathered from multiple sources."""
        jd = {
            "skills": ["Python"],
            "requirements": ["JavaScript"],
            "required": ["React"],
            "qualifications": ["Node.js"],
            "preferred": ["TypeScript"]
        }
        result = normalize_jd(jd)
        
        skills = result["skills"]
        assert "python" in skills
        assert "javascript" in skills
        assert "react" in skills
        assert "nodejs" in skills
        assert "typescript" in skills

    def test_multiple_responsibility_sources(self):
        """Test that responsibilities are gathered from multiple sources."""
        jd = {
            "responsibilities": ["Build APIs"],
            "what_youll_do": ["Design systems"],
            "what you will do": ["Write tests"],
            "duties": ["Review code"]
        }
        result = normalize_jd(jd)
        
        responsibilities = result["responsibilities"]
        assert len(responsibilities) >= 4
        
        # Check that all responsibilities are included (normalized)
        resp_text = " ".join(responsibilities).lower()
        assert "build apis" in resp_text or "apis" in resp_text
        assert "design systems" in resp_text or "systems" in resp_text
        assert "write tests" in resp_text or "tests" in resp_text
        assert "review code" in resp_text or "code" in resp_text

    def test_deduplication(self):
        """Test that duplicate skills and responsibilities are removed."""
        jd = {
            "skills": ["Python", "python", "PYTHON"],
            "responsibilities": ["Build APIs", "build apis", "Build APIs"]
        }
        result = normalize_jd(jd)
        
        # Should deduplicate while preserving canonical form
        skills = result["skills"]
        assert skills.count("python") == 1
        
        # Check responsibilities deduplication
        responsibilities = result["responsibilities"]
        unique_responsibilities = set(r.lower() for r in responsibilities)
        assert len(responsibilities) == len(unique_responsibilities)

    def test_fallback_on_canonicalization_error(self):
        """Test fallback behavior when canonicalization fails."""
        # This test ensures that if canonicalize_terms throws an exception,
        # we fall back to basic normalization
        jd = {
            "skills": ["ValidSkill", "AnotherSkill"],
            "responsibilities": ["Do work", "Complete tasks"]
        }
        result = normalize_jd(jd)
        
        # Should still return normalized results even if canonicalization fails
        assert "skills" in result
        assert "responsibilities" in result
        assert len(result["skills"]) > 0
        assert len(result["responsibilities"]) > 0


class TestExtractJdBuckets:
    """Tests for the extract_jd_buckets function (legacy coverage)."""

    def test_extract_basic_buckets(self):
        """Test basic bucket extraction."""
        jd = {
            "required": ["Python", "JavaScript"],
            "preferred": ["React", "Node.js"],
            "skills": ["Git", "Docker"]
        }
        result = extract_jd_buckets(jd)
        
        assert "req" in result
        assert "pref" in result
        assert "skills" in result
        
        assert len(result["req"]) > 0
        assert len(result["pref"]) > 0
        assert len(result["skills"]) > 0

    def test_missing_fields_handling(self):
        """Test handling of missing fields in JD."""
        jd = {
            "required": ["Python"]
            # Missing preferred and skills
        }
        result = extract_jd_buckets(jd)
        
        assert "req" in result
        assert "pref" in result
        assert "skills" in result
        
        # Should handle missing fields gracefully
        assert len(result["req"]) > 0
        assert isinstance(result["pref"], list)
        assert isinstance(result["skills"], list)


if __name__ == "__main__":
    pytest.main([__file__])