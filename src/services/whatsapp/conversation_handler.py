"""AI-powered conversation handling for patient messages"""
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    IDLE = "idle"
    AWAITING_SLOT_SELECTION = "awaiting_slot_selection"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_SYMPTOMS = "awaiting_symptoms"
    ESCALATED = "escalated"


@dataclass
class IncomingMessage:
    from_number: str
    message_type: str  # text, interactive, image, document, location
    content: str
    timestamp: str
    message_id: str
    context: Optional[Dict] = None  # For replies
    interactive_response: Optional[Dict] = None  # Button/list selection


@dataclass
class OutgoingResponse:
    message: str
    message_type: str = "text"  # text, template, interactive
    template_data: Optional[Dict] = None
    buttons: Optional[List[Dict]] = None
    action: Optional[str] = None  # book_appointment, send_prescription, escalate
    action_data: Optional[Dict] = None
    requires_follow_up: bool = False


@dataclass
class ConversationContext:
    patient_id: Optional[int]
    patient_name: Optional[str]
    state: ConversationState
    pending_action: Optional[str]
    pending_data: Optional[Dict]
    last_message_time: datetime
    message_count: int
    history: List[Dict] = field(default_factory=list)


class ConversationHandler:
    """AI-powered patient conversation handling"""

    TRIAGE_PROMPT = '''You are a medical clinic assistant for an Indian clinic. Analyze this patient message and determine the appropriate response.

Patient Message: {message}
Patient Name: {patient_name}
Recent Visits: {recent_visits}

Determine:
1. Is this urgent? (symptoms suggesting emergency - chest pain, difficulty breathing, severe bleeding, etc.)
2. Category: appointment, prescription_query, symptom_report, general_query, feedback, emergency
3. Can AI safely respond, or should this go to doctor?

Respond in JSON:
{{
    "urgency": "emergency|urgent|routine",
    "category": "appointment|prescription|symptoms|query|feedback|emergency",
    "can_ai_respond": true,
    "suggested_response": "Your helpful response here",
    "escalation_reason": null,
    "detected_symptoms": ["symptom1", "symptom2"],
    "action_suggested": "book_appointment|send_prescription|escalate|none"
}}'''

    EMERGENCY_KEYWORDS = [
        'chest pain', 'heart attack', 'can\'t breathe', 'difficulty breathing',
        'severe bleeding', 'unconscious', 'seizure', 'stroke', 'suicide',
        'severe pain', 'accident', 'emergency', 'urgent', 'help'
    ]

    def __init__(self, llm_service, db_service, whatsapp_client):
        self.llm = llm_service
        self.db = db_service
        self.whatsapp = whatsapp_client
        self.conversations: Dict[str, ConversationContext] = {}

    async def process_message(self, message: IncomingMessage) -> OutgoingResponse:
        """Process incoming patient message"""
        try:
            # Get or create conversation context
            context = self._get_or_create_context(message.from_number)
            context.message_count += 1
            context.last_message_time = datetime.now()

            # Add to history
            context.history.append({
                "role": "user",
                "content": message.content,
                "timestamp": message.timestamp
            })

            # Check for emergency keywords first
            if self._is_emergency(message.content):
                return await self._handle_emergency(message, context)

            # Get patient info from database
            patient = await self._get_patient_by_phone(message.from_number)
            if patient:
                context.patient_id = patient['id']
                context.patient_name = patient['name']

            # Handle based on conversation state
            if context.state == ConversationState.AWAITING_SLOT_SELECTION:
                return await self._handle_slot_selection(message, context)
            elif context.state == ConversationState.AWAITING_CONFIRMATION:
                return await self._handle_confirmation(message, context)
            elif context.state == ConversationState.AWAITING_SYMPTOMS:
                return await self._handle_symptom_report(message, context)

            # Handle interactive responses (button/list clicks)
            if message.interactive_response:
                return await self._handle_interactive_response(message, context)

            # Use LLM to triage the message
            return await self._triage_and_respond(message, context, patient)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return OutgoingResponse(
                message="I apologize, but I'm having trouble processing your message. Please try again or call the clinic directly.",
                message_type="text"
            )

    def _is_emergency(self, message: str) -> bool:
        """Check if message contains emergency keywords"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.EMERGENCY_KEYWORDS)

    async def _handle_emergency(self, message: IncomingMessage,
                               context: ConversationContext) -> OutgoingResponse:
        """Handle emergency messages with immediate escalation"""
        context.state = ConversationState.ESCALATED

        # Notify doctor immediately
        await self._notify_doctor(
            message,
            urgency="emergency",
            patient=await self._get_patient_by_phone(message.from_number)
        )

        return OutgoingResponse(
            message="🚨 This appears to be an emergency. Please call 102 (ambulance) or visit the nearest emergency room immediately.\n\nI have also alerted your doctor. For immediate assistance, call the clinic at: [CLINIC_PHONE]",
            message_type="text",
            action="escalate",
            action_data={"urgency": "emergency", "reason": "Emergency keywords detected"}
        )

    async def _handle_interactive_response(self, message: IncomingMessage,
                                          context: ConversationContext) -> OutgoingResponse:
        """Handle button/list selection responses"""
        response_id = message.interactive_response.get('id')

        # Handle menu selections
        if response_id == 'book_apt':
            return await self._handle_appointment_request(message, context)
        elif response_id == 'get_rx':
            return await self._send_last_prescription(context)
        elif response_id == 'talk_doctor':
            return await self._escalate_to_doctor(message, context, "Patient requested to talk to doctor")
        elif response_id in ['confirm', 'yes']:
            return await self._handle_confirmation_yes(context)
        elif response_id in ['cancel', 'no']:
            return await self._handle_confirmation_no(context)
        elif response_id == 'reschedule':
            return await self._handle_appointment_request(message, context)

        # Default response for unknown interactions
        return OutgoingResponse(
            message="I didn't understand that selection. How can I help you?",
            message_type="text"
        )

    async def _triage_and_respond(self, message: IncomingMessage,
                                 context: ConversationContext,
                                 patient: Optional[Dict]) -> OutgoingResponse:
        """Use LLM to triage message and generate response"""
        try:
            # Get recent visits for context
            recent_visits = []
            if patient:
                recent_visits = await self._get_recent_visits(patient['id'], limit=3)

            # Format prompt
            prompt = self.TRIAGE_PROMPT.format(
                message=message.content,
                patient_name=context.patient_name or "Unknown",
                recent_visits=json.dumps(recent_visits, indent=2)
            )

            # Get LLM response
            llm_response = await self.llm.generate(prompt, temperature=0.3)

            # Parse JSON response
            try:
                triage = json.loads(llm_response)
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                logger.error(f"Invalid JSON from LLM: {llm_response}")
                return await self._escalate_to_doctor(message, context, "Could not parse LLM response")

            # Handle based on triage
            if triage['urgency'] == 'emergency':
                return await self._handle_emergency(message, context)

            if not triage['can_ai_respond'] or triage['action_suggested'] == 'escalate':
                return await self._escalate_to_doctor(
                    message, context,
                    triage.get('escalation_reason', 'Requires doctor review')
                )

            # Handle different actions
            if triage['action_suggested'] == 'book_appointment':
                return await self._handle_appointment_request(message, context)
            elif triage['action_suggested'] == 'send_prescription':
                return await self._send_last_prescription(context)

            # Return AI-generated response
            return OutgoingResponse(
                message=triage['suggested_response'],
                message_type="text",
                requires_follow_up=triage['urgency'] == 'urgent'
            )

        except Exception as e:
            logger.error(f"Error in triage: {e}", exc_info=True)
            return await self._escalate_to_doctor(message, context, f"Triage error: {str(e)}")

    async def _handle_appointment_request(self, message: IncomingMessage,
                                         context: ConversationContext) -> OutgoingResponse:
        """Handle appointment booking request"""
        # Get available slots (mock for now)
        slots = await self._get_available_slots()

        if not slots:
            return OutgoingResponse(
                message="I'm sorry, but there are no available slots at the moment. Please call the clinic to check for cancellations.",
                message_type="text"
            )

        # Update context
        context.state = ConversationState.AWAITING_SLOT_SELECTION
        context.pending_action = 'book_appointment'

        # Import here to avoid circular dependency
        from .templates import QuickReplies

        return OutgoingResponse(
            message="Here are the available appointment slots. Please select one:",
            message_type="interactive",
            buttons=QuickReplies.available_slots_list(slots),
            requires_follow_up=True
        )

    async def _handle_slot_selection(self, message: IncomingMessage,
                                    context: ConversationContext) -> OutgoingResponse:
        """Handle slot selection from interactive list"""
        if message.interactive_response:
            slot_id = message.interactive_response.get('id')
            context.pending_data = {'slot_id': slot_id}
            context.state = ConversationState.AWAITING_CONFIRMATION

            from .templates import QuickReplies

            return OutgoingResponse(
                message=f"You've selected {message.interactive_response.get('title')}. Would you like to confirm this appointment?",
                message_type="interactive",
                buttons=QuickReplies.yes_no_buttons(),
                requires_follow_up=True
            )

        # If not interactive, assume text response
        context.state = ConversationState.IDLE
        return OutgoingResponse(
            message="Please select a slot from the list provided.",
            message_type="text"
        )

    async def _handle_confirmation_yes(self, context: ConversationContext) -> OutgoingResponse:
        """Handle confirmation yes"""
        if context.pending_action == 'book_appointment' and context.pending_data:
            # Book the appointment
            slot_id = context.pending_data.get('slot_id')
            # TODO: Actually book in database

            context.state = ConversationState.IDLE
            context.pending_action = None
            context.pending_data = None

            return OutgoingResponse(
                message="✓ Your appointment has been confirmed! You will receive a reminder 1 day before your visit.",
                message_type="text",
                action="book_appointment",
                action_data={'slot_id': slot_id}
            )

        context.state = ConversationState.IDLE
        return OutgoingResponse(
            message="Confirmed! Is there anything else I can help you with?",
            message_type="text"
        )

    async def _handle_confirmation_no(self, context: ConversationContext) -> OutgoingResponse:
        """Handle confirmation no"""
        context.state = ConversationState.IDLE
        context.pending_action = None
        context.pending_data = None

        return OutgoingResponse(
            message="No problem! How else can I help you?",
            message_type="text"
        )

    async def _handle_prescription_query(self, message: IncomingMessage,
                                        context: ConversationContext) -> OutgoingResponse:
        """Handle prescription-related queries"""
        return await self._send_last_prescription(context)

    async def _send_last_prescription(self, context: ConversationContext) -> OutgoingResponse:
        """Send the patient's last prescription"""
        if not context.patient_id:
            return OutgoingResponse(
                message="I couldn't find your patient record. Please call the clinic for assistance.",
                message_type="text"
            )

        # Get last visit with prescription
        visit = await self._get_last_visit_with_prescription(context.patient_id)

        if not visit:
            return OutgoingResponse(
                message="I couldn't find any prescription in your recent visits. Please consult with the doctor.",
                message_type="text"
            )

        return OutgoingResponse(
            message="Here is your latest prescription:",
            message_type="text",
            action="send_prescription",
            action_data={'visit_id': visit['id'], 'patient_id': context.patient_id}
        )

    async def _handle_symptom_report(self, message: IncomingMessage,
                                    context: ConversationContext) -> OutgoingResponse:
        """Handle symptom reports with triage"""
        context.state = ConversationState.ESCALATED

        await self._notify_doctor(
            message,
            urgency="urgent",
            patient=await self._get_patient_by_phone(message.from_number)
        )

        return OutgoingResponse(
            message="Thank you for sharing your symptoms. I've notified the doctor, who will review and get back to you shortly. If your symptoms worsen, please call the clinic immediately.",
            message_type="text",
            action="escalate",
            action_data={"urgency": "urgent", "reason": "Symptom report"}
        )

    def _get_or_create_context(self, phone: str) -> ConversationContext:
        """Get or create conversation context"""
        if phone not in self.conversations:
            self.conversations[phone] = ConversationContext(
                patient_id=None,
                patient_name=None,
                state=ConversationState.IDLE,
                pending_action=None,
                pending_data=None,
                last_message_time=datetime.now(),
                message_count=0
            )
        return self.conversations[phone]

    async def _escalate_to_doctor(self, message: IncomingMessage,
                                  context: ConversationContext,
                                  reason: str) -> OutgoingResponse:
        """Escalate conversation to doctor"""
        context.state = ConversationState.ESCALATED

        await self._notify_doctor(
            message,
            urgency="routine",
            patient=await self._get_patient_by_phone(message.from_number)
        )

        return OutgoingResponse(
            message="I've forwarded your message to the doctor. They will respond as soon as possible. For urgent matters, please call the clinic directly.",
            message_type="text",
            action="escalate",
            action_data={"urgency": "routine", "reason": reason}
        )

    async def _notify_doctor(self, message: IncomingMessage,
                            urgency: str,
                            patient: Optional[Dict]):
        """Send notification to doctor about patient message"""
        # This would integrate with the desktop app's notification system
        logger.info(f"Doctor notification: {urgency} - Patient: {patient.get('name') if patient else 'Unknown'} - Message: {message.content}")
        # TODO: Implement actual notification to desktop app

    async def _get_patient_by_phone(self, phone: str) -> Optional[Dict]:
        """Get patient from database by phone number"""
        try:
            # Format phone for search
            phone_digits = ''.join(filter(str.isdigit, phone))
            if phone_digits.startswith('91'):
                phone_digits = phone_digits[2:]

            # TODO: Implement actual database query
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting patient by phone: {e}")
            return None

    async def _get_recent_visits(self, patient_id: int, limit: int = 3) -> List[Dict]:
        """Get recent visits for patient"""
        try:
            # TODO: Implement actual database query
            return []
        except Exception as e:
            logger.error(f"Error getting recent visits: {e}")
            return []

    async def _get_last_visit_with_prescription(self, patient_id: int) -> Optional[Dict]:
        """Get last visit that has a prescription"""
        try:
            # TODO: Implement actual database query
            return None
        except Exception as e:
            logger.error(f"Error getting last visit: {e}")
            return None

    async def _get_available_slots(self) -> List[Dict]:
        """Get available appointment slots"""
        # Mock implementation - replace with actual slot management
        from datetime import date, timedelta

        today = date.today()
        slots = []

        for i in range(1, 8):  # Next 7 days
            slot_date = today + timedelta(days=i)
            for time_slot in ["10:00 AM", "11:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"]:
                slots.append({
                    "id": f"{slot_date.isoformat()}_{time_slot.replace(' ', '_')}",
                    "date": slot_date.strftime("%d %B %Y"),
                    "time": time_slot,
                    "available": True
                })

        return slots[:20]  # Return max 20 slots
