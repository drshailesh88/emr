# DocAssist Execution Roadmap

> From Vision to Reality - The Build Plan

## Execution Philosophy

**Parallel Development with Async Agents**

We have 6 major feature streams that can be developed in parallel:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PARALLEL DEVELOPMENT STREAMS                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   STREAM 1  │  │   STREAM 2  │  │   STREAM 3  │                  │
│  │   AMBIENT   │  │   CLINICAL  │  │   WHATSAPP  │                  │
│  │    VOICE    │  │  DECISION   │  │ INTEGRATION │                  │
│  │             │  │   SUPPORT   │  │             │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
│         │                │                │                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   STREAM 4  │  │   STREAM 5  │  │   STREAM 6  │                  │
│  │   PATIENT   │  │  PRACTICE   │  │  MEDICOLEGAL│                  │
│  │   TIMELINE  │  │   GROWTH    │  │   FORTRESS  │                  │
│  │             │  │             │  │             │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
│                                                                      │
│                    ┌─────────────────┐                               │
│                    │   INTEGRATION   │                               │
│                    │      LAYER      │                               │
│                    └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

Each stream is independent and can be developed by a separate agent.

---

## STREAM 1: AMBIENT CLINICAL INTELLIGENCE

> **Goal**: Doctor speaks naturally, AI generates complete clinical documentation

### Components to Build

#### 1.1 Voice Capture Engine
**Location**: `src/services/voice/`

```python
# voice_capture.py
class VoiceCaptureEngine:
    """Continuous voice capture with VAD (Voice Activity Detection)"""

    def start_listening(self):
        """Start ambient listening"""

    def on_speech_detected(self, callback):
        """Callback when speech segment detected"""

    def get_audio_segment(self) -> bytes:
        """Get the captured audio"""

    def stop_listening(self):
        """Stop ambient listening"""

# speech_to_text.py
class SpeechToText:
    """On-device Whisper integration"""

    def __init__(self, model_size: str = "base"):
        """Initialize Whisper model"""

    def transcribe(self, audio: bytes, language: str = "auto") -> str:
        """Transcribe audio to text"""

    def transcribe_realtime(self, audio_stream) -> Generator[str]:
        """Real-time transcription with streaming"""

# language_detector.py
class LanguageDetector:
    """Detect Hindi, English, or code-mixed speech"""

    def detect(self, text: str) -> str:
        """Return 'hi', 'en', or 'hi-en' for code-mixed"""
```

#### 1.2 Clinical NLP Engine
**Location**: `src/services/clinical_nlp/`

```python
# note_extractor.py
class ClinicalNoteExtractor:
    """Extract structured clinical data from natural speech"""

    def extract_soap_note(self, transcript: str) -> SOAPNote:
        """
        From: "Patient has fever for 3 days, cough, no cold"
        To: {
            subjective: {chief_complaint: "fever 3 days", associated: ["cough"]},
            objective: {...},
            assessment: {...},
            plan: {...}
        }
        """

    def extract_vitals(self, transcript: str) -> Vitals:
        """Extract BP, pulse, temp, SpO2 from speech"""

    def extract_medications(self, transcript: str) -> List[Medication]:
        """Extract prescribed medications"""

# medical_entity_recognition.py
class MedicalNER:
    """Named Entity Recognition for medical terms"""

    def extract_symptoms(self, text: str) -> List[Symptom]
    def extract_diagnoses(self, text: str) -> List[Diagnosis]
    def extract_drugs(self, text: str) -> List[Drug]
    def extract_investigations(self, text: str) -> List[Investigation]

# clinical_reasoning.py
class ClinicalReasoning:
    """AI clinical reasoning engine"""

    def generate_differentials(self, symptoms: List[Symptom], patient: Patient) -> List[Differential]:
        """Generate ranked differential diagnoses"""

    def suggest_investigations(self, differentials: List[Differential]) -> List[Investigation]:
        """Suggest investigations to rule in/out differentials"""

    def flag_red_flags(self, presentation: ClinicalPresentation) -> List[RedFlag]:
        """Identify red flags requiring immediate attention"""
```

