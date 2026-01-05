"""Data Validation Security Tests.

Tests the input validation module to ensure all user inputs are properly validated
and sanitized before processing.

Tests include:
- Phone number validation
- Email validation
- Clinical text validation
- File path validation
- SQL injection pattern detection
- XSS pattern detection
"""

import pytest
from datetime import date, datetime
from pathlib import Path

from src.services.security.input_validator import (
    InputValidator,
    ValidationError,
    get_validator
)


class TestBasicValidation:
    """Test basic validation functions."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return InputValidator(strict_mode=True)

    def test_validate_string_normal(self, validator):
        """Test normal string validation."""
        result = validator.validate_string("John Doe", "Name", max_length=100)
        assert result == "John Doe"

    def test_validate_string_strips_whitespace(self, validator):
        """Test that whitespace is stripped."""
        result = validator.validate_string("  John Doe  ", "Name", max_length=100)
        assert result == "John Doe"

    def test_validate_string_too_long(self, validator):
        """Test that overly long strings are rejected."""
        with pytest.raises(ValidationError, match="too long"):
            validator.validate_string("a" * 1000, "Name", max_length=100)

    def test_validate_string_too_short(self, validator):
        """Test that strings below minimum length are rejected."""
        with pytest.raises(ValidationError, match="too short"):
            validator.validate_string("a", "Name", max_length=100, min_length=5)

    def test_validate_string_empty_not_allowed(self, validator):
        """Test that empty strings are rejected when not allowed."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validator.validate_string("", "Name", max_length=100, allow_empty=False)

    def test_validate_string_empty_allowed(self, validator):
        """Test that empty strings are allowed when permitted."""
        result = validator.validate_string("", "Name", max_length=100, allow_empty=True)
        assert result == ""

    def test_validate_integer_normal(self, validator):
        """Test integer validation."""
        result = validator.validate_integer(42, "Age", min_value=0, max_value=150)
        assert result == 42

    def test_validate_integer_from_string(self, validator):
        """Test integer validation from string."""
        result = validator.validate_integer("42", "Age", min_value=0, max_value=150)
        assert result == 42

    def test_validate_integer_out_of_range(self, validator):
        """Test that out of range integers are rejected."""
        with pytest.raises(ValidationError, match="must be <="):
            validator.validate_integer(200, "Age", min_value=0, max_value=150)

        with pytest.raises(ValidationError, match="must be >="):
            validator.validate_integer(-5, "Age", min_value=0, max_value=150)

    def test_validate_integer_invalid_string(self, validator):
        """Test that invalid integer strings are rejected."""
        with pytest.raises(ValidationError, match="valid integer"):
            validator.validate_integer("not a number", "Age")

    def test_validate_float_normal(self, validator):
        """Test float validation."""
        result = validator.validate_float(3.14, "Value", min_value=0, max_value=10)
        assert result == 3.14

    def test_validate_float_from_string(self, validator):
        """Test float validation from string."""
        result = validator.validate_float("3.14", "Value", min_value=0, max_value=10)
        assert result == 3.14


