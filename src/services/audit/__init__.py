"""Medicolegal fortress - Audit, consent, and incident management."""
from .audit_logger import AuditLogger, AuditEvent, AuditAction
from .consent_manager import ConsentManager, ConsentType, ConsentRecord
from .incident_reporter import IncidentReporter, IncidentSeverity, IncidentReport

__all__ = [
    'AuditLogger',
    'AuditEvent',
    'AuditAction',
    'ConsentManager',
    'ConsentType',
    'ConsentRecord',
    'IncidentReporter',
    'IncidentSeverity',
    'IncidentReport',
]
