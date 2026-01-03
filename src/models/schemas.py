"""Pydantic models for data validation."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class Patient(BaseModel):
    """Patient record schema."""
    id: Optional[int] = None
    uhid: Optional[str] = None
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None  # M/F/O
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None


class Medication(BaseModel):
    """Single medication in prescription."""
    drug_name: str
    strength: str = ""
    form: str = "tablet"  # tablet, capsule, syrup, injection, etc.
    dose: str = "1"
    frequency: str = "OD"  # OD, BD, TDS, QID, etc.
    duration: str = ""
    instructions: str = ""  # before meals, after meals, etc.


class Prescription(BaseModel):
    """Structured prescription output from LLM."""
    diagnosis: List[str] = Field(default_factory=list)
    medications: List[Medication] = Field(default_factory=list)
    investigations: List[str] = Field(default_factory=list)
    advice: List[str] = Field(default_factory=list)
    follow_up: str = ""
    red_flags: List[str] = Field(default_factory=list)


class Visit(BaseModel):
    """Patient visit record."""
    id: Optional[int] = None
    patient_id: int
    visit_date: Optional[date] = None
    chief_complaint: str = ""
    clinical_notes: str = ""
    diagnosis: str = ""
    prescription_json: Optional[str] = None
    created_at: Optional[datetime] = None


class Investigation(BaseModel):
    """Lab investigation record."""
    id: Optional[int] = None
    patient_id: int
    test_name: str
    result: str = ""
    unit: str = ""
    reference_range: str = ""
    test_date: Optional[date] = None
    is_abnormal: bool = False


class Procedure(BaseModel):
    """Medical procedure record."""
    id: Optional[int] = None
    patient_id: int
    procedure_name: str
    details: str = ""
    procedure_date: Optional[date] = None
    notes: str = ""


class RAGDocument(BaseModel):
    """Document for RAG indexing."""
    id: str
    patient_id: int
    doc_type: str  # visit, investigation, procedure
    content: str
    metadata: dict = Field(default_factory=dict)


# ============== HOSPITAL/MULTI-USER MODELS ==============

class Doctor(BaseModel):
    """Doctor/Staff record for multi-user hospital setup."""
    id: Optional[int] = None
    name: str
    specialty: Optional[str] = None  # nephrology, cardiology, etc.
    department: Optional[str] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None  # Consultant, Resident, Fellow
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class Consultation(BaseModel):
    """Inter-department consultation record."""
    id: Optional[int] = None
    patient_id: int
    requesting_doctor_id: Optional[int] = None
    consulting_doctor_id: Optional[int] = None
    consulting_specialty: str
    consult_date: Optional[date] = None
    reason_for_referral: str = ""
    clinical_question: str = ""
    findings: str = ""
    impression: str = ""
    recommendations: str = ""
    follow_up_needed: bool = False
    follow_up_date: Optional[date] = None
    created_at: Optional[datetime] = None


class CareTeamMember(BaseModel):
    """Track which doctors are involved in a patient's care."""
    id: Optional[int] = None
    patient_id: int
    doctor_id: int
    role: str  # primary, consultant, referred_by, covering
    specialty: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    added_by: Optional[int] = None
    created_at: Optional[datetime] = None


class AuditLogEntry(BaseModel):
    """Audit trail for all data access."""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    user_id: int
    user_name: str
    user_role: str
    action: str  # VIEW, CREATE, UPDATE, DELETE, EXPORT, PRINT
    resource_type: str  # patient, consultation, prescription
    resource_id: Optional[int] = None
    patient_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    workstation_id: Optional[str] = None


# ============== PATIENT SNAPSHOT (Computed Summary) ==============

class PatientSnapshot(BaseModel):
    """Pre-computed patient summary for fast lookups and context building."""
    patient_id: int
    uhid: str
    demographics: str  # "Ram Lal, 65M"

    # Structured clinical data
    active_problems: List[str] = Field(default_factory=list)
    current_medications: List[Medication] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)

    # Key metrics (latest values)
    key_labs: dict = Field(default_factory=dict)  # {"creatinine": {"value": "1.2", "date": "2024-12-01"}}
    vitals: dict = Field(default_factory=dict)  # {"BP": "130/80", "Weight": "72kg"}

    # Critical flags
    blood_group: Optional[str] = None
    code_status: str = "FULL"  # FULL, DNR, DNI
    on_anticoagulation: bool = False
    anticoag_drug: Optional[str] = None

    # Timeline
    last_visit_date: Optional[date] = None
    major_events: List[str] = Field(default_factory=list)  # ["PCI to LAD - 2023-05-10"]

    # Metadata
    last_updated: Optional[datetime] = None


# ============== SAFETY MODELS ==============

class SafetyAlert(BaseModel):
    """Safety alert from prescription validation."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # allergy, interaction, dose, contraindication
    message: str
    action: str  # BLOCK, WARN, INFO
    details: Optional[str] = None


class PrescriptionDraft(BaseModel):
    """AI-generated prescription draft requiring confirmation."""
    content: Prescription
    raw_ai_output: str
    status: str = "DRAFT"  # DRAFT, CONFIRMED, REJECTED
    safety_alerts: List[SafetyAlert] = Field(default_factory=list)
    generated_at: Optional[datetime] = None
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
