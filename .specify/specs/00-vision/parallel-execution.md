# Parallel Execution Specifications

> Detailed specifications for 6 parallel agent streams

## AGENT DISPATCH PROTOCOL

Each agent receives a complete, self-contained specification. Agents work independently and commit to their own feature branches. Integration happens after all agents complete their stream.

---

## AGENT 1: AMBIENT CLINICAL INTELLIGENCE

### Mission
Build the voice capture and clinical note extraction system that allows doctors to speak naturally while AI generates structured documentation.

### Branch
`claude/ambient-clinical-intelligence`

### Files to Create

```
src/
├── services/
│   └── voice/
│       ├── __init__.py
│       ├── voice_capture.py        # Audio capture with VAD
│       ├── speech_to_text.py       # Whisper.cpp integration
│       ├── language_detector.py    # Hindi/English detection
│       └── audio_processor.py      # Noise reduction, normalization
│   └── clinical_nlp/
│       ├── __init__.py
│       ├── note_extractor.py       # SOAP note extraction
│       ├── medical_ner.py          # Medical entity recognition
│       ├── clinical_reasoning.py   # Differential/red flag logic
│       └── prompts/
│           ├── soap_extraction.txt
│           ├── differential_generation.txt
│           └── red_flag_detection.txt
├── ui/
│   └── ambient/
│       ├── __init__.py
│       ├── ambient_panel.py        # Main ambient UI panel
│       ├── waveform_display.py     # Audio waveform visualization
│       ├── transcript_view.py      # Real-time transcript
│       └── note_editor.py          # Editable extracted notes
└── models/
    └── clinical/
        ├── __init__.py
        ├── soap_note.py            # SOAP note models
        ├── symptoms.py             # Symptom models
        └── differentials.py        # Differential diagnosis models
```

### Core Implementation Details

#### voice_capture.py
```python
import pyaudio
import numpy as np
import webrtcvad
from dataclasses import dataclass
from typing import Callable, Optional
from queue import Queue
from threading import Thread

@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 30  # VAD requires 10, 20, or 30ms
    vad_aggressiveness: int = 2  # 0-3, higher = more aggressive

class VoiceCaptureEngine:
    """Continuous voice capture with Voice Activity Detection"""

    def __init__(self, config: AudioConfig = AudioConfig()):
        self.config = config
        self.vad = webrtcvad.Vad(config.vad_aggressiveness)
        self.audio = pyaudio.PyAudio()
        self.is_listening = False
        self.speech_buffer = []
        self.silence_frames = 0
        self.speech_callback: Optional[Callable] = None

    def start_listening(self):
        """Start ambient listening in background thread"""
        self.is_listening = True
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self._chunk_size,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Process each audio chunk"""
        if not self.is_listening:
            return (None, pyaudio.paComplete)

        # Check for speech
        is_speech = self.vad.is_speech(in_data, self.config.sample_rate)

        if is_speech:
            self.speech_buffer.append(in_data)
            self.silence_frames = 0
        else:
            if self.speech_buffer:
                self.silence_frames += 1
                # If 500ms of silence after speech, trigger callback
                if self.silence_frames > self._silence_threshold:
                    self._on_speech_segment_complete()

        return (None, pyaudio.paContinue)

    def _on_speech_segment_complete(self):
        """Called when a speech segment ends"""
        audio_data = b''.join(self.speech_buffer)
        self.speech_buffer = []
        self.silence_frames = 0

        if self.speech_callback:
            self.speech_callback(audio_data)

    def on_speech_detected(self, callback: Callable[[bytes], None]):
        """Set callback for when speech segment is detected"""
        self.speech_callback = callback

    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
```

#### speech_to_text.py
```python
from whispercpp import Whisper
from typing import Generator
import numpy as np

class SpeechToText:
    """On-device Whisper integration for speech recognition"""

    MODELS = {
        "tiny": "whisper-tiny",      # ~75MB, fastest
        "base": "whisper-base",      # ~142MB, good balance
        "small": "whisper-small",    # ~466MB, more accurate
    }

    def __init__(self, model_size: str = "base"):
        self.model = Whisper.from_pretrained(self.MODELS[model_size])
        self.model_size = model_size

    def transcribe(self, audio: bytes, language: str = "auto") -> str:
        """Transcribe audio to text"""
        # Convert bytes to float32 numpy array
        audio_np = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

        # Transcribe with language hint
        result = self.model.transcribe(
            audio_np,
            language=language if language != "auto" else None,
        )

        return result["text"].strip()

    def transcribe_streaming(self, audio_stream) -> Generator[str, None, None]:
        """Real-time transcription with streaming output"""
        buffer = b''
        for chunk in audio_stream:
            buffer += chunk
            # Process every 2 seconds of audio
            if len(buffer) >= 32000 * 2:  # 16kHz * 2 bytes * 2 seconds
                partial = self.transcribe(buffer[-32000*2:])
                yield partial
                buffer = buffer[-16000:]  # Keep last 1 second for context
```

