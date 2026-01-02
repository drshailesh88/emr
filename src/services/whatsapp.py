"""WhatsApp prescription sharing service."""

import urllib.parse
import webbrowser
from datetime import datetime
from typing import Optional
from ..models.schemas import Prescription, Patient


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
    patient: Patient,
    prescription: Prescription,
    clinic_name: str = "Kumar Clinic",
    visit_date: Optional[str] = None
) -> str:
    """Format prescription as WhatsApp message text."""

    date_str = visit_date or datetime.now().strftime("%d-%b-%Y")

    # Build diagnosis string
    diagnosis = ", ".join(prescription.diagnosis) if prescription.diagnosis else "N/A"

    # Build medications list
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

    # Build advice list
    advice_text = ""
    if prescription.advice:
        advice_text = "\n".join(f"• {a}" for a in prescription.advice)

    # Build follow-up
    follow_up = prescription.follow_up or "As needed"

    # Build message using template
    message = f"""📋 *Prescription from {clinic_name}*
━━━━━━━━━━━━━━━━━━

*Patient:* {patient.name}
*Date:* {date_str}

*Diagnosis:* {diagnosis}

*Medications:*
{meds_text}
"""

    if advice_text:
        message += f"""
*Advice:*
{advice_text}
"""

    message += f"""
*Follow-up:* {follow_up}

━━━━━━━━━━━━━━━━━━
_This is a computer-generated prescription._
_Please bring this message to your next visit._"""

    return message


def open_whatsapp_web(phone: str, message: str) -> bool:
    """Open WhatsApp Web with pre-filled message."""
    try:
        # Format phone number
        formatted_phone = format_phone_number(phone)

        if not formatted_phone:
            return False

        # Encode message for URL
        encoded_message = urllib.parse.quote(message)

        # Build WhatsApp Web URL
        whatsapp_url = f"https://wa.me/{formatted_phone}?text={encoded_message}"

        # Open in default browser
        webbrowser.open(whatsapp_url)

        return True
    except Exception:
        return False


def share_prescription_via_whatsapp(
    patient: Patient,
    prescription: Prescription,
    clinic_name: str = "Kumar Clinic",
    visit_date: Optional[str] = None
) -> bool:
    """Share prescription via WhatsApp.

    Args:
        patient: Patient object with phone number
        prescription: Prescription to share
        clinic_name: Name of the clinic
        visit_date: Date of the visit (defaults to today)

    Returns:
        True if WhatsApp was opened successfully
    """
    if not patient.phone:
        return False

    # Format the message
    message = format_prescription_message(
        patient=patient,
        prescription=prescription,
        clinic_name=clinic_name,
        visit_date=visit_date
    )

    # Open WhatsApp
    return open_whatsapp_web(patient.phone, message)