#### 1.3 Ambient UI
**Location**: `src/ui/ambient/`

```python
# ambient_panel.py
class AmbientPanel(ft.UserControl):
    """Real-time voice capture and note generation panel"""

    # Shows:
    # - Live waveform during speech
    # - Real-time transcript
    # - Extracted SOAP note (editable)
    # - AI suggestions and alerts
    # - One-click accept/edit/reject
```

### Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Speech Model | Whisper.cpp (small/base) | Balance of accuracy and speed |
| Language | Hindi + English + Code-mixed | Reality of Indian consultations |
| NLP Model | Fine-tuned Qwen2.5 | Medical domain adaptation |
| Processing | On-device | Privacy, offline capability |
| Latency Target | <2s from speech end to note | Feels real-time |

---

## STREAM 2: CLINICAL DECISION SUPPORT

> **Goal**: Prevent errors, suggest best practices, catch what humans miss

### Components to Build

#### 2.1 Drug Intelligence Engine
**Location**: `src/services/drugs/`

```python
# drug_database.py
class DrugDatabase:
    """India-specific drug database"""

    def search(self, query: str) -> List[Drug]:
        """Search drugs by name, salt, brand"""

    def get_formulations(self, salt: str) -> List[Formulation]:
        """Get all formulations of a salt"""

    def get_interactions(self, drug: Drug) -> List[Interaction]:
        """Get all known interactions"""

# interaction_checker.py
class InteractionChecker:
    """Check drug-drug and drug-disease interactions"""

    def check_prescription(self, new_drugs: List[Drug],
                          current_drugs: List[Drug],
                          patient: Patient) -> List[Alert]:
        """
        Returns alerts for:
        - Drug-drug interactions (major, moderate, minor)
        - Drug-disease contraindications
        - Duplicate therapy
        - Allergy conflicts
        - Dose adjustments needed (renal, hepatic)
        - Pregnancy/lactation concerns
        """

    def get_alternatives(self, blocked_drug: Drug,
                        indication: str) -> List[Drug]:
        """Suggest safe alternatives for a blocked drug"""

# dose_calculator.py
class DoseCalculator:
    """Smart dosing based on patient parameters"""

    def calculate_renal_dose(self, drug: Drug, egfr: float) -> Dose:
        """Adjust dose for renal impairment"""

    def calculate_pediatric_dose(self, drug: Drug, weight: float, age: int) -> Dose:
        """Weight-based pediatric dosing"""

    def calculate_hepatic_dose(self, drug: Drug, child_pugh: str) -> Dose:
        """Adjust for hepatic impairment"""
```

#### 2.2 Diagnosis Assistant
**Location**: `src/services/diagnosis/`

```python
# differential_engine.py
class DifferentialEngine:
    """Bayesian differential diagnosis engine"""

    def __init__(self):
        self.prior_probabilities = load_india_disease_prevalence()

    def calculate_differentials(self,
                               symptoms: List[Symptom],
                               patient: Patient) -> List[Differential]:
        """
        Uses Bayesian probability with:
        - India-specific disease prevalence (prior)
        - Symptom likelihood ratios
        - Risk factor adjustments
        - Age/gender modifiers
        """

    def get_distinguishing_features(self,
                                   diff1: Differential,
                                   diff2: Differential) -> List[Feature]:
        """What findings would help distinguish between two diagnoses?"""

# red_flag_detector.py
class RedFlagDetector:
    """Detect clinical red flags requiring immediate action"""

    CARDIAC_RED_FLAGS = [
        "chest pain + sweating + nausea",
        "severe chest pain radiating to arm/jaw",
        "chest pain + shortness of breath",
    ]

    NEURO_RED_FLAGS = [
        "sudden severe headache",
        "headache + neck stiffness + fever",
        "weakness one side of body",
    ]

    # ... more categories

    def check(self, presentation: ClinicalPresentation) -> List[RedFlag]:
        """Return any red flags with urgency level and recommended action"""

# protocol_engine.py
class ProtocolEngine:
    """Evidence-based treatment protocols"""

    def get_protocol(self, diagnosis: str) -> TreatmentProtocol:
        """Get standard treatment protocol for a diagnosis"""

    def check_compliance(self, prescription: Prescription,
                        diagnosis: str) -> ComplianceReport:
        """Check if prescription follows guidelines"""
```