#### note_extractor.py
```python
from typing import Optional
from dataclasses import dataclass, field
from ..llm import LLMService

@dataclass
class SOAPNote:
    subjective: dict = field(default_factory=dict)  # Chief complaint, HPI
    objective: dict = field(default_factory=dict)   # Vitals, exam findings
    assessment: dict = field(default_factory=dict)  # Diagnoses, differentials
    plan: dict = field(default_factory=dict)        # Medications, investigations

class ClinicalNoteExtractor:
    """Extract structured clinical data from natural speech"""

    EXTRACTION_PROMPT = """
    You are a medical scribe. Extract structured clinical information from
    the doctor-patient conversation transcript below.

    TRANSCRIPT:
    {transcript}

    Extract the following in JSON format:
    {
        "subjective": {
            "chief_complaint": "main reason for visit",
            "history_of_present_illness": "detailed description",
            "associated_symptoms": ["list of symptoms"],
            "relevant_history": "pertinent past history"
        },
        "objective": {
            "vitals": {"bp": "", "pulse": "", "temp": "", "spo2": "", "weight": ""},
            "general_appearance": "",
            "examination_findings": ["list of findings"]
        },
        "assessment": {
            "primary_diagnosis": "",
            "differential_diagnoses": ["list"],
            "severity": "mild/moderate/severe"
        },
        "plan": {
            "medications": [{"drug": "", "dose": "", "frequency": "", "duration": ""}],
            "investigations": ["list"],
            "advice": ["list"],
            "follow_up": ""
        }
    }

    Only include information explicitly mentioned. Use null for missing fields.
    """

    def __init__(self, llm: LLMService):
        self.llm = llm

    def extract_soap_note(self, transcript: str) -> SOAPNote:
        """Extract SOAP note from transcript"""
        prompt = self.EXTRACTION_PROMPT.format(transcript=transcript)
        response = self.llm.generate(prompt)

        # Parse JSON response
        data = self._parse_json(response)

        return SOAPNote(
            subjective=data.get("subjective", {}),
            objective=data.get("objective", {}),
            assessment=data.get("assessment", {}),
            plan=data.get("plan", {})
        )

    def extract_vitals_only(self, transcript: str) -> dict:
        """Quick extraction of just vitals from transcript"""
        # ... implementation
```

### Dependencies
- pyaudio
- webrtcvad
- whispercpp (or whisper.cpp Python bindings)
- numpy

### Acceptance Criteria
- [ ] Voice capture works continuously without blocking UI
- [ ] VAD correctly identifies speech vs silence
- [ ] Transcription accuracy >90% for clear speech
- [ ] Hindi + English + code-mixed speech supported
- [ ] SOAP note extraction produces valid structured data
- [ ] Latency from speech end to note: <3 seconds
- [ ] Works fully offline

---

## AGENT 2: CLINICAL DECISION SUPPORT

### Mission
Build the drug interaction checker, dose calculator, and clinical alert system that prevents errors and suggests best practices.

### Branch
`claude/clinical-decision-support`

### Files to Create

```
src/
├── services/
│   └── drugs/
│       ├── __init__.py
│       ├── drug_database.py        # Drug lookup and search
│       ├── interaction_checker.py  # Drug-drug interactions
│       ├── contraindication.py     # Drug-disease contraindications
│       ├── dose_calculator.py      # Renal/hepatic/pediatric dosing
│       ├── allergy_checker.py      # Cross-reactivity checking
│       └── data/
│           ├── interactions.json   # Interaction database
│           ├── contraindications.json
│           └── cross_allergies.json
│   └── diagnosis/
│       ├── __init__.py
│       ├── differential_engine.py  # Bayesian differential diagnosis
│       ├── red_flag_detector.py    # Clinical red flags
│       ├── protocol_engine.py      # Treatment protocols
│       └── data/
│           ├── disease_prevalence_india.json
│           ├── symptom_likelihood.json
│           └── red_flags.json
├── ui/
│   └── alerts/
│       ├── __init__.py
│       ├── alert_banner.py         # Alert display component
│       ├── interaction_dialog.py   # Detailed interaction info
│       ├── alternative_picker.py   # Safe alternative selection
│       └── override_dialog.py      # Override with reason
└── models/
    └── drugs/
        ├── __init__.py
        ├── drug.py                 # Drug model
        ├── interaction.py          # Interaction model
        └── alert.py                # Alert model
```

### Core Implementation Details

