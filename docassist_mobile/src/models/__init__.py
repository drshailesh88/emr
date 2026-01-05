"""DocAssist Mobile - Data models.

Shares schemas with desktop app for consistency.
"""

# Import from desktop if available, otherwise define minimal versions
try:
    from src.models.schemas import Patient, Visit, Investigation, Procedure
except ImportError:
    # Fallback: define minimal models for mobile
    from .schemas import Patient, Visit, Investigation, Procedure

__all__ = ['Patient', 'Visit', 'Investigation', 'Procedure']