#### 2.3 Alert UI
**Location**: `src/ui/alerts/`

```python
# alert_banner.py
class AlertBanner(ft.UserControl):
    """Non-intrusive but unmissable alert display"""

    # Severity levels:
    # - CRITICAL (red, blocks prescription until acknowledged)
    # - WARNING (orange, requires acknowledgment)
    # - INFO (blue, dismissable)

    def show_interaction_alert(self, interaction: Interaction)
    def show_allergy_alert(self, allergy: Allergy)
    def show_red_flag_alert(self, red_flag: RedFlag)
    def show_dose_alert(self, dose_issue: DoseIssue)
```

---

## STREAM 3: WHATSAPP INTEGRATION

> **Goal**: Meet patients where they are, automate communication

### Components to Build

#### 3.1 WhatsApp Business API Integration
**Location**: `src/services/whatsapp/`

```python
# whatsapp_client.py
class WhatsAppClient:
    """WhatsApp Business API integration"""

    def send_text(self, phone: str, message: str) -> MessageStatus
    def send_document(self, phone: str, pdf: bytes, filename: str) -> MessageStatus
    def send_template(self, phone: str, template: str, params: dict) -> MessageStatus

    def register_webhook(self, callback: Callable)
    def handle_incoming(self, message: IncomingMessage)

# message_templates.py
class MessageTemplates:
    """Pre-approved WhatsApp templates"""

    APPOINTMENT_REMINDER = """
    Namaste {patient_name}!

    This is a reminder for your appointment with Dr. {doctor_name}
    tomorrow at {time}.

    📍 {clinic_address}

    Reply CONFIRM to confirm or RESCHEDULE to change.
    """

    PRESCRIPTION_DELIVERY = """
    Your prescription from Dr. {doctor_name} is attached.

    Medicines:
    {medicine_list}

    Follow-up: {follow_up_date}

    For any queries, reply to this message.
    """

    MEDICATION_REMINDER = """
    ⏰ Medicine Reminder

    Time to take your {time_of_day} medicines:
    {medicine_list}

    Stay healthy! 💊
    """

# conversation_handler.py
class ConversationHandler:
    """Handle patient conversations with AI assistance"""

    def process_message(self, message: IncomingMessage) -> Response:
        """
        AI-assisted response:
        - Symptom triage (urgent vs can wait)
        - FAQ answering
        - Appointment booking
        - Prescription queries
        - Escalation to doctor when needed
        """

    def escalate_to_doctor(self, conversation: Conversation):
        """Flag for doctor attention with priority"""
```

#### 3.2 Automated Communications
**Location**: `src/services/communications/`

```python
# reminder_service.py
class ReminderService:
    """Automated reminder scheduling and sending"""

    def schedule_appointment_reminder(self, appointment: Appointment):
        """Schedule reminder 1 day and 1 hour before"""

    def schedule_follow_up_reminder(self, visit: Visit):
        """Schedule reminder when follow-up is due"""

    def schedule_medication_reminders(self, prescription: Prescription):
        """Schedule daily medication reminders"""

    def schedule_preventive_care(self, patient: Patient):
        """Annual checkup, screening reminders"""

# broadcast_service.py
class BroadcastService:
    """Bulk messaging for clinic communications"""

    def send_clinic_notice(self, patients: List[Patient], message: str):
        """Holiday notice, doctor unavailability, etc."""

    def send_health_tip(self, patient_segment: str, tip: str):
        """Weekly health tips to engaged patients"""
```