#### interaction_checker.py
```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import json

class Severity(Enum):
    CRITICAL = "critical"  # Block prescription
    MAJOR = "major"        # Strong warning
    MODERATE = "moderate"  # Warning
    MINOR = "minor"        # Info

@dataclass
class Interaction:
    drug1: str
    drug2: str
    severity: Severity
    mechanism: str
    clinical_effect: str
    recommendation: str
    evidence_level: str

@dataclass
class Alert:
    type: str  # interaction, allergy, contraindication, dose
    severity: Severity
    title: str
    message: str
    details: dict
    alternatives: List[str]
    can_override: bool

class InteractionChecker:
    """Check drug-drug and drug-disease interactions"""

    def __init__(self, data_path: str = "data/interactions.json"):
        with open(data_path) as f:
            self.interactions_db = json.load(f)
        self._build_index()

    def _build_index(self):
        """Build fast lookup index for interactions"""
        self.index = {}
        for interaction in self.interactions_db:
            key1 = (interaction["drug1"].lower(), interaction["drug2"].lower())
            key2 = (interaction["drug2"].lower(), interaction["drug1"].lower())
            self.index[key1] = interaction
            self.index[key2] = interaction

    def check_pair(self, drug1: str, drug2: str) -> Optional[Interaction]:
        """Check interaction between two drugs"""
        key = (drug1.lower(), drug2.lower())
        if key in self.index:
            data = self.index[key]
            return Interaction(
                drug1=drug1,
                drug2=drug2,
                severity=Severity(data["severity"]),
                mechanism=data["mechanism"],
                clinical_effect=data["clinical_effect"],
                recommendation=data["recommendation"],
                evidence_level=data["evidence"]
            )
        return None

    def check_prescription(self,
                          new_drugs: List[str],
                          current_drugs: List[str],
                          patient_conditions: List[str],
                          patient_allergies: List[str]) -> List[Alert]:
        """
        Comprehensive prescription checking

        Returns list of alerts for:
        - Drug-drug interactions
        - Drug-disease contraindications
        - Allergy conflicts (including cross-reactivity)
        - Duplicate therapy
        """
        alerts = []

        # Check all drug pairs (new vs current and new vs new)
        all_drugs = new_drugs + current_drugs
        for i, drug1 in enumerate(all_drugs):
            for drug2 in all_drugs[i+1:]:
                interaction = self.check_pair(drug1, drug2)
                if interaction:
                    alerts.append(self._interaction_to_alert(interaction))

        # Check contraindications
        for drug in new_drugs:
            for condition in patient_conditions:
                contra = self.check_contraindication(drug, condition)
                if contra:
                    alerts.append(contra)

        # Check allergies
        for drug in new_drugs:
            allergy_alert = self.check_allergy(drug, patient_allergies)
            if allergy_alert:
                alerts.append(allergy_alert)

        # Sort by severity
        alerts.sort(key=lambda a: list(Severity).index(a.severity))

        return alerts

    def get_alternatives(self, drug: str, indication: str) -> List[str]:
        """Suggest safe alternatives for a problematic drug"""
        # Look up drug class and find alternatives
        # Filter out drugs with same interactions
        # Return ranked by efficacy for indication
        pass

    def _interaction_to_alert(self, interaction: Interaction) -> Alert:
        return Alert(
            type="interaction",
            severity=interaction.severity,
            title=f"{interaction.drug1} + {interaction.drug2}",
            message=interaction.clinical_effect,
            details={
                "mechanism": interaction.mechanism,
                "recommendation": interaction.recommendation,
                "evidence": interaction.evidence_level
            },
            alternatives=[],  # Populated separately
            can_override=interaction.severity != Severity.CRITICAL
        )
```

#### dose_calculator.py
```python
from dataclasses import dataclass
from typing import Optional
import math

@dataclass
class DoseRecommendation:
    drug: str
    recommended_dose: str
    original_dose: str
    adjustment_reason: str
    confidence: float
    references: List[str]

class DoseCalculator:
    """Calculate adjusted doses based on patient parameters"""

    def __init__(self, dosing_data_path: str):
        with open(dosing_data_path) as f:
            self.dosing_db = json.load(f)

    def calculate_egfr(self, creatinine: float, age: int,
                       weight: float, gender: str) -> float:
        """Calculate eGFR using CKD-EPI equation"""
        # CKD-EPI 2021 equation (race-free)
        kappa = 0.7 if gender == "F" else 0.9
        alpha = -0.241 if gender == "F" else -0.302
        female_factor = 1.012 if gender == "F" else 1.0

        min_ratio = min(creatinine / kappa, 1)
        max_ratio = max(creatinine / kappa, 1)

        egfr = 142 * (min_ratio ** alpha) * (max_ratio ** -1.200) * \
               (0.9938 ** age) * female_factor

        return round(egfr, 1)

    def calculate_renal_dose(self, drug: str, egfr: float,
                            original_dose: str) -> DoseRecommendation:
        """Adjust dose for renal impairment"""
        if drug not in self.dosing_db:
            return None

        drug_data = self.dosing_db[drug]
        if "renal" not in drug_data:
            return None

        # Find appropriate dose for eGFR
        for threshold in sorted(drug_data["renal"].keys(), reverse=True):
            if egfr >= float(threshold):
                adjustment = drug_data["renal"][threshold]
                break

        return DoseRecommendation(
            drug=drug,
            recommended_dose=adjustment["dose"],
            original_dose=original_dose,
            adjustment_reason=f"eGFR {egfr} mL/min requires dose adjustment",
            confidence=0.9,
            references=adjustment.get("references", [])
        )

    def calculate_pediatric_dose(self, drug: str, weight_kg: float,
                                 age_years: int) -> DoseRecommendation:
        """Calculate weight-based pediatric dose"""
        if drug not in self.dosing_db:
            return None

        drug_data = self.dosing_db[drug]
        if "pediatric" not in drug_data:
            return None

        ped_data = drug_data["pediatric"]
        mg_per_kg = ped_data["mg_per_kg"]
        max_dose = ped_data.get("max_dose")
        frequency = ped_data["frequency"]

        calculated_dose = weight_kg * mg_per_kg
        if max_dose and calculated_dose > max_dose:
            calculated_dose = max_dose

        return DoseRecommendation(
            drug=drug,
            recommended_dose=f"{calculated_dose:.1f}mg {frequency}",
            original_dose="",
            adjustment_reason=f"Weight-based: {mg_per_kg}mg/kg",
            confidence=0.95,
            references=ped_data.get("references", [])
        )
```

