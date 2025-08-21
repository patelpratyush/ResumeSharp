"""
Unit tests for error handling system.
Tests error formatting, exception handling, and validation.
"""
import pytest
import sys
import os
import json

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.error_handler import (
    APIError, ValidationError, ParseError, AnalysisError, ConfigurationError,
    format_error_response, handle_exception, validate_request_size,
    validate_file_type, validate_text_length, safe_execute
)
from app.config import config
from fastapi import HTTPException


class TestErrorClasses:
    """Test custom error classes."""

    def test_api_error_creation(self):
        """Test basic APIError creation."""
        error = APIError(
            message="Test error",
            status_code=500,
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}

    def test_validation_error_defaults(self):
        """Test ValidationError has correct defaults."""
        error = ValidationError("Invalid input")
        
        assert error.message == "Invalid input"
        assert error.status_code == 422
        assert error.error_code == "VALIDATION_ERROR"

    def test_parse_error_with_file_type(self):
        """Test ParseError includes file type in details."""
        error = ParseError("Parse failed", file_type="pdf", details={"line": 5})
        
        assert error.message == "Parse failed"
        assert error.status_code == 400
        assert error.error_code == "PARSE_ERROR"
        assert error.details["file_type"] == "pdf"
        assert error.details["line"] == 5

    def test_analysis_error_creation(self):
        """Test AnalysisError creation."""
        error = AnalysisError("Analysis failed", details={"resume_id": "123"})
        
        assert error.message == "Analysis failed"
        assert error.status_code == 500
        assert error.error_code == "ANALYSIS_ERROR"
        assert error.details["resume_id"] == "123"

    def test_configuration_error_creation(self):
        """Test ConfigurationError creation."""
        error = ConfigurationError("Config invalid")
        
        assert error.message == "Config invalid"
        assert error.status_code == 500
        assert error.error_code == "CONFIG_ERROR"


class TestErrorFormatting:
    """Test error response formatting."""

    def test_format_error_response_basic(self):
        """Test basic error response formatting."""
        error = ValidationError("Invalid field", details={"field": "email"})
        response = format_error_response(error)
        
        expected_keys = {"error", "message", "error_code", "status_code", "details"}
        assert set(response.keys()) == expected_keys
        
        assert response["error"] is True
        assert response["message"] == "Invalid field"
        assert response["error_code"] == "VALIDATION_ERROR"
        assert response["status_code"] == 422
        assert response["details"]["field"] == "email"

    def test_format_error_response_no_details(self):
        """Test error formatting without details."""
        error = APIError("Simple error")
        response = format_error_response(error)
        
        assert "details" not in response
        assert response["error"] is True
        assert response["message"] == "Simple error"

    def test_format_error_response_debug_mode(self):
        """Test error formatting includes traceback in debug mode."""
        # Save original debug setting
        original_debug = config.DEBUG_MODE
        
        try:
            config.DEBUG_MODE = True
            
            # Create error to get a traceback
            try:
                raise ValueError("Test exception")
            except ValueError:
                error = APIError("Error with traceback")
                response = format_error_response(error)
                
                assert "traceback" in response
                assert "ValueError: Test exception" in response["traceback"]
        
        finally:
            config.DEBUG_MODE = original_debug


