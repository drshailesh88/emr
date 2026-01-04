"""Digital consent collection and management.

This module handles:
- Treatment consent collection
- Procedure-specific consents
- Data sharing consents (research, referrals)
- Consent withdrawal and audit trail
- Digital signature capture
"""
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum


class ConsentType(Enum):
    """Types of medical consents."""
    # Treatment consents
    GENERAL_TREATMENT = "general_treatment"
    PROCEDURE_SPECIFIC = "procedure_specific"
    SURGERY = "surgery"
    ANESTHESIA = "anesthesia"
    BLOOD_TRANSFUSION = "blood_transfusion"
    HIGH_RISK_MEDICATION = "high_risk_medication"

    # Investigation consents
    INVASIVE_PROCEDURE = "invasive_procedure"
    CONTRAST_ADMINISTRATION = "contrast_administration"
    BIOPSY = "biopsy"

    # Data consents
    DATA_COLLECTION = "data_collection"
    DATA_SHARING_REFERRAL = "data_sharing_referral"
    DATA_SHARING_INSURANCE = "data_sharing_insurance"
    DATA_SHARING_RESEARCH = "data_sharing_research"
    TELEMEDICINE = "telemedicine"

    # Communication consents
    WHATSAPP_COMMUNICATION = "whatsapp_communication"
    SMS_REMINDERS = "sms_reminders"
    EMAIL_COMMUNICATION = "email_communication"

    # Special consents
    AGAINST_MEDICAL_ADVICE = "against_medical_advice"
    DISCHARGE_AGAINST_ADVICE = "discharge_against_advice"
    REFUSAL_OF_TREATMENT = "refusal_of_treatment"
    DO_NOT_RESUSCITATE = "do_not_resuscitate"


class ConsentStatus(Enum):
    """Status of a consent."""
    PENDING = "pending"
    OBTAINED = "obtained"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


@dataclass
class ConsentTemplate:
    """Template for a consent form."""
    template_id: str
    consent_type: ConsentType
    title: str
    title_hindi: str
    description: str
    description_hindi: str
    risks: List[str]
    risks_hindi: List[str]
    alternatives: List[str]
    alternatives_hindi: List[str]
    requires_witness: bool = False
    requires_interpreter: bool = False
    validity_days: Optional[int] = None  # None = indefinite
    is_procedure_specific: bool = False


@dataclass
class ConsentRecord:
    """A recorded consent from a patient."""
    consent_id: str
    patient_id: int
    patient_name: str
    consent_type: ConsentType
    template_id: Optional[str]
    status: ConsentStatus

    # What was consented to
    procedure_name: Optional[str]
    procedure_details: Optional[str]
    treating_doctor_id: str
    treating_doctor_name: str

    # Consent details
    consented_at: Optional[datetime]
    withdrawn_at: Optional[datetime]
    expires_at: Optional[datetime]

    # Who provided consent
    consenter_name: str  # Patient or guardian
    consenter_relationship: str  # Self, Parent, Spouse, etc.
    consenter_id_type: Optional[str]  # Aadhaar, PAN, etc.
    consenter_id_number: Optional[str]  # Last 4 digits only

    # Digital signature
    signature_data: Optional[str]  # Base64 encoded signature image
    signature_hash: Optional[str]

    # Witness (if required)
    witness_name: Optional[str]
    witness_relationship: Optional[str]
    witness_signature: Optional[str]

    # Interpreter (if required)
    interpreter_name: Optional[str]
    interpreter_language: Optional[str]

    # For withdrawn/refused
    withdrawal_reason: Optional[str]
    refusal_reason: Optional[str]

    # Metadata
    collected_via: str = "mobile"  # mobile, tablet, paper_scanned
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if self.status != ConsentStatus.OBTAINED:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True