#### 3.3 WhatsApp UI in App
**Location**: `src/ui/whatsapp/`

```python
# conversation_panel.py
class WhatsAppConversationPanel(ft.UserControl):
    """View and respond to patient WhatsApp messages"""

    # Shows:
    # - Conversation history
    # - AI-suggested responses
    # - Quick action buttons (send prescription, book appointment)
    # - Unread message indicators
```

---

## STREAM 4: SMART PATIENT TIMELINE

> **Goal**: Understand any patient in 30 seconds

### Components to Build

#### 4.1 AI Summary Engine
**Location**: `src/services/summary/`

```python
# patient_summarizer.py
class PatientSummarizer:
    """Generate intelligent patient summaries"""

    def generate_summary(self, patient: Patient) -> Summary:
        """
        Creates natural language summary:
        - Key diagnoses and when diagnosed
        - Current medications
        - Recent trends (improving/worsening)
        - Red flags and concerns
        - Overdue preventive care
        """

    def generate_visit_summary(self, visit: Visit) -> str:
        """Summarize a single visit"""

    def compare_to_last_visit(self, current: Visit, previous: Visit) -> Comparison:
        """What's changed since last time?"""

# trend_analyzer.py
class TrendAnalyzer:
    """Analyze trends in patient data"""

    def analyze_lab_trends(self, investigations: List[Investigation]) -> List[Trend]:
        """Identify improving, worsening, or stable trends"""

    def predict_trajectory(self, trend: Trend) -> Prediction:
        """Where is this heading if nothing changes?"""

    def get_intervention_suggestions(self, worsening_trend: Trend) -> List[Intervention]:
        """What can be done to reverse a worsening trend?"""
```

#### 4.2 Proactive Alerts
**Location**: `src/services/proactive/`

```python
# care_gap_detector.py
class CareGapDetector:
    """Detect gaps in patient care"""

    def check_preventive_care(self, patient: Patient) -> List[CareGap]:
        """
        Checks for:
        - Overdue annual exams
        - Missing vaccinations
        - Overdue screenings (mammogram, colonoscopy)
        - Missing diabetes monitoring (HbA1c, eye exam, foot exam)
        """

    def check_medication_monitoring(self, patient: Patient) -> List[CareGap]:
        """
        Checks for:
        - Statins without recent lipid panel
        - ACE inhibitors without recent creatinine
        - Metformin without recent B12
        """

# risk_stratifier.py
class RiskStratifier:
    """Stratify patients by risk level"""

    def calculate_cardiovascular_risk(self, patient: Patient) -> RiskScore:
        """Framingham/QRISK style calculation"""

    def calculate_diabetes_risk(self, patient: Patient) -> RiskScore:
        """FINDRISC style calculation"""

    def identify_high_risk_patients(self) -> List[Patient]:
        """Who needs attention before they get sick?"""
```

#### 4.3 Timeline UI
**Location**: `src/ui/timeline/`

```python
# patient_timeline.py
class PatientTimeline(ft.UserControl):
    """Visual patient timeline with AI insights"""

    # Shows:
    # - 30-second AI summary at top
    # - Vital trend charts
    # - Medication timeline
    # - Visit history as cards
    # - Lab results with abnormal highlighting
    # - Proactive alerts and care gaps
```

---

## STREAM 5: PRACTICE GROWTH ENGINE

> **Goal**: Grow the practice on autopilot

### Components to Build

#### 5.1 Analytics Engine
**Location**: `src/services/analytics/`

