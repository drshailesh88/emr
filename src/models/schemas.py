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


class Vitals(BaseModel):
    """Vitals record schema."""
    id: Optional[int] = None
    patient_id: int
    visit_id: Optional[int] = None
    recorded_at: Optional[datetime] = None

    # Blood Pressure
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None

    # Other vitals
    pulse: Optional[int] = None
    temperature: Optional[float] = None
    spo2: Optional[int] = None
    respiratory_rate: Optional[int] = None

    # Anthropometry
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None

    # Blood Sugar
    blood_sugar: Optional[float] = None
    sugar_type: Optional[str] = None  # FBS, RBS, PPBS

    notes: Optional[str] = None


class RAGDocument(BaseModel):
    """Document for RAG indexing."""
    id: str
    patient_id: int
    doc_type: str  # visit, investigation, procedure
    content: str
    metadata: dict = Field(default_factory=dict)
