"""Security services for DocAssist EMR.

This module provides comprehensive security features:
- Input validation and sanitization
- Data protection and audit logging
- Authentication and authorization
- Secure file handling
- SQL injection prevention
- XSS protection

Usage:
    from src.services.security import get_validator, get_protection_service, get_auth_manager

    # Input validation
    validator = get_validator()
    name = validator.validate_patient_name(user_input)

    # Audit logging
    protection = get_protection_service()
    protection.log_action(AuditAction.VIEW_PATIENT, patient_id=123)

    # Authentication
    auth = get_auth_manager()
    success, user, msg = auth.authenticate(username, password)
"""

from .input_validator import (
    InputValidator,
    ValidationError,
    get_validator
)

from .data_protection import (
    DataProtectionService,
    AuditAction,
    AuditLogEntry,
    get_protection_service
)

from .auth_manager import (
    AuthenticationManager,
    UserRole,
    AuthMethod,
    User,
    get_auth_manager
)

__all__ = [
    # Input validation
    "InputValidator",
    "ValidationError",
    "get_validator",

    # Data protection
    "DataProtectionService",
    "AuditAction",
    "AuditLogEntry",
    "get_protection_service",

    # Authentication
    "AuthenticationManager",
    "UserRole",
    "AuthMethod",
    "User",
    "get_auth_manager",
]
