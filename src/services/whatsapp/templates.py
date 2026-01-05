"""WhatsApp message templates for common scenarios"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, date


@dataclass
class TemplateComponent:
    type: str  # header, body, button
    parameters: List[Dict]


class MessageTemplates:
    """Pre-defined message templates for common clinic communications"""

    # Template names (must match approved templates in WhatsApp Business)
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    PRESCRIPTION_DELIVERY = "prescription_delivery"
    MEDICATION_REMINDER = "medication_reminder"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    LAB_RESULT_READY = "lab_result_ready"
    CLINIC_NOTICE = "clinic_notice"

    @staticmethod
    def appointment_reminder(patient_name: str,
                            doctor_name: str,
                            appointment_date: date,
                            appointment_time: str,
                            clinic_address: str) -> Dict:
        """Generate appointment reminder template data"""
        return {
            "name": MessageTemplates.APPOINTMENT_REMINDER,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": patient_name},
                        {"type": "text", "text": doctor_name},
                        {"type": "text", "text": appointment_date.strftime("%A, %d %B %Y")},
                        {"type": "text", "text": appointment_time},
                        {"type": "text", "text": clinic_address},
                    ]
                }
            ]
        }

    @staticmethod
    def prescription_delivery(patient_name: str,
                             doctor_name: str,
                             visit_date: date,
                             medication_summary: str,
                             follow_up: str) -> Dict:
        """Generate prescription delivery template data"""
        return {
            "name": MessageTemplates.PRESCRIPTION_DELIVERY,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {"type": "text", "text": "Your Prescription"}
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": patient_name},
                        {"type": "text", "text": doctor_name},
                        {"type": "text", "text": visit_date.strftime("%d %B %Y")},
                        {"type": "text", "text": medication_summary},
                        {"type": "text", "text": follow_up},
                    ]
                }
            ]
        }

    @staticmethod
    def medication_reminder(patient_name: str,
                           time_of_day: str,
                           medications: List[str]) -> Dict:
        """Generate medication reminder template data"""
        med_list = "\n".join([f"• {med}" for med in medications])

        return {
            "name": MessageTemplates.MEDICATION_REMINDER,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": patient_name},
                        {"type": "text", "text": time_of_day},
                        {"type": "text", "text": med_list},
                    ]
                }
            ]
        }

    @staticmethod
    def follow_up_reminder(patient_name: str,
                          doctor_name: str,
                          due_date: date,
                          reason: str) -> Dict:
        """Generate follow-up reminder template data"""
        return {
            "name": MessageTemplates.FOLLOW_UP_REMINDER,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": patient_name},
                        {"type": "text", "text": doctor_name},
                        {"type": "text", "text": due_date.strftime("%d %B %Y")},
                        {"type": "text", "text": reason},
                    ]
                }
            ]
        }

    @staticmethod
    def lab_result_ready(patient_name: str,
                        test_name: str,
                        clinic_name: str) -> Dict:
        """Generate lab result ready notification"""
        return {
            "name": MessageTemplates.LAB_RESULT_READY,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": patient_name},
                        {"type": "text", "text": test_name},
                        {"type": "text", "text": clinic_name},
                    ]
                }
            ]
        }

    @staticmethod
    def clinic_notice(subject: str,
                     message: str,
                     clinic_name: str) -> Dict:
        """Generate clinic notice template data"""
        return {
            "name": MessageTemplates.CLINIC_NOTICE,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {"type": "text", "text": subject}
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": message},
                        {"type": "text", "text": clinic_name},
                    ]
                }
            ]
        }


class QuickReplies:
    """Quick reply message builders"""

    @staticmethod
    def appointment_confirmation_buttons() -> List[Dict]:
        """Buttons for appointment confirmation"""
        return [
            {"type": "reply", "reply": {"id": "confirm", "title": "✓ Confirm"}},
            {"type": "reply", "reply": {"id": "reschedule", "title": "📅 Reschedule"}},
            {"type": "reply", "reply": {"id": "cancel", "title": "✗ Cancel"}},
        ]

    @staticmethod
    def medication_taken_buttons() -> List[Dict]:
        """Buttons for medication reminder response"""
        return [
            {"type": "reply", "reply": {"id": "taken", "title": "✓ Taken"}},
            {"type": "reply", "reply": {"id": "remind_later", "title": "⏰ Remind Later"}},
            {"type": "reply", "reply": {"id": "skipped", "title": "✗ Skipped"}},
        ]

    @staticmethod
    def available_slots_list(slots: List[Dict]) -> List[Dict]:
        """
        Generate list sections for appointment slots.

        Args:
            slots: List of slot dicts with keys: id, date, time, available

        Returns:
            List of sections for interactive list message
        """
        sections = []

        # Group slots by date
        slots_by_date = {}
        for slot in slots:
            slot_date = slot['date']
            if slot_date not in slots_by_date:
                slots_by_date[slot_date] = []
            slots_by_date[slot_date].append(slot)

        # Create sections
        for slot_date, date_slots in slots_by_date.items():
            rows = []
            for slot in date_slots:
                if slot.get('available', True):
                    rows.append({
                        "id": slot['id'],
                        "title": slot['time'],
                        "description": f"Available on {slot_date}"
                    })

            if rows:
                sections.append({
                    "title": slot_date,
                    "rows": rows[:10]  # WhatsApp limits to 10 rows per section
                })

        return sections[:10]  # WhatsApp limits to 10 sections

    @staticmethod
    def symptom_severity_buttons() -> List[Dict]:
        """Buttons for symptom severity assessment"""
        return [
            {"type": "reply", "reply": {"id": "severe", "title": "🔴 Severe"}},
            {"type": "reply", "reply": {"id": "moderate", "title": "🟡 Moderate"}},
            {"type": "reply", "reply": {"id": "mild", "title": "🟢 Mild"}},
        ]

    @staticmethod
    def prescription_query_buttons() -> List[Dict]:
        """Buttons for prescription-related queries"""
        return [
            {"type": "reply", "reply": {"id": "send_rx", "title": "📄 Send Prescription"}},
            {"type": "reply", "reply": {"id": "refill", "title": "🔄 Request Refill"}},
            {"type": "reply", "reply": {"id": "query", "title": "❓ Ask Question"}},
        ]

    @staticmethod
    def yes_no_buttons() -> List[Dict]:
        """Simple yes/no buttons"""
        return [
            {"type": "reply", "reply": {"id": "yes", "title": "✓ Yes"}},
            {"type": "reply", "reply": {"id": "no", "title": "✗ No"}},
        ]

    @staticmethod
    def main_menu_list() -> List[Dict]:
        """Main menu options as list sections"""
        return [
            {
                "title": "Appointments",
                "rows": [
                    {"id": "book_apt", "title": "📅 Book Appointment", "description": "Schedule a new visit"},
                    {"id": "view_apt", "title": "👁️ View Appointments", "description": "See upcoming visits"},
                    {"id": "cancel_apt", "title": "❌ Cancel Appointment", "description": "Cancel scheduled visit"},
                ]
            },
            {
                "title": "Medical Records",
                "rows": [
                    {"id": "get_rx", "title": "📄 Get Prescription", "description": "Download last prescription"},
                    {"id": "lab_results", "title": "🧪 Lab Results", "description": "View test results"},
                    {"id": "medical_history", "title": "📋 Medical History", "description": "View past visits"},
                ]
            },
            {
                "title": "Help & Support",
                "rows": [
                    {"id": "talk_doctor", "title": "👨‍⚕️ Talk to Doctor", "description": "Send message to doctor"},
                    {"id": "clinic_hours", "title": "🕐 Clinic Hours", "description": "View clinic timings"},
                    {"id": "contact", "title": "📞 Contact Us", "description": "Get clinic contact info"},
                ]
            }
        ]