### Dependencies
- No external ML dependencies (rule-based + JSON data)
- Optional: fuzzywuzzy for drug name matching

### Acceptance Criteria
- [ ] Detects all major drug-drug interactions
- [ ] Zero false negatives for critical interactions
- [ ] Renal dosing calculations match clinical guidelines
- [ ] Pediatric dosing uses correct weight-based formulas
- [ ] Cross-allergy detection (e.g., penicillin → cephalosporin)
- [ ] Response time <100ms for full prescription check
- [ ] Alert UI is clear, non-intrusive but unmissable

---

## AGENT 3: WHATSAPP INTEGRATION

### Mission
Build the WhatsApp Business API integration for prescription delivery, appointment booking, and automated patient communication.

### Branch
`claude/whatsapp-integration`

### Files to Create

```
src/
├── services/
│   └── whatsapp/
│       ├── __init__.py
│       ├── client.py               # WhatsApp Business API client
│       ├── templates.py            # Message templates
│       ├── conversation_handler.py # AI conversation handling
│       ├── webhook_handler.py      # Incoming message webhook
│       └── media_handler.py        # PDF/image sending
│   └── communications/
│       ├── __init__.py
│       ├── reminder_service.py     # Scheduled reminders
│       ├── broadcast_service.py    # Bulk messaging
│       └── scheduler.py            # Background job scheduler
├── ui/
│   └── whatsapp/
│       ├── __init__.py
│       ├── conversation_panel.py   # Chat view in app
│       ├── quick_replies.py        # Quick action buttons
│       └── message_composer.py     # Compose messages
└── models/
    └── messaging/
        ├── __init__.py
        ├── message.py              # Message models
        ├── conversation.py         # Conversation models
        └── template.py             # Template models
```

### Core Implementation Details

#### client.py
```python
import httpx
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class MessageStatus(Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

@dataclass
class SendResult:
    message_id: str
    status: MessageStatus
    timestamp: str

class WhatsAppClient:
    """WhatsApp Business Cloud API client"""

    BASE_URL = "https://graph.facebook.com/v17.0"

    def __init__(self, phone_number_id: str, access_token: str):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    def send_text(self, to: str, message: str) -> SendResult:
        """Send a text message"""
        response = self.client.post(
            f"/{self.phone_number_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": self._format_phone(to),
                "type": "text",
                "text": {"body": message}
            }
        )
        return self._parse_response(response)

    def send_template(self, to: str, template_name: str,
                     language: str = "en",
                     components: List[dict] = None) -> SendResult:
        """Send a pre-approved template message"""
        payload = {
            "messaging_product": "whatsapp",
            "to": self._format_phone(to),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            }
        }
        if components:
            payload["template"]["components"] = components

        response = self.client.post(
            f"/{self.phone_number_id}/messages",
            json=payload
        )
        return self._parse_response(response)

    def send_document(self, to: str, document_url: str,
                     filename: str, caption: str = "") -> SendResult:
        """Send a document (PDF, etc.)"""
        response = self.client.post(
            f"/{self.phone_number_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": self._format_phone(to),
                "type": "document",
                "document": {
                    "link": document_url,
                    "filename": filename,
                    "caption": caption
                }
            }
        )
        return self._parse_response(response)

    def upload_media(self, file_path: str, mime_type: str) -> str:
        """Upload media and get media ID"""
        with open(file_path, 'rb') as f:
            response = self.client.post(
                f"/{self.phone_number_id}/media",
                files={"file": (file_path, f, mime_type)},
                data={"messaging_product": "whatsapp"}
            )
        return response.json()["id"]

    def _format_phone(self, phone: str) -> str:
        """Format phone number to E.164 format"""
        phone = ''.join(filter(str.isdigit, phone))
        if not phone.startswith('91'):
            phone = '91' + phone
        return phone
```