```python
# practice_analytics.py
class PracticeAnalytics:
    """Practice performance analytics"""

    def get_daily_summary(self, date: date) -> DailySummary:
        """Patients seen, revenue, new patients"""

    def get_patient_flow(self, period: str) -> FlowAnalysis:
        """Peak hours, wait times, bottlenecks"""

    def get_revenue_analysis(self, period: str) -> RevenueAnalysis:
        """Revenue by service, trends, projections"""

    def get_retention_metrics(self) -> RetentionMetrics:
        """Follow-up compliance, patient return rates"""

# patient_acquisition.py
class PatientAcquisition:
    """Track new patient sources"""

    def track_source(self, patient: Patient, source: str):
        """Track where new patient came from"""

    def get_source_breakdown(self, period: str) -> SourceBreakdown:
        """Google, referrals, WhatsApp, walk-ins"""

    def calculate_acquisition_cost(self, source: str) -> float:
        """Cost per new patient by source"""
```

#### 5.2 Reputation Management
**Location**: `src/services/reputation/`

```python
# review_manager.py
class ReviewManager:
    """Manage patient reviews and reputation"""

    def request_review(self, patient: Patient, visit: Visit):
        """Send review request after positive visit"""

    def sync_google_reviews(self):
        """Pull reviews from Google Maps"""

    def respond_to_review(self, review: Review, response: str):
        """Respond to Google review"""

    def get_sentiment_analysis(self) -> SentimentReport:
        """What are patients saying about us?"""

# referral_tracker.py
class ReferralTracker:
    """Track and incentivize patient referrals"""

    def track_referral(self, new_patient: Patient, referrer: Patient):
        """Record who referred whom"""

    def get_top_referrers(self, period: str) -> List[Patient]:
        """Which patients refer the most?"""

    def send_thank_you(self, referrer: Patient):
        """Thank patients who refer"""
```

#### 5.3 Growth Dashboard
**Location**: `src/ui/growth/`

```python
# growth_dashboard.py
class GrowthDashboard(ft.UserControl):
    """Practice growth analytics dashboard"""

    # Shows:
    # - Key metrics (patients, revenue, rating)
    # - Patient acquisition funnel
    # - Review sentiment and recent feedback
    # - Retention and follow-up compliance
    # - Actionable recommendations
```

---

## STREAM 6: MEDICOLEGAL FORTRESS

> **Goal**: Complete protection through documentation

### Components to Build

#### 6.1 Audit Trail
**Location**: `src/services/audit/`

```python
# audit_logger.py
class AuditLogger:
    """Immutable audit trail for all actions"""

    def log_action(self, action: Action, user: User, details: dict):
        """Log with cryptographic timestamp"""

    def log_data_access(self, patient: Patient, accessor: User, reason: str):
        """Track who accessed what"""

    def log_prescription(self, prescription: Prescription, warnings_shown: List[Warning]):
        """Document prescription with all warnings shown"""

    def get_audit_trail(self, patient: Patient, period: str) -> List[AuditEntry]:
        """Get complete audit trail for a patient"""

    def export_legal_document(self, patient: Patient) -> PDF:
        """Export legally defensible documentation"""

# timestamp_service.py
class TimestampService:
    """Cryptographic timestamping for non-repudiation"""

    def create_timestamp(self, data: bytes) -> Timestamp:
        """Create verifiable timestamp"""

    def verify_timestamp(self, data: bytes, timestamp: Timestamp) -> bool:
        """Verify data hasn't been modified since timestamp"""
```

#### 6.2 Consent Management
**Location**: `src/services/consent/`

```python
# consent_manager.py
class ConsentManager:
    """Digital consent collection and management"""

    def create_consent_form(self, type: str, patient: Patient) -> ConsentForm:
        """Generate consent form (procedure, treatment, sharing)"""

    def collect_signature(self, form: ConsentForm) -> SignedConsent:
        """Collect digital signature"""

    def verify_consent(self, patient: Patient, action: str) -> bool:
        """Check if required consent exists"""

    def get_consent_history(self, patient: Patient) -> List[SignedConsent]:
        """All consents given by patient"""
```