class ConsentManager:
    """
    Manage digital consent collection and verification.

    Features:
    - Multilingual consent forms (Hindi + English)
    - Digital signature capture
    - Witness support for complex procedures
    - Consent validity tracking
    - Easy verification before procedures
    """

    # Standard consent templates
    TEMPLATES = {
        "general_treatment": ConsentTemplate(
            template_id="general_treatment",
            consent_type=ConsentType.GENERAL_TREATMENT,
            title="General Treatment Consent",
            title_hindi="सामान्य उपचार सहमति",
            description=(
                "I consent to receive medical examination, diagnostic procedures, "
                "and treatment as recommended by the treating physician."
            ),
            description_hindi=(
                "मैं उपचार करने वाले चिकित्सक द्वारा सुझाए गए चिकित्सा परीक्षण, "
                "नैदानिक प्रक्रियाओं और उपचार प्राप्त करने के लिए सहमति देता/देती हूं।"
            ),
            risks=[
                "Side effects from medications",
                "Allergic reactions",
                "Need for additional treatment",
            ],
            risks_hindi=[
                "दवाओं से दुष्प्रभाव",
                "एलर्जी प्रतिक्रियाएं",
                "अतिरिक्त उपचार की आवश्यकता",
            ],
            alternatives=["Seeking second opinion", "Alternative treatments"],
            alternatives_hindi=["दूसरी राय लेना", "वैकल्पिक उपचार"],
        ),
        "data_sharing_referral": ConsentTemplate(
            template_id="data_sharing_referral",
            consent_type=ConsentType.DATA_SHARING_REFERRAL,
            title="Data Sharing Consent (Referral)",
            title_hindi="डेटा साझाकरण सहमति (रेफरल)",
            description=(
                "I consent to share my medical records with the referred specialist "
                "for continuity of care."
            ),
            description_hindi=(
                "मैं उपचार की निरंतरता के लिए रेफर किए गए विशेषज्ञ के साथ "
                "अपने मेडिकल रिकॉर्ड साझा करने के लिए सहमति देता/देती हूं।"
            ),
            risks=["Information will be shared with another healthcare provider"],
            risks_hindi=["जानकारी अन्य स्वास्थ्य सेवा प्रदाता के साथ साझा की जाएगी"],
            alternatives=["Not sharing records (may affect care coordination)"],
            alternatives_hindi=["रिकॉर्ड साझा न करना (देखभाल समन्वय को प्रभावित कर सकता है)"],
        ),
        "whatsapp_communication": ConsentTemplate(
            template_id="whatsapp_communication",
            consent_type=ConsentType.WHATSAPP_COMMUNICATION,
            title="WhatsApp Communication Consent",
            title_hindi="व्हाट्सएप संचार सहमति",
            description=(
                "I consent to receive appointment reminders, health tips, and "
                "prescription details via WhatsApp."
            ),
            description_hindi=(
                "मैं व्हाट्सएप के माध्यम से अपॉइंटमेंट रिमाइंडर, स्वास्थ्य टिप्स "
                "और प्रिस्क्रिप्शन विवरण प्राप्त करने के लिए सहमति देता/देती हूं।"
            ),
            risks=[
                "Messages may be seen by others with access to your phone",
                "WhatsApp is not a HIPAA-compliant platform",
            ],
            risks_hindi=[
                "आपके फोन तक पहुंच रखने वाले अन्य लोग संदेश देख सकते हैं",
                "व्हाट्सएप HIPAA-अनुपालक प्लेटफॉर्म नहीं है",
            ],
            alternatives=["SMS communication", "Phone calls only"],
            alternatives_hindi=["एसएमएस संचार", "केवल फोन कॉल"],
        ),
        "against_medical_advice": ConsentTemplate(
            template_id="against_medical_advice",
            consent_type=ConsentType.AGAINST_MEDICAL_ADVICE,
            title="Discharge Against Medical Advice",
            title_hindi="चिकित्सा सलाह के विरुद्ध छुट्टी",
            description=(
                "I understand that I am leaving against medical advice. I take "
                "full responsibility for any consequences of this decision."
            ),
            description_hindi=(
                "मैं समझता/समझती हूं कि मैं चिकित्सा सलाह के विरुद्ध जा रहा/रही हूं। "
                "मैं इस निर्णय के किसी भी परिणाम की पूर्ण जिम्मेदारी लेता/लेती हूं।"
            ),
            risks=[
                "Condition may worsen",
                "Permanent disability or death may result",
                "Additional treatment may be required later",
            ],
            risks_hindi=[
                "स्थिति खराब हो सकती है",
                "स्थायी विकलांगता या मृत्यु हो सकती है",
                "बाद में अतिरिक्त उपचार की आवश्यकता हो सकती है",
            ],
            alternatives=["Continue recommended treatment"],
            alternatives_hindi=["अनुशंसित उपचार जारी रखें"],
            requires_witness=True,
        ),
    }

    def __init__(self, db_service, audit_logger=None):
        """Initialize consent manager."""
        self.db = db_service
        self.audit = audit_logger

    def create_consent_request(
        self,
        patient_id: int,
        patient_name: str,
        consent_type: ConsentType,
        treating_doctor_id: str,
        treating_doctor_name: str,
        procedure_name: Optional[str] = None,
        procedure_details: Optional[str] = None,
        custom_risks: Optional[List[str]] = None,
        validity_days: Optional[int] = None,
    ) -> ConsentRecord:
        """
        Create a new consent request to be signed by patient.

        Args:
            patient_id: Patient ID
            patient_name: Patient name
            consent_type: Type of consent needed
            treating_doctor_id: Doctor requesting consent
            treating_doctor_name: Doctor name
            procedure_name: Name of procedure (if applicable)
            procedure_details: Additional details
            custom_risks: Additional risks to disclose
            validity_days: How long consent is valid

        Returns:
            ConsentRecord in PENDING status
        """
        template = self.TEMPLATES.get(consent_type.value)

        consent = ConsentRecord(
            consent_id=str(uuid.uuid4()),
            patient_id=patient_id,
            patient_name=patient_name,
            consent_type=consent_type,
            template_id=template.template_id if template else None,
            status=ConsentStatus.PENDING,
            procedure_name=procedure_name,
            procedure_details=procedure_details,
            treating_doctor_id=treating_doctor_id,
            treating_doctor_name=treating_doctor_name,
            consented_at=None,
            withdrawn_at=None,
            expires_at=None,
            consenter_name="",
            consenter_relationship="",
            consenter_id_type=None,
            consenter_id_number=None,
            signature_data=None,
            signature_hash=None,
            witness_name=None,
            witness_relationship=None,
            witness_signature=None,
            interpreter_name=None,
            interpreter_language=None,
            withdrawal_reason=None,
            refusal_reason=None,
        )

        if self.db:
            self.db.store_consent_record(consent)

        return consent

    def record_consent(
        self,
        consent_id: str,
        consenter_name: str,
        consenter_relationship: str,
        signature_data: str,
        consenter_id_type: Optional[str] = None,
        consenter_id_number: Optional[str] = None,
        witness_name: Optional[str] = None,
        witness_relationship: Optional[str] = None,
        witness_signature: Optional[str] = None,
        interpreter_name: Optional[str] = None,
        interpreter_language: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> ConsentRecord:
        """
        Record that consent was obtained.

        Args:
            consent_id: ID of pending consent
            consenter_name: Name of person providing consent
            consenter_relationship: Relationship to patient
            signature_data: Base64 encoded signature image
            consenter_id_type: Type of ID shown (Aadhaar, etc.)
            consenter_id_number: Last 4 digits of ID
            witness_*: Witness details if required
            interpreter_*: Interpreter details if used

        Returns:
            Updated ConsentRecord
        """
        consent = self._get_consent(consent_id)
        if not consent:
            raise ValueError(f"Consent {consent_id} not found")

        # Calculate signature hash
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

        # Get template for validity
        template = self.TEMPLATES.get(consent.consent_type.value)
        validity_days = template.validity_days if template else None

        # Update consent
        consent.status = ConsentStatus.OBTAINED
        consent.consented_at = datetime.now()
        consent.consenter_name = consenter_name
        consent.consenter_relationship = consenter_relationship
        consent.consenter_id_type = consenter_id_type
        consent.consenter_id_number = consenter_id_number[-4:] if consenter_id_number else None
        consent.signature_data = signature_data
        consent.signature_hash = signature_hash
        consent.witness_name = witness_name
        consent.witness_relationship = witness_relationship
        consent.witness_signature = witness_signature
        consent.interpreter_name = interpreter_name
        consent.interpreter_language = interpreter_language
        consent.ip_address = ip_address
        consent.device_info = device_info

        if validity_days:
            from datetime import timedelta
            consent.expires_at = datetime.now() + timedelta(days=validity_days)

        if self.db:
            self.db.update_consent_record(consent)

        # Log to audit trail
        if self.audit:
            self.audit.log(
                action=self.audit.AuditAction.CONSENT_OBTAIN,
                user_id=consent.treating_doctor_id,
                user_name=consent.treating_doctor_name,
                patient_id=consent.patient_id,
                patient_name=consent.patient_name,
                description=f"Obtained {consent.consent_type.value} consent",
                resource_type="consent",
                resource_id=consent_id,
                details={
                    "consent_type": consent.consent_type.value,
                    "consenter": consenter_name,
                    "relationship": consenter_relationship,
                    "signature_hash": signature_hash,
                },
            )

        return consent

    def record_refusal(
        self,
        consent_id: str,
        refusal_reason: str,
        refused_by: str,
    ) -> ConsentRecord:
        """Record that consent was refused."""
        consent = self._get_consent(consent_id)
        if not consent:
            raise ValueError(f"Consent {consent_id} not found")

        consent.status = ConsentStatus.REFUSED
        consent.refusal_reason = refusal_reason
        consent.consenter_name = refused_by

        if self.db:
            self.db.update_consent_record(consent)

        return consent

    def withdraw_consent(
        self,
        consent_id: str,
        withdrawal_reason: str,
        withdrawn_by: str,
    ) -> ConsentRecord:
        """Withdraw a previously given consent."""
        consent = self._get_consent(consent_id)
        if not consent:
            raise ValueError(f"Consent {consent_id} not found")

        consent.status = ConsentStatus.WITHDRAWN
        consent.withdrawn_at = datetime.now()
        consent.withdrawal_reason = withdrawal_reason

        if self.db:
            self.db.update_consent_record(consent)

        # Log to audit trail
        if self.audit:
            self.audit.log(
                action=self.audit.AuditAction.CONSENT_WITHDRAW,
                user_id=consent.treating_doctor_id,
                user_name=consent.treating_doctor_name,
                patient_id=consent.patient_id,
                patient_name=consent.patient_name,
                description=f"Withdrew {consent.consent_type.value} consent",
                resource_type="consent",
                resource_id=consent_id,
                details={
                    "consent_type": consent.consent_type.value,
                    "withdrawal_reason": withdrawal_reason,
                    "withdrawn_by": withdrawn_by,
                },
            )

        return consent

    def verify_consent(
        self,
        patient_id: int,
        consent_type: ConsentType,
        procedure_name: Optional[str] = None,
    ) -> Dict:
        """
        Verify if valid consent exists for a patient/procedure.

        Use before performing procedures to ensure consent is documented.

        Returns:
            Dict with verification result and consent details
        """
        consents = self.get_patient_consents(patient_id)

        # Find matching valid consent
        matching = [
            c for c in consents
            if c.consent_type == consent_type
            and c.is_valid()
            and (procedure_name is None or c.procedure_name == procedure_name)
        ]

        if matching:
            consent = matching[0]
            return {
                "has_valid_consent": True,
                "consent_id": consent.consent_id,
                "consented_at": consent.consented_at,
                "consented_by": consent.consenter_name,
                "expires_at": consent.expires_at,
                "signature_hash": consent.signature_hash,
            }

        # Check if refused
        refused = [
            c for c in consents
            if c.consent_type == consent_type
            and c.status == ConsentStatus.REFUSED
        ]

        if refused:
            return {
                "has_valid_consent": False,
                "reason": "consent_refused",
                "refused_at": refused[0].created_at,
                "refusal_reason": refused[0].refusal_reason,
            }

        return {
            "has_valid_consent": False,
            "reason": "no_consent_on_record",
            "action_required": "Obtain consent before proceeding",
        }

    def get_patient_consents(self, patient_id: int) -> List[ConsentRecord]:
        """Get all consent records for a patient."""
        if self.db:
            return self.db.get_consents_for_patient(patient_id)
        return []

    def get_pending_consents(self, doctor_id: str) -> List[ConsentRecord]:
        """Get all pending consent requests for a doctor."""
        if self.db:
            return self.db.get_pending_consents_for_doctor(doctor_id)
        return []

    def get_expiring_consents(self, days_ahead: int = 30) -> List[ConsentRecord]:
        """Get consents expiring within specified days."""
        if self.db:
            return self.db.get_expiring_consents(days_ahead)
        return []

    def get_consent_template(
        self,
        consent_type: ConsentType,
        language: str = "en"
    ) -> Dict:
        """Get consent template for display."""
        template = self.TEMPLATES.get(consent_type.value)

        if not template:
            return {
                "title": consent_type.value.replace("_", " ").title(),
                "description": "",
                "risks": [],
                "alternatives": [],
            }

        if language == "hi":
            return {
                "title": template.title_hindi,
                "description": template.description_hindi,
                "risks": template.risks_hindi,
                "alternatives": template.alternatives_hindi,
                "requires_witness": template.requires_witness,
            }

        return {
            "title": template.title,
            "description": template.description,
            "risks": template.risks,
            "alternatives": template.alternatives,
            "requires_witness": template.requires_witness,
        }

    def generate_consent_pdf(
        self,
        consent: ConsentRecord,
        language: str = "en"
    ) -> bytes:
        """
        Generate PDF of signed consent for records.

        Returns:
            PDF bytes
        """
        # This would use fpdf2 to generate a proper consent document
        # For now, return placeholder
        template = self.get_consent_template(consent.consent_type, language)

        # In production, use fpdf2 to generate proper PDF
        # with signature image embedded
        return b""  # Placeholder

    def _get_consent(self, consent_id: str) -> Optional[ConsentRecord]:
        """Get consent by ID."""
        if self.db:
            return self.db.get_consent_by_id(consent_id)
        return None
