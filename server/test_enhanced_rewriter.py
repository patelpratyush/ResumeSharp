#!/usr/bin/env python3
"""
Test script for the enhanced bullet rewriter.
Shows before/after examples with different types of resume bullets.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.rewrite import rewrite

def test_rewriter():
    print("🚀 Enhanced Resume Bullet Rewriter Test")
    print("=" * 50)
    
    test_cases = [
        {
            "bullet": "Responsible for building web applications",
            "jd_keywords": ["React", "Node.js", "MongoDB"],
            "context": "Generic weak opener"
        },
        {
            "bullet": "Worked on API development using Python",
            "jd_keywords": ["FastAPI", "PostgreSQL", "Docker"],
            "context": "Weak verb with existing tech"
        },
        {
            "bullet": "Helped create user interfaces for mobile app",
            "jd_keywords": ["React Native", "TypeScript"],
            "context": "Weak helper verb"
        },
        {
            "bullet": "Built machine learning models",
            "jd_keywords": ["TensorFlow", "Python", "AWS"],
            "context": "Good verb, needs quantification"
        },
        {
            "bullet": "Led team of 5 developers on microservices project",
            "jd_keywords": ["Kubernetes", "Docker", "Go"],
            "context": "Management bullet with numbers"
        },
        {
            "bullet": "Improved system performance through code optimization",
            "jd_keywords": ["Redis", "Elasticsearch"],
            "context": "Performance improvement"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['context']}")
        print(f"   Original: \"{case['bullet']}\"")
        
        result = rewrite('experience', case['bullet'], {
            'jd_keywords': case['jd_keywords'],
            'max_words': 25,
            'add_impact': True,
            'enhance_technical': True,
            'preserve_numbers': True
        })
        
        enhanced = result['rewritten']
        word_count = len(enhanced.split())
        
        print(f"   Enhanced: \"{enhanced}\"")
        print(f"   Word count: {word_count}/25")
        
        # Show improvements
        improvements = []
        if "responsible for" in case['bullet'].lower() and "responsible for" not in enhanced.lower():
            improvements.append("✓ Removed weak opener")
        if any(kw.lower() in enhanced.lower() for kw in case['jd_keywords']):
            improvements.append("✓ Added JD keywords")
        if any(char.isdigit() for char in enhanced) and not any(char.isdigit() for char in case['bullet']):
            improvements.append("✓ Added quantified impact")
        if "leveraging" in enhanced or "utilizing" in enhanced:
            improvements.append("✓ Natural keyword integration")
        
        if improvements:
            print(f"   Improvements: {', '.join(improvements)}")

if __name__ == "__main__":
    test_rewriter()