#### conversation_handler.py
```python
from dataclasses import dataclass
from typing import Optional
from ..llm import LLMService
from ..database import DatabaseService

@dataclass
class IncomingMessage:
    from_number: str
    message_type: str  # text, image, document
    content: str
    timestamp: str
    message_id: str

@dataclass
class Response:
    message: str
    action: Optional[str] = None  # book_appointment, send_prescription, escalate
    action_data: Optional[dict] = None

class ConversationHandler:
    """AI-powered conversation handling for patient messages"""

    TRIAGE_PROMPT = """
    You are a medical clinic assistant. A patient has sent a message.
    Analyze the message and determine the appropriate response.

    Patient message: {message}
    Patient history: {history}

    Determine:
    1. Is this urgent? (symptoms suggesting emergency)
    2. What category? (appointment, prescription, query, emergency)
    3. Can AI respond, or should this go to doctor?

    Respond in JSON:
    {
        "urgency": "emergency|urgent|routine",
        "category": "appointment|prescription|query|feedback|other",
        "can_ai_respond": true/false,
        "suggested_response": "response if AI can handle",
        "escalation_reason": "reason if needs doctor"
    }
    """

    def __init__(self, llm: LLMService, db: DatabaseService,
                 whatsapp: WhatsAppClient):
        self.llm = llm
        self.db = db
        self.whatsapp = whatsapp

    def process_message(self, message: IncomingMessage) -> Response:
        """Process incoming patient message"""

        # Get patient context
        patient = self.db.get_patient_by_phone(message.from_number)
        history = self._get_conversation_history(message.from_number)

        # Analyze message with AI
        analysis = self._analyze_message(message.content, patient, history)

        if analysis["urgency"] == "emergency":
            return self._handle_emergency(message, patient)

        if analysis["can_ai_respond"]:
            return Response(
                message=analysis["suggested_response"],
                action=None
            )
        else:
            return self._escalate_to_doctor(message, patient,
                                           analysis["escalation_reason"])

    def _handle_emergency(self, message: IncomingMessage,
                         patient) -> Response:
        """Handle emergency messages"""
        # Immediately notify doctor
        self._notify_doctor_emergency(message, patient)

        return Response(
            message="""🚨 This sounds urgent.

Please call emergency services (108) or go to the nearest hospital immediately.

Dr. {doctor_name} has been notified and will call you shortly.

If this is a life-threatening emergency, please call 108 NOW.""",
            action="emergency_alert",
            action_data={"patient_id": patient.id if patient else None}
        )

    def handle_appointment_request(self, message: IncomingMessage,
                                   patient) -> Response:
        """Handle appointment booking request"""
        # Get available slots
        slots = self.db.get_available_slots(days_ahead=7)

        slot_text = "\n".join([
            f"{i+1}. {slot.date.strftime('%a %d %b')} at {slot.time}"
            for i, slot in enumerate(slots[:5])
        ])

        return Response(
            message=f"""Available appointment slots:

{slot_text}

Reply with the number (1-5) to book, or type 'more' for additional options.""",
            action="await_slot_selection"
        )
```

#### reminder_service.py
```python
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler

@dataclass
class ScheduledReminder:
    id: str
    patient_phone: str
    message: str
    send_at: datetime
    reminder_type: str  # appointment, medication, follow_up
    metadata: dict

class ReminderService:
    """Automated reminder scheduling and sending"""

    def __init__(self, whatsapp: WhatsAppClient, db: DatabaseService):
        self.whatsapp = whatsapp
        self.db = db
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def schedule_appointment_reminder(self, appointment):
        """Schedule reminders for an appointment"""
        patient = self.db.get_patient(appointment.patient_id)

        # 1 day before
        self._schedule_reminder(
            patient.phone,
            self._format_appointment_reminder(appointment, "1_day"),
            appointment.datetime - timedelta(days=1),
            "appointment_1day",
            {"appointment_id": appointment.id}
        )

        # 1 hour before
        self._schedule_reminder(
            patient.phone,
            self._format_appointment_reminder(appointment, "1_hour"),
            appointment.datetime - timedelta(hours=1),
            "appointment_1hour",
            {"appointment_id": appointment.id}
        )

    def schedule_medication_reminders(self, prescription):
        """Schedule medication reminders based on prescription"""
        patient = self.db.get_patient(prescription.patient_id)

        for medication in prescription.medications:
            times = self._parse_frequency(medication.frequency)

            for time in times:
                # Schedule daily at each time
                self.scheduler.add_job(
                    self._send_medication_reminder,
                    'cron',
                    hour=time.hour,
                    minute=time.minute,
                    args=[patient.phone, medication],
                    id=f"med_{prescription.id}_{medication.id}_{time}",
                    end_date=prescription.end_date
                )

    def schedule_follow_up_reminder(self, visit):
        """Schedule follow-up reminder"""
        if not visit.follow_up_date:
            return

        patient = self.db.get_patient(visit.patient_id)

        # 2 days before follow-up
        reminder_date = visit.follow_up_date - timedelta(days=2)

        self._schedule_reminder(
            patient.phone,
            f"""Namaste {patient.name}!

Your follow-up visit with Dr. {visit.doctor_name} is due on {visit.follow_up_date.strftime('%d %b %Y')}.

Reply BOOK to schedule your appointment.""",
            reminder_date,
            "follow_up",
            {"visit_id": visit.id}
        )

    def _schedule_reminder(self, phone: str, message: str,
                          send_at: datetime, reminder_type: str,
                          metadata: dict):
        """Add reminder to scheduler"""
        job_id = f"{reminder_type}_{metadata.get('id', datetime.now().timestamp())}"

        self.scheduler.add_job(
            self._send_reminder,
            'date',
            run_date=send_at,
            args=[phone, message, reminder_type, metadata],
            id=job_id
        )

    def _send_reminder(self, phone: str, message: str,
                      reminder_type: str, metadata: dict):
        """Send the reminder"""
        result = self.whatsapp.send_text(phone, message)

        # Log the reminder
        self.db.log_reminder(
            phone=phone,
            message=message,
            reminder_type=reminder_type,
            status=result.status,
            metadata=metadata
        )
```

