"""
Mobile Data Schemas - Pydantic models for mobile app.

These models are compatible with desktop schemas but optimized for mobile use.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Patient(BaseModel):
    """Patient model for mobile display."""
    id: int
    uhid: str
    name: str
    age: Optional[int] = None
    gender: str = "O"  # M, F, O
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class Visit(BaseModel):
    """Visit model for mobile display."""
    id: int
    patient_id: int
    visit_date: date
    chief_complaint: Optional[str] = None
    clinical_notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class Investigation(BaseModel):
    """Investigation/Lab result model for mobile display."""
    id: int
    patient_id: int
    test_name: str
    result: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    test_date: date
    is_abnormal: bool = False

    class Config:
        from_attributes = True


class Procedure(BaseModel):
    """Procedure model for mobile display."""
    id: int
    patient_id: int
    procedure_name: str
    details: Optional[str] = None
    procedure_date: date
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class Appointment(BaseModel):
    """Appointment model for mobile display."""
    id: int
    patient_id: int
    appointment_time: datetime
    reason: Optional[str] = None
    status: str = "scheduled"  # scheduled, completed, cancelled

    class Config:
        from_attributes = True


class Medication(BaseModel):
    """Medication in a prescription."""
    drug_name: str
    strength: Optional[str] = None
    form: Optional[str] = None  # tablet, capsule, syrup, etc.
    dose: Optional[str] = None
    frequency: Optional[str] = None  # OD, BD, TDS, etc.
    duration: Optional[str] = None
    instructions: Optional[str] = None


class Prescription(BaseModel):
    """Prescription model."""
    diagnosis: List[str] = []
    medications: List[Medication] = []
    investigations: List[str] = []
    advice: List[str] = []
    follow_up: Optional[str] = None
    red_flags: List[str] = []


class SyncMetadata(BaseModel):
    """Sync metadata for tracking."""
    last_sync: Optional[datetime] = None
    backup_id: Optional[str] = None
    patient_count: int = 0
    visit_count: int = 0
    device_id: Optional[str] = None


class UserCredentials(BaseModel):
    """User credentials (not stored, only used in memory)."""
    email: str
    token: str
    encryption_key_hash: str  # Hash only, not the actual key
