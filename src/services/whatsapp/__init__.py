"""WhatsApp Business API integration services"""
from .client import WhatsAppClient, MessageStatus, SendResult, MediaUploadResult
from .templates import MessageTemplates, QuickReplies, TemplateComponent
from .conversation_handler import (
    ConversationHandler,
    IncomingMessage,
    OutgoingResponse,
    ConversationContext,
    ConversationState
)
from .webhook_handler import WebhookHandler, WebhookEvent


import urllib.parse
import webbrowser
from datetime import datetime
from typing import Optional


def format_phone_number(phone: str) -> str:
    """Format phone number for WhatsApp (add India country code)."""
    if not phone:
        return ""

    # Remove common characters
    phone = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Add India country code if not present
    if len(phone) == 10 and phone.isdigit():
        phone = "91" + phone
    elif not phone.startswith("91") and len(phone) == 10:
        phone = "91" + phone

    return phone


def format_prescription_message(
    patient,
    prescription,
    clinic_name: str = "Kumar Clinic",
    visit_date: Optional[str] = None
) -> str:
    """Format prescription as WhatsApp message text."""
    date_str = visit_date or datetime.now().strftime("%d-%b-%Y")
    diagnosis = ", ".join(prescription.diagnosis) if prescription.diagnosis else "N/A"

    meds_lines = []
    if prescription.medications:
        for i, med in enumerate(prescription.medications, 1):
            med_line = f"{i}. {med.drug_name}"
            if med.strength:
                med_line += f" {med.strength}"
            med_line += f" - {med.dose} {med.frequency}"
            if med.duration:
                med_line += f" x {med.duration}"
            if med.instructions:
                med_line += f" ({med.instructions})"
            meds_lines.append(med_line)

    meds_text = "\n".join(meds_lines) if meds_lines else "N/A"
    advice_text = "\n".join(f"• {a}" for a in prescription.advice) if prescription.advice else ""
    follow_up = prescription.follow_up or "As needed"

    message = f"""📋 *Prescription from {clinic_name}*
━━━━━━━━━━━━━━━━━━

*Patient:* {patient.name}
*Date:* {date_str}

*Diagnosis:* {diagnosis}

*Medications:*
{meds_text}
"""
    if advice_text:
        message += f"\n*Advice:*\n{advice_text}\n"

    message += f"""
*Follow-up:* {follow_up}

━━━━━━━━━━━━━━━━━━
_This is a computer-generated prescription._
_Please bring this message to your next visit._"""

    return message


def open_whatsapp_web(phone: str, message: str) -> bool:
    """Open WhatsApp Web with pre-filled message."""
    try:
        formatted_phone = format_phone_number(phone)
        if not formatted_phone:
            return False
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{formatted_phone}?text={encoded_message}"
        webbrowser.open(whatsapp_url)
        return True
    except Exception:
        return False


def share_prescription_via_whatsapp(
    patient,
    prescription,
    clinic_name: str = "Kumar Clinic",
    visit_date: Optional[str] = None
) -> bool:
    """Share prescription via WhatsApp."""
    if not patient.phone:
        return False
    message = format_prescription_message(patient, prescription, clinic_name, visit_date)
    return open_whatsapp_web(patient.phone, message)


__all__ = [
    'WhatsAppClient',
    'MessageStatus',
    'SendResult',
    'MediaUploadResult',
    'MessageTemplates',
    'QuickReplies',
    'TemplateComponent',
    'ConversationHandler',
    'IncomingMessage',
    'OutgoingResponse',
    'ConversationContext',
    'ConversationState',
    'WebhookHandler',
    'WebhookEvent',
    'format_phone_number',
    'format_prescription_message',
    'open_whatsapp_web',
    'share_prescription_via_whatsapp',
]