class TestDomainSpecificValidation:
    """Test domain-specific validation (medical data)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return InputValidator(strict_mode=True)

    def test_validate_patient_name_normal(self, validator):
        """Test normal patient name."""
        result = validator.validate_patient_name("John Doe")
        assert result == "John Doe"

    def test_validate_patient_name_unicode(self, validator):
        """Test Unicode names (Indian names, etc)."""
        names = [
            "राम लाल",  # Hindi
            "محمد",  # Arabic
            "José García",  # Spanish
            "李明",  # Chinese
        ]

        for name in names:
            result = validator.validate_patient_name(name)
            assert result == name

    def test_validate_patient_name_too_long(self, validator):
        """Test that overly long names are rejected."""
        with pytest.raises(ValidationError):
            validator.validate_patient_name("a" * 300)

    def test_validate_patient_name_empty(self, validator):
        """Test that empty names are rejected."""
        with pytest.raises(ValidationError):
            validator.validate_patient_name("")

    def test_validate_phone_normal(self, validator):
        """Test normal phone numbers."""
        valid_phones = [
            "1234567890",
            "+91 98765 43210",
            "(555) 123-4567",
            "555-1234",
        ]

        for phone in valid_phones:
            result = validator.validate_phone(phone, allow_empty=False)
            assert result == phone

    def test_validate_phone_empty_when_allowed(self, validator):
        """Test empty phone when allowed."""
        result = validator.validate_phone("", allow_empty=True)
        assert result == ""

    def test_validate_phone_invalid_format(self, validator):
        """Test that invalid phone formats are rejected."""
        invalid_phones = [
            "abc123",  # Letters
            "123",  # Too short
            "12345678901234567890123",  # Too long
            "phone@example.com",  # Not a phone
        ]

        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                validator.validate_phone(phone, allow_empty=False)

    def test_validate_email_normal(self, validator):
        """Test normal email addresses."""
        valid_emails = [
            "user@example.com",
            "doctor.name@clinic.co.in",
            "test+tag@domain.com",
        ]

        for email in valid_emails:
            result = validator.validate_email(email, allow_empty=False)
            assert result == email.lower()

    def test_validate_email_normalizes_case(self, validator):
        """Test that emails are normalized to lowercase."""
        result = validator.validate_email("USER@EXAMPLE.COM", allow_empty=False)
        assert result == "user@example.com"

    def test_validate_email_invalid_format(self, validator):
        """Test that invalid emails are rejected."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user space@example.com",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validator.validate_email(email, allow_empty=False)

    def test_validate_age_normal(self, validator):
        """Test normal age validation."""
        assert validator.validate_age(30) == 30
        assert validator.validate_age("45") == 45
        assert validator.validate_age(None, allow_none=True) is None

    def test_validate_age_out_of_range(self, validator):
        """Test that invalid ages are rejected."""
        with pytest.raises(ValidationError):
            validator.validate_age(-5)  # Negative

        with pytest.raises(ValidationError):
            validator.validate_age(200)  # Too high

    def test_validate_gender_normal(self, validator):
        """Test gender validation."""
        assert validator.validate_gender("M") == "M"
        assert validator.validate_gender("F") == "F"
        assert validator.validate_gender("O") == "O"

    def test_validate_gender_normalizes(self, validator):
        """Test that gender values are normalized."""
        assert validator.validate_gender("male") == "M"
        assert validator.validate_gender("FEMALE") == "F"
        assert validator.validate_gender("other") == "O"

    def test_validate_uhid_normal(self, validator):
        """Test UHID validation."""
        valid_uhids = [
            "EMR-2024-0001",
            "CLINIC-12345",
            "PT123",
        ]

        for uhid in valid_uhids:
            result = validator.validate_uhid(uhid)
            assert result == uhid

    def test_validate_uhid_invalid(self, validator):
        """Test that invalid UHIDs are rejected."""
        invalid_uhids = [
            "",  # Empty
            "uhid with spaces",  # Spaces
            "uhid@special",  # Special chars
            "a" * 100,  # Too long
        ]

        for uhid in invalid_uhids:
            with pytest.raises(ValidationError):
                validator.validate_uhid(uhid)

    def test_validate_date_from_string(self, validator):
        """Test date validation from string."""
        result = validator.validate_date("2024-01-15")
        assert result == date(2024, 1, 15)

        result = validator.validate_date("15-01-2024")
        assert result == date(2024, 1, 15)

    def test_validate_date_from_date_object(self, validator):
        """Test date validation from date object."""
        input_date = date(2024, 1, 15)
        result = validator.validate_date(input_date)
        assert result == input_date

    def test_validate_date_from_datetime(self, validator):
        """Test date validation from datetime object."""
        input_datetime = datetime(2024, 1, 15, 10, 30)
        result = validator.validate_date(input_datetime)
        assert result == date(2024, 1, 15)

    def test_validate_date_invalid_format(self, validator):
        """Test that invalid date formats are rejected."""
        with pytest.raises(ValidationError):
            validator.validate_date("not a date")


class TestSQLInjectionDetection:
    """Test SQL injection pattern detection."""

    @pytest.fixture
    def validator(self):
        """Create validator in strict mode."""
        return InputValidator(strict_mode=True)

    def test_detect_sql_injection_or_pattern(self, validator):
        """Test detection of OR-based SQL injection."""
        with pytest.raises(ValidationError, match="dangerous"):
            validator.validate_clinical_text("Test' OR '1'='1", allow_empty=False)

    def test_detect_sql_injection_drop_table(self, validator):
        """Test detection of DROP TABLE."""
        with pytest.raises(ValidationError, match="dangerous"):
            validator.validate_clinical_text("'; DROP TABLE patients; --", allow_empty=False)

    def test_detect_sql_injection_union_select(self, validator):
        """Test detection of UNION SELECT."""
        with pytest.raises(ValidationError, match="dangerous"):
            validator.validate_clinical_text("' UNION SELECT * FROM users --", allow_empty=False)

    def test_detect_sql_injection_comments(self, validator):
        """Test detection of SQL comments."""
        with pytest.raises(ValidationError, match="dangerous"):
            validator.validate_clinical_text("Test /* comment */ data", allow_empty=False)

    def test_normal_clinical_text_allowed(self, validator):
        """Test that normal clinical text is allowed."""
        normal_texts = [
            "Patient presents with chest pain for 2 days",
            "History of diabetes and hypertension",
            "Prescribed Metformin 500mg twice daily",
        ]

        for text in normal_texts:
            result = validator.validate_clinical_text(text)
            assert result == text

    def test_strict_mode_vs_permissive(self):
        """Test difference between strict and permissive modes."""
        strict = InputValidator(strict_mode=True)
        permissive = InputValidator(strict_mode=False)

        malicious = "Test' OR '1'='1"

        # Strict mode should reject
        with pytest.raises(ValidationError):
            strict.validate_clinical_text(malicious)

        # Permissive mode should allow (for backward compatibility)
        result = permissive.validate_clinical_text(malicious)
        assert result == malicious