### Dependencies
- httpx (HTTP client)
- apscheduler (job scheduling)
- Optional: webhook server (FastAPI/Flask for incoming messages)

### Acceptance Criteria
- [ ] Can send text messages via WhatsApp Business API
- [ ] Can send prescription PDFs
- [ ] Template messages work for reminders
- [ ] AI correctly triages incoming messages
- [ ] Emergency messages trigger immediate alerts
- [ ] Appointment booking flow is conversational
- [ ] Medication reminders sent at correct times
- [ ] All messages logged for audit

---

## AGENT 4: SMART PATIENT TIMELINE

### Mission
Build the AI-powered patient summary and trend analysis system that enables 30-second patient understanding.

### Branch
`claude/smart-patient-timeline`

### Files to Create

```
src/
├── services/
│   └── summary/
│       ├── __init__.py
│       ├── patient_summarizer.py   # AI summary generation
│       ├── trend_analyzer.py       # Lab/vital trend analysis
│       ├── care_gap_detector.py    # Overdue care detection
│       ├── risk_stratifier.py      # Patient risk scoring
│       └── prompts/
│           ├── summary_generation.txt
│           └── trend_interpretation.txt
├── ui/
│   └── timeline/
│       ├── __init__.py
│       ├── patient_timeline.py     # Main timeline view
│       ├── summary_card.py         # AI summary display
│       ├── trend_chart.py          # Trend visualization
│       ├── care_gap_alerts.py      # Care gap display
│       └── timeline_entry.py       # Individual timeline items
└── models/
    └── timeline/
        ├── __init__.py
        ├── summary.py              # Summary models
        ├── trend.py                # Trend models
        └── care_gap.py             # Care gap models
```

### Core Implementation Details

#### patient_summarizer.py
```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import date

@dataclass
class PatientSummary:
    one_liner: str                    # Single sentence overview
    key_diagnoses: List[str]          # Major diagnoses with duration
    current_medications: List[str]    # Active medications
    recent_trends: List[str]          # What's improving/worsening
    red_flags: List[str]              # Concerns requiring attention
    care_gaps: List[str]              # Overdue preventive care
    last_visit_summary: str           # What happened last time
    generated_at: date

class PatientSummarizer:
    """Generate intelligent patient summaries using LLM"""

    SUMMARY_PROMPT = """
    You are a medical AI assistant. Generate a concise clinical summary
    for a doctor who is about to see this patient.

    PATIENT DATA:
    Name: {name}
    Age/Gender: {age} {gender}

    DIAGNOSES (with dates):
    {diagnoses}

    CURRENT MEDICATIONS:
    {medications}

    RECENT VISITS (last 6 months):
    {visits}

    RECENT LABS:
    {labs}

    Generate a summary in this exact JSON format:
    {
        "one_liner": "Single sentence capturing the essence of this patient",
        "key_diagnoses": ["Diagnosis 1 (duration)", "Diagnosis 2 (duration)"],
        "current_medications": ["Med 1 dose", "Med 2 dose"],
        "recent_trends": ["HbA1c improving from 8.2 to 7.5", "BP stable at target"],
        "red_flags": ["Creatinine rising - may need nephrology referral"],
        "care_gaps": ["Annual eye exam overdue by 6 months"],
        "last_visit_summary": "Came for diabetes follow-up. HbA1c improved. Continued same medications."
    }

    Be concise but comprehensive. Focus on what the doctor needs to know NOW.
    """

    def __init__(self, llm, db):
        self.llm = llm
        self.db = db

    def generate_summary(self, patient_id: int) -> PatientSummary:
        """Generate comprehensive patient summary"""
        patient = self.db.get_patient(patient_id)
        diagnoses = self.db.get_patient_diagnoses(patient_id)
        medications = self.db.get_current_medications(patient_id)
        visits = self.db.get_recent_visits(patient_id, months=6)
        labs = self.db.get_recent_labs(patient_id, months=12)

        prompt = self.SUMMARY_PROMPT.format(
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            diagnoses=self._format_diagnoses(diagnoses),
            medications=self._format_medications(medications),
            visits=self._format_visits(visits),
            labs=self._format_labs(labs)
        )

        response = self.llm.generate(prompt)
        data = self._parse_json(response)

        return PatientSummary(
            one_liner=data["one_liner"],
            key_diagnoses=data["key_diagnoses"],
            current_medications=data["current_medications"],
            recent_trends=data["recent_trends"],
            red_flags=data["red_flags"],
            care_gaps=data["care_gaps"],
            last_visit_summary=data["last_visit_summary"],
            generated_at=date.today()
        )

    def generate_visit_comparison(self, current_visit_id: int,
                                  previous_visit_id: int) -> str:
        """What's changed since last visit?"""
        current = self.db.get_visit(current_visit_id)
        previous = self.db.get_visit(previous_visit_id)

        # Compare vitals, labs, symptoms
        # Generate natural language comparison
        pass
```