class TestExceptionHandling:
    """Test exception handling and conversion."""

    def test_handle_api_error(self):
        """Test handling of APIError instances."""
        api_error = ValidationError("Invalid input", details={"field": "content"})
        
        http_exc = handle_exception(api_error, "test_context")
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 422
        assert isinstance(http_exc.detail, dict)
        assert http_exc.detail["error"] is True
        assert http_exc.detail["message"] == "Invalid input"

    def test_handle_value_error(self):
        """Test handling of ValueError."""
        value_error = ValueError("Invalid value provided")
        
        http_exc = handle_exception(value_error, "validation")
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 422
        assert http_exc.detail["error_code"] == "VALIDATION_ERROR"
        assert "Invalid value provided" in http_exc.detail["message"]
        assert http_exc.detail["details"]["context"] == "validation"

    def test_handle_file_not_found_error(self):
        """Test handling of FileNotFoundError."""
        file_error = FileNotFoundError("File not found")
        
        http_exc = handle_exception(file_error, "file_parsing")
        
        assert http_exc.status_code == 400  # ParseError default
        assert http_exc.detail["error_code"] == "PARSE_ERROR"
        assert "File not found" in http_exc.detail["message"]

    def test_handle_permission_error(self):
        """Test handling of PermissionError."""
        perm_error = PermissionError("Access denied")
        
        http_exc = handle_exception(perm_error, "file_access")
        
        assert http_exc.status_code == 403
        assert http_exc.detail["error_code"] == "PERMISSION_ERROR"
        assert http_exc.detail["message"] == "Permission denied"

    def test_handle_timeout_error(self):
        """Test handling of TimeoutError."""
        timeout_error = TimeoutError("Operation timed out")
        
        http_exc = handle_exception(timeout_error, "llm_request")
        
        assert http_exc.status_code == 408
        assert http_exc.detail["error_code"] == "TIMEOUT_ERROR"
        assert http_exc.detail["message"] == "Operation timed out"

    def test_handle_generic_exception(self):
        """Test handling of generic exceptions."""
        generic_error = RuntimeError("Unexpected error")
        
        http_exc = handle_exception(generic_error, "processing")
        
        assert http_exc.status_code == 500
        assert http_exc.detail["error_code"] == "INTERNAL_ERROR"
        assert http_exc.detail["details"]["context"] == "processing"
        assert http_exc.detail["details"]["exception_type"] == "RuntimeError"

    def test_handle_exception_debug_vs_production(self):
        """Test exception handling differs between debug and production."""
        # Save original debug setting
        original_debug = config.DEBUG_MODE
        
        try:
            error = RuntimeError("Sensitive error details")
            
            # Production mode - generic message
            config.DEBUG_MODE = False
            http_exc_prod = handle_exception(error, "test")
            assert http_exc_prod.detail["message"] == "An internal error occurred"
            
            # Debug mode - actual error message
            config.DEBUG_MODE = True
            http_exc_debug = handle_exception(error, "test")
            assert "Sensitive error details" in http_exc_debug.detail["message"]
        
        finally:
            config.DEBUG_MODE = original_debug


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_request_size_valid(self):
        """Test request size validation with valid size."""
        # Should not raise for valid size
        validate_request_size(1024 * 1024)  # 1MB
        validate_request_size(None)  # No size header
        validate_request_size(0)  # Empty request

    def test_validate_request_size_too_large(self):
        """Test request size validation with oversized request."""
        max_size_mb = 5
        max_bytes = max_size_mb * 1024 * 1024
        oversized = max_bytes + (1024 * 1024)  # Add 1MB to be clearly over
        
        with pytest.raises(ValidationError) as exc_info:
            validate_request_size(oversized, max_size_mb)
        
        error = exc_info.value
        assert "exceeds maximum allowed size" in error.message
        assert error.details["max_size_mb"] == max_size_mb
        assert error.details["actual_size_mb"] > max_size_mb

    def test_validate_file_type_valid(self):
        """Test file type validation with valid extensions."""
        validate_file_type("document.pdf", ["pdf", "docx", "txt"])
        validate_file_type("resume.docx", ["pdf", "docx"])
        validate_file_type("text.txt", ["txt"])

    def test_validate_file_type_invalid(self):
        """Test file type validation with invalid extensions."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_type("image.jpg", ["pdf", "docx"])
        
        error = exc_info.value
        assert "not allowed" in error.message
        assert error.details["provided_extension"] == "jpg"
        assert error.details["allowed_extensions"] == ["pdf", "docx"]

    def test_validate_file_type_no_extension(self):
        """Test file type validation with no extension."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_type("filename_no_ext", ["pdf"])
        
        error = exc_info.value
        assert "not allowed" in error.message
        assert error.details["provided_extension"] == ""

    def test_validate_file_type_empty_filename(self):
        """Test file type validation with empty filename."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_type("", ["pdf"])
        
        error = exc_info.value
        assert "required" in error.message

    def test_validate_text_length_valid(self):
        """Test text length validation with valid text."""
        validate_text_length("Short text", 100)
        validate_text_length("A" * 50, 100, "content")

    def test_validate_text_length_too_long(self):
        """Test text length validation with oversized text."""
        long_text = "A" * 1001
        
        with pytest.raises(ValidationError) as exc_info:
            validate_text_length(long_text, 1000, "description")
        
        error = exc_info.value
        assert "exceeds maximum length" in error.message
        assert error.details["max_length"] == 1000
        assert error.details["actual_length"] == 1001
        assert error.details["field_name"] == "description"


class TestSafeExecute:
    """Test safe execution wrapper."""

    def test_safe_execute_success(self):
        """Test safe execution with successful function."""
        def successful_function(a, b, c=None):
            return a + b + (c or 0)
        
        result = safe_execute(successful_function, 2, 3, c=5, context="math")
        assert result == 10

    def test_safe_execute_exception(self):
        """Test safe execution with failing function."""
        def failing_function():
            raise ValueError("Function failed")
        
        with pytest.raises(HTTPException) as exc_info:
            safe_execute(failing_function, context="test_operation")
        
        http_exc = exc_info.value
        assert http_exc.status_code == 422  # ValueError -> ValidationError
        assert http_exc.detail["error_code"] == "VALIDATION_ERROR"
        assert http_exc.detail["details"]["context"] == "test_operation"

    def test_safe_execute_with_api_error(self):
        """Test safe execution with APIError."""
        def function_with_api_error():
            raise ParseError("Parse failed", file_type="pdf")
        
        with pytest.raises(HTTPException) as exc_info:
            safe_execute(function_with_api_error, context="parsing")
        
        http_exc = exc_info.value
        assert http_exc.status_code == 400
        assert http_exc.detail["error_code"] == "PARSE_ERROR"

    def test_safe_execute_preserves_return_type(self):
        """Test safe execution preserves return types."""
        def return_dict():
            return {"key": "value", "number": 42}
        
        def return_list():
            return [1, 2, 3]
        
        def return_string():
            return "test string"
        
        assert safe_execute(return_dict, context="test") == {"key": "value", "number": 42}
        assert safe_execute(return_list, context="test") == [1, 2, 3]
        assert safe_execute(return_string, context="test") == "test string"


class TestErrorHandlerIntegration:
    """Integration tests for error handling system."""

    def test_error_response_consistency(self):
        """Test all error types produce consistent response format."""
        errors = [
            ValidationError("Validation failed"),
            ParseError("Parse failed", file_type="pdf"),
            AnalysisError("Analysis failed"),
            ConfigurationError("Config invalid"),
            APIError("Generic error", status_code=503, error_code="SERVICE_UNAVAILABLE")
        ]
        
        for error in errors:
            response = format_error_response(error)
            
            # All should have required fields
            required_fields = {"error", "message", "error_code", "status_code"}
            assert set(response.keys()) >= required_fields
            
            # Error field should always be True
            assert response["error"] is True
            
            # Status code should be valid HTTP code
            assert 400 <= response["status_code"] < 600
            
            # Error code should be string
            assert isinstance(response["error_code"], str)
            assert len(response["error_code"]) > 0

    def test_context_preservation(self):
        """Test that context is preserved through error handling."""
        contexts = ["parsing", "analysis", "file_upload", "llm_request", "validation"]
        
        for context in contexts:
            error = ValueError("Test error")
            http_exc = handle_exception(error, context)
            
            assert http_exc.detail["details"]["context"] == context

    def test_error_logging_integration(self):
        """Test that errors are logged appropriately."""
        # This test would ideally capture log output, but for simplicity
        # we just ensure no exceptions are raised during error handling
        
        test_exceptions = [
            ValueError("Test validation error"),
            FileNotFoundError("Test file error"),
            RuntimeError("Test runtime error"),
            TypeError("Test type error")
        ]
        
        for exc in test_exceptions:
            try:
                http_exc = handle_exception(exc, "test_logging")
                assert isinstance(http_exc, HTTPException)
            except Exception as e:
                pytest.fail(f"Error handling failed for {type(exc).__name__}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])