#### 6.3 Incident Management
**Location**: `src/services/incidents/`

```python
# incident_reporter.py
class IncidentReporter:
    """Adverse event and incident reporting"""

    def report_incident(self, incident: Incident):
        """Document adverse event with full context"""

    def get_timeline(self, incident: Incident) -> Timeline:
        """Reconstruct what happened and when"""

    def analyze_standard_of_care(self, incident: Incident) -> Analysis:
        """AI analysis of whether standard of care was met"""

    def generate_disclosure_document(self, incident: Incident) -> Document:
        """Generate patient disclosure document if needed"""
```

---

## Integration Layer

### Cross-Stream Integration Points

```python
# integration/clinical_flow.py
class ClinicalFlow:
    """Orchestrates the entire clinical workflow"""

    def start_consultation(self, patient: Patient):
        """
        1. Show patient timeline (Stream 4)
        2. Start ambient listening (Stream 1)
        3. Log consultation start (Stream 6)
        """

    def process_speech(self, audio: bytes):
        """
        1. Transcribe (Stream 1)
        2. Extract clinical data (Stream 1)
        3. Check for red flags (Stream 2)
        4. Update timeline (Stream 4)
        """

    def generate_prescription(self, medications: List[Medication]):
        """
        1. Check interactions (Stream 2)
        2. Log with warnings (Stream 6)
        3. Generate PDF
        4. Queue for WhatsApp (Stream 3)
        """

    def complete_consultation(self, visit: Visit):
        """
        1. Finalize documentation (Stream 6)
        2. Schedule reminders (Stream 3)
        3. Request review if appropriate (Stream 5)
        4. Update analytics (Stream 5)
        """
```

---

## Parallel Execution Plan

### Week 1-2: Foundation Sprint

Launch 6 parallel agents, one for each stream:

```
Agent 1: Ambient Voice - Build voice capture + STT pipeline
Agent 2: Clinical DS - Build drug database + interaction checker
Agent 3: WhatsApp - Build API client + message templates
Agent 4: Timeline - Build summarizer + trend analyzer
Agent 5: Growth - Build analytics engine + review manager
Agent 6: Medicolegal - Build audit logger + consent manager
```

### Week 3-4: Integration Sprint

```
Agent 1: Integrate voice → clinical extraction → prescription
Agent 2: Integrate CDS into prescription workflow
Agent 3: Integrate WhatsApp into post-visit flow
Agent 4: Integrate timeline into consultation start
Agent 5: Integrate analytics into dashboard
Agent 6: Integrate audit into all flows
```

### Week 5-6: Polish Sprint

```
Agent 1: Voice UI polish, error handling, edge cases
Agent 2: Alert UI, override workflows, alternative suggestions
Agent 3: Conversation AI, escalation logic
Agent 4: Timeline UI, trend visualization
Agent 5: Growth dashboard, recommendations engine
Agent 6: Legal export, incident workflow
```

---

## Success Criteria

### Must Hit Before Launch

| Metric | Target | Measurement |
|--------|--------|-------------|
| Voice accuracy | >95% for Hindi+English | Manual review of 100 consultations |
| Interaction detection | 100% of major interactions | Test against known interaction database |
| WhatsApp delivery | >99% | Delivery receipts |
| Summary accuracy | >90% approval by doctor | Doctor feedback on generated summaries |
| Audit completeness | 100% of actions logged | Audit log review |
| App launch time | <2 seconds | Automated testing |

### Must Hit in First Month

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily active users | 30% of registered | Analytics |
| Consultation time saved | 30%+ reduction | Before/after comparison |
| Patient satisfaction | 4.5+ stars | WhatsApp surveys |
| Doctor NPS | >50 | Monthly survey |
| Zero missed interactions | 0 incidents | Incident reports |

---

*This is not a product. This is a movement to transform Indian healthcare.*