#### trend_analyzer.py
```python
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum
import numpy as np

class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class Trend:
    parameter: str              # e.g., "HbA1c", "Creatinine"
    direction: TrendDirection
    values: List[Tuple[date, float]]  # (date, value) pairs
    change_percent: float       # Percent change from first to last
    interpretation: str         # Natural language interpretation
    action_needed: bool
    suggested_action: Optional[str]

class TrendAnalyzer:
    """Analyze trends in patient data over time"""

    # Define what "improving" means for each parameter
    TREND_DEFINITIONS = {
        "hba1c": {"improving": "decreasing", "target": 7.0, "unit": "%"},
        "creatinine": {"improving": "stable_or_decreasing", "target": 1.2, "unit": "mg/dL"},
        "systolic_bp": {"improving": "decreasing", "target": 130, "unit": "mmHg"},
        "ldl": {"improving": "decreasing", "target": 100, "unit": "mg/dL"},
        "weight": {"improving": "context_dependent", "unit": "kg"},
    }

    def analyze_trend(self, parameter: str,
                     values: List[Tuple[date, float]]) -> Trend:
        """Analyze trend for a single parameter"""
        if len(values) < 2:
            return Trend(
                parameter=parameter,
                direction=TrendDirection.INSUFFICIENT_DATA,
                values=values,
                change_percent=0,
                interpretation="Not enough data points to determine trend",
                action_needed=False,
                suggested_action=None
            )

        # Sort by date
        values = sorted(values, key=lambda x: x[0])

        # Calculate linear regression for trend
        dates_numeric = [(v[0] - values[0][0]).days for v in values]
        vals = [v[1] for v in values]

        slope, _ = np.polyfit(dates_numeric, vals, 1)

        # Determine direction based on parameter type
        definition = self.TREND_DEFINITIONS.get(parameter.lower(), {})
        improving_means = definition.get("improving", "decreasing")

        if abs(slope) < 0.01:  # Essentially flat
            direction = TrendDirection.STABLE
        elif improving_means == "decreasing":
            direction = TrendDirection.IMPROVING if slope < 0 else TrendDirection.WORSENING
        else:  # increasing is improving
            direction = TrendDirection.IMPROVING if slope > 0 else TrendDirection.WORSENING

        # Calculate percent change
        change_percent = ((vals[-1] - vals[0]) / vals[0]) * 100 if vals[0] != 0 else 0

        # Generate interpretation
        interpretation = self._generate_interpretation(
            parameter, direction, vals[0], vals[-1], definition
        )

        # Determine if action needed
        action_needed = direction == TrendDirection.WORSENING
        suggested_action = self._suggest_action(parameter, direction, vals[-1], definition)

        return Trend(
            parameter=parameter,
            direction=direction,
            values=values,
            change_percent=change_percent,
            interpretation=interpretation,
            action_needed=action_needed,
            suggested_action=suggested_action
        )

    def _generate_interpretation(self, parameter: str,
                                direction: TrendDirection,
                                first_value: float,
                                last_value: float,
                                definition: dict) -> str:
        """Generate natural language interpretation"""
        unit = definition.get("unit", "")
        target = definition.get("target")

        if direction == TrendDirection.IMPROVING:
            base = f"{parameter} improving from {first_value}{unit} to {last_value}{unit}"
            if target and last_value <= target:
                return f"{base}. Now at target."
            elif target:
                return f"{base}. Getting closer to target of {target}{unit}."
            return base

        elif direction == TrendDirection.WORSENING:
            return f"{parameter} worsening from {first_value}{unit} to {last_value}{unit}. Needs attention."

        else:
            return f"{parameter} stable at {last_value}{unit}"
```

