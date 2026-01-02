"""Patient reminder service for appointment and clinical reminders."""

import threading
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Callable
import urllib.parse
import webbrowser

# Try to import requests for SMS API
try:
    import requests
    _requests_available = True
except ImportError:
    _requests_available = False


# Reminder message templates
APPOINTMENT_REMINDER_TEMPLATE = """🏥 *Appointment Reminder*

Dear {patient_name},

This is a reminder of your appointment:

📅 Date: {date}
⏰ Time: {time}
🏥 {clinic_name}

If you need to reschedule, please call {clinic_phone}.

Thank you!"""

LAB_DUE_REMINDER_TEMPLATE = """🔬 *Lab Test Reminder*

Dear {patient_name},

Your {test_name} is due for a recheck. Your last test was on {last_date}.

Please schedule your test at your convenience.

{clinic_name}
{clinic_phone}"""

MEDICATION_REMINDER_TEMPLATE = """💊 *Medication Refill Reminder*

Dear {patient_name},

It's time to refill your prescription for {medication_name}.

Please visit {clinic_name} or your pharmacy for a refill.

{clinic_phone}"""


class ReminderService:
    """Service for managing patient reminders."""

    def __init__(self, db, clinic_name: str = "Kumar Clinic", clinic_phone: str = ""):
        """Initialize reminder service.

        Args:
            db: Database service instance
            clinic_name: Name of the clinic
            clinic_phone: Clinic contact number
        """
        self.db = db
        self.clinic_name = clinic_name
        self.clinic_phone = clinic_phone
        self.sms_gateway = None
        self.sms_api_key = None

    def configure_sms_gateway(self, gateway: str, api_key: str, sender_id: str = "CLINIC"):
        """Configure SMS gateway for sending SMS reminders.

        Args:
            gateway: Gateway name ('msg91', 'fast2sms', 'twilio')
            api_key: API key for the gateway
            sender_id: Sender ID for SMS (default: CLINIC)
        """
        self.sms_gateway = gateway.lower()
        self.sms_api_key = api_key
        self.sms_sender_id = sender_id

    def get_pending_reminders(self, days_ahead: int = 1) -> List[Dict]:
        """Get appointments that need reminders.

        Args:
            days_ahead: How many days ahead to check

        Returns:
            List of appointment dicts with patient info
        """
        target_date = (date.today() + timedelta(days=days_ahead)).isoformat()
        appointments = self.db.get_appointments_for_date(target_date)

        pending = []
        for appt in appointments:
            # Check if patient has opted out
            prefs = self.db.get_patient_preferences(appt['patient_id'])
            if prefs and prefs.get('reminder_opted_out'):
                continue

            # Check if reminder already sent today
            if self._reminder_already_sent(appt['id'], 'appointment'):
                continue

            pending.append(appt)

        return pending

    def _reminder_already_sent(self, reference_id: int, reminder_type: str) -> bool:
        """Check if a reminder was already sent today."""
        today = date.today().isoformat()
        logs = self.db.get_reminder_logs(
            reference_id=reference_id,
            reminder_type=reminder_type,
            date=today
        )
        return len(logs) > 0

    def format_appointment_reminder(self, appointment: Dict, patient_name: str) -> str:
        """Format appointment reminder message.

        Args:
            appointment: Appointment dict
            patient_name: Patient's name

        Returns:
            Formatted message string
        """
        appt_date = appointment.get('appointment_date', '')
        appt_time = appointment.get('appointment_time', '')

        # Format date nicely
        try:
            dt = datetime.strptime(appt_date, '%Y-%m-%d')
            formatted_date = dt.strftime('%d %B %Y (%A)')
        except:
            formatted_date = appt_date

        # Format time nicely
        try:
            if appt_time:
                t = datetime.strptime(appt_time, '%H:%M')
                formatted_time = t.strftime('%I:%M %p')
            else:
                formatted_time = "As scheduled"
        except:
            formatted_time = appt_time or "As scheduled"

        return APPOINTMENT_REMINDER_TEMPLATE.format(
            patient_name=patient_name,
            date=formatted_date,
            time=formatted_time,
            clinic_name=self.clinic_name,
            clinic_phone=self.clinic_phone or "the clinic"
        )

    def format_lab_reminder(self, patient_name: str, test_name: str, last_date: str) -> str:
        """Format lab test reminder message."""
        try:
            dt = datetime.strptime(last_date, '%Y-%m-%d')
            formatted_date = dt.strftime('%d %B %Y')
        except:
            formatted_date = last_date

        return LAB_DUE_REMINDER_TEMPLATE.format(
            patient_name=patient_name,
            test_name=test_name,
            last_date=formatted_date,
            clinic_name=self.clinic_name,
            clinic_phone=self.clinic_phone or "the clinic"
        )

    def send_reminder_whatsapp(self, phone: str, message: str) -> bool:
        """Send reminder via WhatsApp (opens WhatsApp Web).

        Args:
            phone: Patient phone number
            message: Message to send

        Returns:
            True if WhatsApp was opened
        """
        try:
            # Format phone number
            phone = phone.replace("+", "").replace(" ", "").replace("-", "")
            if len(phone) == 10:
                phone = "91" + phone

            # Encode message
            encoded_message = urllib.parse.quote(message)

            # Open WhatsApp Web
            url = f"https://wa.me/{phone}?text={encoded_message}"
            webbrowser.open(url)

            return True
        except Exception:
            return False

    def send_reminder_sms(self, phone: str, message: str) -> bool:
        """Send reminder via SMS gateway.

        Args:
            phone: Patient phone number
            message: Message to send

        Returns:
            True if SMS was sent successfully
        """
        if not _requests_available:
            return False

        if not self.sms_gateway or not self.sms_api_key:
            return False

        # Format phone
        phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        if len(phone) == 10:
            phone = "91" + phone

        try:
            if self.sms_gateway == 'msg91':
                return self._send_msg91(phone, message)
            elif self.sms_gateway == 'fast2sms':
                return self._send_fast2sms(phone, message)
            elif self.sms_gateway == 'twilio':
                return self._send_twilio(phone, message)
            else:
                return False
        except Exception:
            return False

    def _send_msg91(self, phone: str, message: str) -> bool:
        """Send SMS via MSG91."""
        url = "https://api.msg91.com/api/v5/flow/"
        headers = {
            "authkey": self.sms_api_key,
            "content-type": "application/json"
        }
        # Note: MSG91 requires template approval for transactional SMS
        # This is a simplified example
        data = {
            "mobiles": phone,
            "message": message,
            "sender": self.sms_sender_id,
            "route": "4",  # Transactional
            "country": "91"
        }
        response = requests.post(url, json=data, headers=headers, timeout=10)
        return response.status_code == 200

    def _send_fast2sms(self, phone: str, message: str) -> bool:
        """Send SMS via Fast2SMS."""
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": self.sms_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "route": "q",  # Quick SMS
            "message": message,
            "numbers": phone.replace("91", ""),
        }
        response = requests.post(url, json=data, headers=headers, timeout=10)
        return response.status_code == 200

    def _send_twilio(self, phone: str, message: str) -> bool:
        """Send SMS via Twilio."""
        # Twilio requires account SID and auth token
        # This is a placeholder - would need proper Twilio setup
        return False

    def send_reminder(
        self,
        patient_id: int,
        phone: str,
        message: str,
        reminder_type: str,
        reference_id: Optional[int] = None,
        prefer_whatsapp: bool = True
    ) -> Dict:
        """Send a reminder and log the result.

        Args:
            patient_id: Patient ID
            phone: Patient phone number
            message: Reminder message
            reminder_type: Type of reminder ('appointment', 'lab_due', 'medication')
            reference_id: ID of the related record (e.g., appointment_id)
            prefer_whatsapp: Try WhatsApp first

        Returns:
            Dict with status and channel used
        """
        channel = None
        status = 'failed'

        if prefer_whatsapp:
            if self.send_reminder_whatsapp(phone, message):
                channel = 'whatsapp'
                status = 'sent'
            elif self.send_reminder_sms(phone, message):
                channel = 'sms'
                status = 'sent'
        else:
            if self.send_reminder_sms(phone, message):
                channel = 'sms'
                status = 'sent'
            elif self.send_reminder_whatsapp(phone, message):
                channel = 'whatsapp'
                status = 'sent'

        # Log the reminder
        self.db.log_reminder(
            patient_id=patient_id,
            reminder_type=reminder_type,
            reference_id=reference_id,
            channel=channel or 'none',
            status=status,
            message=message
        )

        return {'status': status, 'channel': channel}

    def send_all_pending_reminders(
        self,
        on_progress: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict:
        """Send all pending reminders for tomorrow's appointments.

        Args:
            on_progress: Callback(current, total, patient_name)

        Returns:
            Dict with sent, failed counts
        """
        pending = self.get_pending_reminders(days_ahead=1)
        sent = 0
        failed = 0

        for i, appt in enumerate(pending):
            patient_name = appt.get('patient_name', 'Patient')
            patient_phone = appt.get('patient_phone', '')

            if on_progress:
                on_progress(i + 1, len(pending), patient_name)

            if not patient_phone:
                failed += 1
                continue

            # Get patient preferences
            prefs = self.db.get_patient_preferences(appt['patient_id'])
            prefer_whatsapp = True
            if prefs:
                prefer_whatsapp = prefs.get('preferred_channel', 'whatsapp') == 'whatsapp'

            # Format and send reminder
            message = self.format_appointment_reminder(appt, patient_name)
            result = self.send_reminder(
                patient_id=appt['patient_id'],
                phone=patient_phone,
                message=message,
                reminder_type='appointment',
                reference_id=appt['id'],
                prefer_whatsapp=prefer_whatsapp
            )

            if result['status'] == 'sent':
                sent += 1
            else:
                failed += 1

        return {'sent': sent, 'failed': failed, 'total': len(pending)}

    def get_overdue_labs(self, days_overdue: int = 30) -> List[Dict]:
        """Get patients with overdue lab tests based on flowsheets.

        Args:
            days_overdue: Minimum days since test was due

        Returns:
            List of dicts with patient and test info
        """
        # This would integrate with flowsheets to find overdue tests
        # Placeholder for now
        return []

    def send_lab_reminders(self) -> Dict:
        """Send reminders for overdue lab tests."""
        overdue = self.get_overdue_labs()
        sent = 0
        failed = 0

        for item in overdue:
            patient_phone = item.get('phone', '')
            if not patient_phone:
                failed += 1
                continue

            message = self.format_lab_reminder(
                patient_name=item.get('patient_name', 'Patient'),
                test_name=item.get('test_name', 'routine tests'),
                last_date=item.get('last_date', '')
            )

            result = self.send_reminder(
                patient_id=item['patient_id'],
                phone=patient_phone,
                message=message,
                reminder_type='lab_due',
                reference_id=None,
                prefer_whatsapp=True
            )

            if result['status'] == 'sent':
                sent += 1
            else:
                failed += 1

        return {'sent': sent, 'failed': failed, 'total': len(overdue)}


def run_daily_reminders(db, clinic_name: str = "Kumar Clinic", clinic_phone: str = ""):
    """Run the daily reminder job.

    This function should be called by a scheduler (cron, Task Scheduler, etc.)
    """
    service = ReminderService(db, clinic_name, clinic_phone)

    # Send appointment reminders
    result = service.send_all_pending_reminders()
    print(f"Appointment reminders: {result['sent']} sent, {result['failed']} failed")

    # Send lab reminders
    lab_result = service.send_lab_reminders()
    print(f"Lab reminders: {lab_result['sent']} sent, {lab_result['failed']} failed")

    return {
        'appointments': result,
        'labs': lab_result
    }