class TestXSSDetection:
    """Test XSS pattern detection."""

    @pytest.fixture
    def validator(self):
        """Create validator in strict mode."""
        return InputValidator(strict_mode=True)

    def test_detect_xss_script_tags(self, validator):
        """Test detection of script tags."""
        with pytest.raises(ValidationError, match="dangerous"):
            validator.validate_clinical_text("<script>alert('XSS')</script>")

    def test_detect_xss_javascript_protocol(self, validator):
        """Test detection of javascript: protocol."""
        with pytest.raises(ValidationError, match="dangerous"):
            validator.validate_clinical_text("javascript:alert('XSS')")

    def test_detect_xss_event_handlers(self, validator):
        """Test detection of event handlers."""
        xss_patterns = [
            "<img onerror='alert(1)'>",
            "<body onload='alert(1)'>",
            "<div onclick='alert(1)'>",
        ]

        for pattern in xss_patterns:
            with pytest.raises(ValidationError):
                validator.validate_clinical_text(pattern)

    def test_sanitize_for_display(self, validator):
        """Test HTML sanitization."""
        dangerous = "<script>alert('XSS')</script>"
        safe = validator.sanitize_for_display(dangerous)

        assert "<" not in safe or "&lt;" in safe
        assert ">" not in safe or "&gt;" in safe


class TestFilePathValidation:
    """Test file path validation (prevent path traversal)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return InputValidator(strict_mode=True)

    def test_validate_file_path_normal(self, validator):
        """Test normal file path."""
        result = validator.validate_file_path("/home/user/data/file.pdf", must_exist=False)
        assert isinstance(result, Path)

    def test_validate_file_path_detect_traversal(self, validator):
        """Test detection of path traversal attempts."""
        dangerous_paths = [
            "../../../etc/passwd",
            "~/important.file",
            "/etc/shadow",
            "C:\\Windows\\System32",
        ]

        for path in dangerous_paths:
            with pytest.raises(ValidationError, match="dangerous"):
                validator.validate_file_path(path)

    def test_validate_file_path_extension_check(self, validator):
        """Test file extension validation."""
        # Should pass
        result = validator.validate_file_path(
            "/home/user/file.pdf",
            must_exist=False,
            allowed_extensions=['.pdf', '.zip']
        )

        # Should fail
        with pytest.raises(ValidationError, match="Invalid file extension"):
            validator.validate_file_path(
                "/home/user/file.exe",
                must_exist=False,
                allowed_extensions=['.pdf', '.zip']
            )


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return InputValidator(strict_mode=True)

    def test_extremely_long_input(self, validator):
        """Test handling of extremely long inputs."""
        very_long_text = "a" * 1_000_000

        with pytest.raises(ValidationError):
            validator.validate_clinical_text(very_long_text)

    def test_null_bytes_in_input(self, validator):
        """Test handling of null bytes."""
        text_with_null = "Test\x00data"

        # Should either reject or handle gracefully
        try:
            result = validator.validate_clinical_text(text_with_null)
            # If accepted, null bytes should be preserved or removed
            assert isinstance(result, str)
        except ValidationError:
            # Rejecting is also acceptable
            pass

    def test_special_unicode_characters(self, validator):
        """Test handling of special Unicode characters."""
        special_chars = [
            "Test\u200b\u200cdata",  # Zero-width characters
            "Test\ufeffdata",  # BOM
            "Test\u202edata",  # Right-to-left override
        ]

        for text in special_chars:
            # Should handle gracefully
            result = validator.validate_clinical_text(text)
            assert isinstance(result, str)

    def test_json_size_validation(self, validator):
        """Test JSON size validation."""
        small_json = '{"key": "value"}'
        validator.validate_json_size(small_json, max_size_bytes=1000)

        large_json = '{"key": "' + "x" * 2_000_000 + '"}'
        with pytest.raises(ValidationError, match="too large"):
            validator.validate_json_size(large_json, max_size_bytes=1_000_000)


class TestValidatorSingleton:
    """Test validator singleton pattern."""

    def test_get_validator_returns_singleton(self):
        """Test that get_validator returns the same instance."""
        v1 = get_validator()
        v2 = get_validator()
        assert v1 is v2

    def test_get_validator_with_strict_mode(self):
        """Test validator with different modes."""
        strict = get_validator(strict_mode=True)
        permissive = get_validator(strict_mode=False)

        # Both should work (though they might be the same instance)
        assert isinstance(strict, InputValidator)
        assert isinstance(permissive, InputValidator)