### Acceptance Criteria
- [ ] AI summary accurately captures patient essence
- [ ] Summaries generated in <3 seconds
- [ ] Trend analysis correctly identifies improving/worsening
- [ ] Care gaps detected based on clinical guidelines
- [ ] Timeline UI shows all relevant information
- [ ] Trend charts are visually clear
- [ ] Red flags prominently displayed

---

## AGENT 5: PRACTICE GROWTH ENGINE

### Mission
Build analytics, reputation management, and patient acquisition tracking to help doctors grow their practice.

### Branch
`claude/practice-growth-engine`

### Files to Create

```
src/
├── services/
│   └── analytics/
│       ├── __init__.py
│       ├── practice_analytics.py   # Core analytics engine
│       ├── patient_acquisition.py  # Source tracking
│       ├── retention_tracker.py    # Follow-up compliance
│       └── revenue_analytics.py    # Revenue analysis
│   └── reputation/
│       ├── __init__.py
│       ├── review_manager.py       # Review collection/response
│       ├── google_integration.py   # Google Business Profile
│       └── sentiment_analyzer.py   # Review sentiment analysis
├── ui/
│   └── growth/
│       ├── __init__.py
│       ├── growth_dashboard.py     # Main dashboard
│       ├── analytics_charts.py     # Chart components
│       ├── review_panel.py         # Review management
│       └── insights_panel.py       # AI-generated insights
└── models/
    └── analytics/
        ├── __init__.py
        ├── metrics.py              # Metric models
        └── insights.py             # Insight models
```

### Acceptance Criteria
- [ ] Dashboard shows key metrics at a glance
- [ ] Patient acquisition sources tracked accurately
- [ ] Review collection automation works
- [ ] Sentiment analysis provides useful insights
- [ ] Retention metrics calculated correctly
- [ ] Revenue analytics by service/period
- [ ] Actionable recommendations generated

---

## AGENT 6: MEDICOLEGAL FORTRESS

### Mission
Build complete audit trail, consent management, and incident documentation for legal protection.

### Branch
`claude/medicolegal-fortress`

### Files to Create

```
src/
├── services/
│   └── audit/
│       ├── __init__.py
│       ├── audit_logger.py         # Immutable audit trail
│       ├── timestamp_service.py    # Cryptographic timestamps
│       ├── export_service.py       # Legal document export
│       └── data_access_tracker.py  # Who accessed what
│   └── consent/
│       ├── __init__.py
│       ├── consent_manager.py      # Consent collection
│       ├── consent_templates.py    # Template forms
│       └── signature_capture.py    # Digital signatures
│   └── incidents/
│       ├── __init__.py
│       ├── incident_reporter.py    # Adverse event logging
│       ├── timeline_builder.py     # Incident timeline
│       └── disclosure_generator.py # Disclosure documents
├── ui/
│   └── legal/
│       ├── __init__.py
│       ├── audit_viewer.py         # View audit trail
│       ├── consent_form.py         # Consent collection UI
│       └── incident_form.py        # Incident reporting UI
└── models/
    └── legal/
        ├── __init__.py
        ├── audit_entry.py          # Audit models
        ├── consent.py              # Consent models
        └── incident.py             # Incident models
```

### Acceptance Criteria
- [ ] All actions logged with cryptographic timestamps
- [ ] Audit trail is immutable (append-only)
- [ ] Consent forms capture digital signatures
- [ ] Multi-language consent templates
- [ ] Incident reports include full timeline
- [ ] Legal exports are court-admissible format
- [ ] Data access tracking complete

---

## LAUNCH SEQUENCE

### Day 1: Agent Dispatch
```bash
# Launch all 6 agents in parallel
claude --branch claude/ambient-clinical-intelligence --prompt "Execute Agent 1 spec"
claude --branch claude/clinical-decision-support --prompt "Execute Agent 2 spec"
claude --branch claude/whatsapp-integration --prompt "Execute Agent 3 spec"
claude --branch claude/smart-patient-timeline --prompt "Execute Agent 4 spec"
claude --branch claude/practice-growth-engine --prompt "Execute Agent 5 spec"
claude --branch claude/medicolegal-fortress --prompt "Execute Agent 6 spec"
```

### Day 7: Integration Phase
1. Merge all branches to integration branch
2. Resolve any conflicts
3. Build integration layer (`src/integration/clinical_flow.py`)
4. End-to-end testing

### Day 14: Launch Ready
1. All features working
2. Performance optimized
3. Documentation complete
4. Ready for production

---

*Six streams. Six agents. One revolutionary product.*
