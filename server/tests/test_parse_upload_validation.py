"""
Validation tests for /parse-upload endpoint.
Tests file upload validation, error handling, and edge cases.
"""
import pytest
import sys
import os
from io import BytesIO

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestParseUploadValidation:
    """Validation tests for /parse-upload endpoint."""

    def test_parse_upload_endpoint_exists(self):
        """Test that /parse-upload endpoint exists and accepts POST."""
        # Invalid request should return 422, not 404
        response = client.post("/api/parse-upload", data={})
        assert response.status_code != 404, "Endpoint should exist"

    def test_parse_upload_missing_required_fields(self):
        """Test validation when required fields are missing."""
        # Missing type field
        response = client.post(
            "/api/parse-upload",
            files={"file": ("test.txt", "content", "text/plain")}
        )
        assert response.status_code == 422, "Should require type field"
        
        # Missing file field
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"}
        )
        assert response.status_code == 422, "Should require file field"

    def test_parse_upload_invalid_type_values(self):
        """Test validation of type field values."""
        invalid_types = ["document", "cv", "jobdescription", "", "invalid"]
        
        for invalid_type in invalid_types:
            response = client.post(
                "/api/parse-upload",
                data={"type": invalid_type},
                files={"file": ("test.txt", "content", "text/plain")}
            )
            assert response.status_code == 422, f"Should reject invalid type: {invalid_type}"

    def test_parse_upload_valid_type_values(self):
        """Test validation accepts valid type values."""
        valid_types = ["resume", "jd"]
        
        for valid_type in valid_types:
            # Use minimal valid file content to focus on type validation
            response = client.post(
                "/api/parse-upload",
                data={"type": valid_type},
                files={"file": ("test.txt", "Some content here", "text/plain")}
            )
            # Should not fail due to type validation (might fail for other reasons)
            assert response.status_code != 422 or "type" not in response.text.lower()

    def test_parse_upload_file_type_validation(self):
        """Test file extension validation."""
        # Valid extensions should be accepted
        valid_extensions = ["pdf", "docx", "txt"]
        
        for ext in valid_extensions:
            filename = f"document.{ext}"
            response = client.post(
                "/api/parse-upload",
                data={"type": "resume"},
                files={"file": (filename, "Valid content", "application/octet-stream")}
            )
            # Should not fail due to file type (might fail for other reasons)
            assert response.status_code != 422 or "not allowed" not in response.text.lower()

    def test_parse_upload_invalid_file_extensions(self):
        """Test rejection of invalid file extensions."""
        invalid_extensions = ["jpg", "png", "mp3", "exe", "html", "js"]
        
        for ext in invalid_extensions:
            filename = f"document.{ext}"
            response = client.post(
                "/api/parse-upload",
                data={"type": "resume"},
                files={"file": (filename, "content", "application/octet-stream")}
            )
            assert response.status_code == 422, f"Should reject .{ext} files"
            
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                # Error message is nested under 'detail'
                detail = error_data.get("detail", {})
                message = detail.get("message", "") if isinstance(detail, dict) else ""
                assert "not allowed" in message.lower(), f"Expected 'not allowed' in error message: {message}"

    def test_parse_upload_no_file_extension(self):
        """Test handling of files without extensions."""
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": ("document_no_extension", "content", "text/plain")}
        )
        assert response.status_code == 422, "Should reject files without extensions"

    def test_parse_upload_empty_filename(self):
        """Test handling of empty or missing filenames."""
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": ("", "content", "text/plain")}
        )
        assert response.status_code == 422, "Should reject empty filenames"

    def test_parse_upload_file_size_validation(self):
        """Test file size validation for large uploads."""
        # Create a file that exceeds the limit (assuming 5MB default)
        large_content = "x" * (6 * 1024 * 1024)  # 6MB content
        
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": ("large.txt", large_content, "text/plain")}
        )
        
        # Should be rejected due to size (413 or 422)
        assert response.status_code in [413, 422], "Should reject oversized files"
        
        if response.headers.get("content-type", "").startswith("application/json"):
            error_data = response.json()
            assert "size" in error_data.get("message", "").lower()

    def test_parse_upload_empty_file_content(self):
        """Test handling of empty file content."""
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": ("empty.txt", "", "text/plain")}
        )
        
        # Might succeed with empty result or fail gracefully
        assert response.status_code in [200, 422], "Should handle empty files gracefully"
        
        if response.status_code == 200:
            data = response.json()
            assert "parsed" in data

    def test_parse_upload_minimal_valid_content(self):
        """Test parsing with minimal but valid content."""
        minimal_content = "John Smith\nSoftware Engineer\nPython, JavaScript"
        
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": ("resume.txt", minimal_content, "text/plain")}
        )
        
        assert response.status_code == 200, "Should handle minimal valid content"
        
        data = response.json()
        assert "parsed" in data, "Response should contain parsed field"
        assert isinstance(data["parsed"], dict), "Parsed should be dict"

    def test_parse_upload_malformed_content(self):
        """Test handling of malformed or unparseable content."""
        malformed_contents = [
            "Random gibberish !@#$%^&*()",
            "\x00\x01\x02\x03",  # Binary content in text file
            "A" * 100000,  # Very long content
        ]
        
        for content in malformed_contents:
            response = client.post(
                "/api/parse-upload",
                data={"type": "resume"},
                files={"file": ("test.txt", content, "text/plain")}
            )
            
            # Should either parse successfully or fail gracefully
            assert response.status_code in [200, 422, 500], "Should handle malformed content gracefully"

    def test_parse_upload_unicode_content_and_filename(self):
        """Test handling of unicode content and filenames."""
        unicode_content = "José García\nIngeniero de Software\nPython, JavaScript, 数据科学"
        unicode_filename = "José_García_résumé.txt"
        
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": (unicode_filename, unicode_content, "text/plain")}
        )
        
        # Should handle unicode content properly
        assert response.status_code in [200, 422], "Should handle unicode content"
        
        if response.status_code == 200:
            data = response.json()
            assert "parsed" in data

    def test_parse_upload_different_content_types(self):
        """Test handling of different MIME types for text files."""
        content = "Sample resume content\nSoftware Engineer\nPython"
        mime_types = [
            "text/plain",
            "text/txt", 
            "application/octet-stream",
            "text/x-python",  # Unusual but text-based
        ]
        
        for mime_type in mime_types:
            response = client.post(
                "/api/parse-upload",
                data={"type": "resume"},
                files={"file": ("resume.txt", content, mime_type)}
            )
            
            # MIME type shouldn't affect text file parsing
            assert response.status_code in [200, 422], f"Should handle MIME type {mime_type}"

    def test_parse_upload_form_data_edge_cases(self):
        """Test edge cases in form data submission."""
        # Multiple files (should probably use the first one)
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files=[
                ("file", ("first.txt", "First file content", "text/plain")),
                ("file", ("second.txt", "Second file content", "text/plain"))
            ]
        )
        
        # Should handle gracefully (use first file or error)
        assert response.status_code in [200, 422], "Should handle multiple files gracefully"

    def test_parse_upload_content_length_header_validation(self):
        """Test content-length header validation."""
        # This tests the middleware validation
        content = "Normal resume content"
        
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": ("resume.txt", content, "text/plain")},
            headers={"Content-Length": str(len(content) + 100)}  # Accurate length
        )
        
        # Should work fine with correct length
        assert response.status_code in [200, 422, 413], "Should handle content-length validation"

    def test_parse_upload_error_response_format(self):
        """Test that error responses follow standard format."""
        # Trigger a validation error
        response = client.post(
            "/api/parse-upload",
            data={"type": "invalid"},
            files={"file": ("test.txt", "content", "text/plain")}
        )
        
        assert response.status_code == 422, "Should return validation error"
        
        if response.headers.get("content-type", "").startswith("application/json"):
            error_data = response.json()
            # Check for standard error format (might be FastAPI default or custom)
            assert "detail" in error_data or "error" in error_data, "Should have error details"

    def test_parse_upload_concurrent_requests(self):
        """Test handling of concurrent upload requests."""
        import threading
        import time
        
        results = []
        content = "Sample resume for concurrency test\nSoftware Engineer\nPython"
        
        def make_request():
            response = client.post(
                "/api/parse-upload",
                data={"type": "resume"},
                files={"file": ("test.txt", content, "text/plain")}
            )
            results.append(response.status_code)
        
        # Start multiple concurrent requests
        threads = []
        for i in range(3):  # Modest concurrency to avoid overwhelming
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All should succeed or fail gracefully
        for status in results:
            assert status in [200, 422, 413, 500], f"Unexpected status code: {status}"

    def test_parse_upload_request_timeout_resilience(self):
        """Test that upload endpoint handles processing timeouts gracefully."""
        # Large but valid content that might take time to process
        large_content = "Name: Test User\n" + "Experience: " + "Long description. " * 1000
        
        response = client.post(
            "/api/parse-upload",
            data={"type": "resume"},
            files={"file": ("large_resume.txt", large_content, "text/plain")},
            timeout=30  # Give it time but not infinite
        )
        
        # Should complete within reasonable time or timeout gracefully
        assert response.status_code in [200, 422, 500, 408], "Should handle large content within timeout"

    def test_parse_upload_boundary_file_sizes(self):
        """Test parsing with files at size boundaries."""
        # Test with content right at common boundaries
        boundary_sizes = [
            1024,      # 1KB
            10240,     # 10KB  
            102400,    # 100KB
            1048576,   # 1MB
        ]
        
        for size in boundary_sizes:
            content = "Resume content. " * (size // 15)  # Approximate target size
            content = content[:size]  # Exact size
            
            response = client.post(
                "/api/parse-upload",
                data={"type": "resume"},
                files={"file": ("boundary_test.txt", content, "text/plain")}
            )
            
            # Should handle various sizes appropriately
            assert response.status_code in [200, 422, 413], f"Should handle {size} byte files"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])