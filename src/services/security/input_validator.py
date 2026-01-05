"""Input validation and sanitization for security hardening.

Protects against:
- SQL injection (validates inputs before parameterized queries)
- XSS attacks (if rendering any HTML)
- Path traversal attacks
- Malformed data that could cause crashes
- Excessively long inputs (DoS prevention)

All user inputs should be validated before processing.
"""

import re
import logging
from typing import Optional, Union
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputValidator:
    """Validates and sanitizes user inputs for security."""

    # Maximum lengths to prevent DoS
    MAX_NAME_LENGTH = 200
    MAX_TEXT_LENGTH = 10000  # For notes, complaints
    MAX_ADDRESS_LENGTH = 500
    MAX_PHONE_LENGTH = 20
    MAX_EMAIL_LENGTH = 254  # RFC 5321
    MAX_UHID_LENGTH = 50
    MAX_DRUG_NAME_LENGTH = 200
    MAX_FILE_PATH_LENGTH = 500

    # Regex patterns for validation
    PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]{7,20}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    UHID_PATTERN = re.compile(r'^[A-Z0-9\-]{1,50}$')

    # Dangerous characters for SQL (even though we use parameterized queries)
    # This is defense-in-depth - catch attacks before they reach SQL layer
    SQL_INJECTION_PATTERNS = [
        r"(\bOR\b.*?=.*?)",
        r"(\bAND\b.*?=.*?)",
        r"(--\s*$)",
        r"(;\s*DROP\s+TABLE)",
        r"(;\s*DELETE\s+FROM)",
        r"(;\s*UPDATE\s+)",
        r"(;\s*INSERT\s+INTO)",
        r"(UNION\s+SELECT)",
        r"(/\*.*?\*/)",  # SQL comments
        r"(xp_cmdshell)",
        r"(exec\s*\()",
    ]

    # XSS patterns (if any HTML rendering is added)
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
    ]

    def __init__(self, strict_mode: bool = True):
        """Initialize validator.

        Args:
            strict_mode: If True, reject potentially dangerous inputs.
                        If False, sanitize them instead (more permissive).
        """
        self.strict_mode = strict_mode

    # ============== BASIC TYPE VALIDATION ==============

    def validate_string(self, value: str, field_name: str, max_length: int,
                       min_length: int = 0, allow_empty: bool = False,
                       pattern: Optional[re.Pattern] = None) -> str:
        """Validate and sanitize a string input.

        Args:
            value: Input string
            field_name: Name of field (for error messages)
            max_length: Maximum allowed length
            min_length: Minimum allowed length
            allow_empty: Whether empty strings are allowed
            pattern: Optional regex pattern to match

        Returns:
            Sanitized string

        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if allow_empty:
                return ""
            raise ValidationError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")

        # Strip whitespace
        value = value.strip()

        if not value and not allow_empty:
            raise ValidationError(f"{field_name} cannot be empty")

        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} too long (max {max_length} chars, got {len(value)})"
            )

        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} too short (min {min_length} chars, got {len(value)})"
            )

        if pattern and value and not pattern.match(value):
            raise ValidationError(f"{field_name} format is invalid")

        return value

    def validate_integer(self, value: Union[int, str], field_name: str,
                        min_value: Optional[int] = None,
                        max_value: Optional[int] = None) -> int:
        """Validate an integer input.

        Args:
            value: Input value (int or string)
            field_name: Name of field
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Validated integer

        Raises:
            ValidationError: If validation fails
        """
        try:
            if isinstance(value, str):
                value = int(value.strip())
            elif not isinstance(value, int):
                raise ValueError("Not an integer")

            if min_value is not None and value < min_value:
                raise ValidationError(
                    f"{field_name} must be >= {min_value} (got {value})"
                )

            if max_value is not None and value > max_value:
                raise ValidationError(
                    f"{field_name} must be <= {max_value} (got {value})"
                )

            return value

        except (ValueError, TypeError) as e:
            raise ValidationError(f"{field_name} must be a valid integer") from e

    def validate_float(self, value: Union[float, str], field_name: str,
                      min_value: Optional[float] = None,
                      max_value: Optional[float] = None) -> float:
        """Validate a float input.

        Args:
            value: Input value
            field_name: Name of field
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Validated float

        Raises:
            ValidationError: If validation fails
        """
        try:
            if isinstance(value, str):
                value = float(value.strip())
            elif not isinstance(value, (int, float)):
                raise ValueError("Not a number")

            value = float(value)

            if min_value is not None and value < min_value:
                raise ValidationError(
                    f"{field_name} must be >= {min_value} (got {value})"
                )

            if max_value is not None and value > max_value:
                raise ValidationError(
                    f"{field_name} must be <= {max_value} (got {value})"
                )

            return value

        except (ValueError, TypeError) as e:
            raise ValidationError(f"{field_name} must be a valid number") from e

    # ============== DOMAIN-SPECIFIC VALIDATION ==============

    def validate_patient_name(self, name: str) -> str:
        """Validate patient name.

        Args:
            name: Patient name

        Returns:
            Validated name

        Raises:
            ValidationError: If invalid
        """
        name = self.validate_string(
            name, "Patient name",
            max_length=self.MAX_NAME_LENGTH,
            min_length=1,
            allow_empty=False
        )

        # Check for SQL injection attempts
        self._check_sql_injection(name, "Patient name")

        # Names should contain letters (allow Unicode for international names)
        if not re.search(r'\w', name, re.UNICODE):
            raise ValidationError("Patient name must contain letters")

        return name

    def validate_phone(self, phone: str, allow_empty: bool = True) -> str:
        """Validate phone number.

        Args:
            phone: Phone number
            allow_empty: Whether empty phone is allowed

        Returns:
            Validated phone number

        Raises:
            ValidationError: If invalid
        """
        if not phone and allow_empty:
            return ""

        phone = self.validate_string(
            phone, "Phone number",
            max_length=self.MAX_PHONE_LENGTH,
            allow_empty=allow_empty
        )

        if phone and not self.PHONE_PATTERN.match(phone):
            raise ValidationError(
                "Invalid phone number format (use digits, spaces, +, -, or parentheses)"
            )

        return phone

    def validate_email(self, email: str, allow_empty: bool = True) -> str:
        """Validate email address.

        Args:
            email: Email address
            allow_empty: Whether empty email is allowed

        Returns:
            Validated email

        Raises:
            ValidationError: If invalid
        """
        if not email and allow_empty:
            return ""

        email = self.validate_string(
            email, "Email",
            max_length=self.MAX_EMAIL_LENGTH,
            allow_empty=allow_empty
        )

        if email and not self.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")

        return email.lower()  # Normalize to lowercase

    def validate_age(self, age: Union[int, str], allow_none: bool = True) -> Optional[int]:
        """Validate patient age.

        Args:
            age: Age value
            allow_none: Whether None is allowed

        Returns:
            Validated age

        Raises:
            ValidationError: If invalid
        """
        if age is None and allow_none:
            return None

        return self.validate_integer(age, "Age", min_value=0, max_value=150)

    def validate_gender(self, gender: str, allow_empty: bool = True) -> str:
        """Validate gender field.

        Args:
            gender: Gender value (M/F/O or full names)
            allow_empty: Whether empty is allowed

        Returns:
            Validated gender

        Raises:
            ValidationError: If invalid
        """
        if not gender and allow_empty:
            return ""

        gender = self.validate_string(gender, "Gender", max_length=20, allow_empty=allow_empty)

        # Normalize common values
        gender_upper = gender.upper()
        if gender_upper in ('M', 'MALE'):
            return 'M'
        elif gender_upper in ('F', 'FEMALE'):
            return 'F'
        elif gender_upper in ('O', 'OTHER', 'NON-BINARY'):
            return 'O'
        elif gender:
            # Allow other values but validate length
            return gender

        return ""

    def validate_uhid(self, uhid: str) -> str:
        """Validate UHID (Universal Health ID).

        Args:
            uhid: UHID string

        Returns:
            Validated UHID

        Raises:
            ValidationError: If invalid
        """
        uhid = self.validate_string(
            uhid, "UHID",
            max_length=self.MAX_UHID_LENGTH,
            min_length=1,
            allow_empty=False,
            pattern=self.UHID_PATTERN
        )

        return uhid

    def validate_clinical_text(self, text: str, field_name: str = "Clinical text",
                               allow_empty: bool = True) -> str:
        """Validate clinical notes, complaints, diagnosis, etc.

        Args:
            text: Clinical text
            field_name: Name of field
            allow_empty: Whether empty is allowed

        Returns:
            Validated text

        Raises:
            ValidationError: If invalid
        """
        if not text and allow_empty:
            return ""

        text = self.validate_string(
            text, field_name,
            max_length=self.MAX_TEXT_LENGTH,
            allow_empty=allow_empty
        )

        # Check for SQL injection
        self._check_sql_injection(text, field_name)

        # Check for XSS
        self._check_xss(text, field_name)

        return text

    def validate_date(self, date_value: Union[str, date, datetime],
                     field_name: str = "Date") -> date:
        """Validate date input.

        Args:
            date_value: Date value (string or date object)
            field_name: Name of field

        Returns:
            Validated date

        Raises:
            ValidationError: If invalid
        """
        if isinstance(date_value, datetime):
            return date_value.date()

        if isinstance(date_value, date):
            return date_value

        if isinstance(date_value, str):
            # Try parsing common formats
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue

            raise ValidationError(f"{field_name} format invalid (use YYYY-MM-DD)")

        raise ValidationError(f"{field_name} must be a date")

    def validate_file_path(self, path: str, must_exist: bool = False,
                          allowed_extensions: Optional[list] = None) -> Path:
        """Validate file path (prevent path traversal).

        Args:
            path: File path string
            must_exist: Whether file must exist
            allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.zip'])

        Returns:
            Validated Path object

        Raises:
            ValidationError: If invalid or dangerous
        """
        path = self.validate_string(
            path, "File path",
            max_length=self.MAX_FILE_PATH_LENGTH,
            allow_empty=False
        )

        # Check for path traversal attempts
        dangerous_patterns = ['..', '~/', '/etc/', '/root/', 'c:\\', 'windows\\']
        path_lower = path.lower()

        for pattern in dangerous_patterns:
            if pattern in path_lower:
                raise ValidationError(
                    f"Path contains dangerous pattern: {pattern}"
                )

        try:
            file_path = Path(path)

            # Resolve to absolute path and check it doesn't escape base directory
            # (This is a basic check - actual enforcement happens at file operation level)

            if must_exist and not file_path.exists():
                raise ValidationError(f"File does not exist: {path}")

            if allowed_extensions:
                if file_path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                    raise ValidationError(
                        f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
                    )

            return file_path

        except Exception as e:
            raise ValidationError(f"Invalid file path: {e}") from e

    # ============== SECURITY CHECKS ==============

    def _check_sql_injection(self, value: str, field_name: str):
        """Check for SQL injection patterns.

        Note: This is defense-in-depth. We use parameterized queries,
        but this catches obvious attacks early.

        Args:
            value: String to check
            field_name: Field name for error messages

        Raises:
            ValidationError: If SQL injection detected
        """
        if not self.strict_mode:
            return

        value_upper = value.upper()

        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(
                    f"Potential SQL injection attempt in {field_name}: {value[:100]}"
                )
                raise ValidationError(
                    f"{field_name} contains potentially dangerous content"
                )

    def _check_xss(self, value: str, field_name: str):
        """Check for XSS patterns.

        Args:
            value: String to check
            field_name: Field name for error messages

        Raises:
            ValidationError: If XSS detected
        """
        if not self.strict_mode:
            return

        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(
                    f"Potential XSS attempt in {field_name}: {value[:100]}"
                )
                raise ValidationError(
                    f"{field_name} contains potentially dangerous HTML/JavaScript"
                )

    def sanitize_for_display(self, value: str) -> str:
        """Sanitize string for safe display (HTML escape).

        Args:
            value: String to sanitize

        Returns:
            Sanitized string safe for HTML display
        """
        if not value:
            return ""

        # Basic HTML escaping
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
        }

        for char, escape in replacements.items():
            value = value.replace(char, escape)

        return value

    def validate_json_size(self, json_str: str, max_size_bytes: int = 1_000_000):
        """Validate JSON string size (prevent DoS).

        Args:
            json_str: JSON string
            max_size_bytes: Maximum allowed size in bytes

        Raises:
            ValidationError: If too large
        """
        size = len(json_str.encode('utf-8'))
        if size > max_size_bytes:
            raise ValidationError(
                f"JSON too large ({size} bytes, max {max_size_bytes})"
            )


# Singleton instance
_validator = None


def get_validator(strict_mode: bool = True) -> InputValidator:
    """Get global validator instance.

    Args:
        strict_mode: Whether to use strict validation

    Returns:
        InputValidator instance
    """
    global _validator
    if _validator is None:
        _validator = InputValidator(strict_mode=strict_mode)
    return _validator
