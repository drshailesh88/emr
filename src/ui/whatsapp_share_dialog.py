"""WhatsApp prescription sharing dialog."""

import flet as ft
from typing import Optional
from datetime import datetime
from ..models.schemas import Patient, Prescription
from ..services.whatsapp import (
    format_phone_number,
    format_prescription_message,
    open_whatsapp_web
)


class WhatsAppShareDialog:
    """Dialog for sharing prescription via WhatsApp."""

    def __init__(
        self,
        patient: Patient,
        prescription: Prescription,
        pdf_path: Optional[str] = None,
        clinic_name: str = "Kumar Clinic",
        on_shared: callable = None
    ):
        self.patient = patient
        self.prescription = prescription
        self.pdf_path = pdf_path
        self.clinic_name = clinic_name
        self.on_shared = on_shared
        self.dialog = None
        self.phone_field = None
        self.message_preview = None

    def _build_dialog(self, page: ft.Page) -> ft.AlertDialog:
        """Build the share dialog."""

        # Phone number field
        phone_value = self.patient.phone or ""
        formatted_phone = format_phone_number(phone_value)

        self.phone_field = ft.TextField(
            label="Patient Phone Number",
            value=phone_value,
            prefix_text="+91 ",
            hint_text="Enter 10-digit mobile number",
            keyboard_type=ft.KeyboardType.PHONE,
            width=300,
        )

        # Format message preview
        message = format_prescription_message(
            patient=self.patient,
            prescription=self.prescription,
            clinic_name=self.clinic_name
        )

        # Message preview (scrollable)
        self.message_preview = ft.Container(
            content=ft.Text(
                message,
                size=11,
                selectable=True,
            ),
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(1, ft.Colors.GREEN_200),
            border_radius=8,
            padding=10,
            width=400,
            height=250,
        )

        # PDF indicator
        pdf_indicator = None
        if self.pdf_path:
            pdf_indicator = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ATTACH_FILE, size=16, color=ft.Colors.BLUE_700),
                    ft.Text(
                        f"PDF ready: {self.pdf_path.split('/')[-1] if '/' in self.pdf_path else self.pdf_path.split(chr(92))[-1]}",
                        size=11,
                        color=ft.Colors.BLUE_700
                    ),
                ], spacing=5),
                bgcolor=ft.Colors.BLUE_50,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                border_radius=5,
            )

        # Note about PDF attachment
        pdf_note = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Note: After clicking 'Open WhatsApp', please:",
                    size=11,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Text(
                    "1. The message will be pre-filled in WhatsApp",
                    size=10,
                    color=ft.Colors.GREY_700,
                ),
                ft.Text(
                    "2. Attach the PDF file using the 📎 icon",
                    size=10,
                    color=ft.Colors.GREY_700,
                ),
                ft.Text(
                    "3. Click Send",
                    size=10,
                    color=ft.Colors.GREY_700,
                ),
            ], spacing=2),
            bgcolor=ft.Colors.AMBER_50,
            padding=10,
            border_radius=5,
            border=ft.border.all(1, ft.Colors.AMBER_200),
        )

        content_controls = [
            ft.Text(
                f"Share prescription with {self.patient.name}",
                size=14,
                weight=ft.FontWeight.W_500,
            ),
            ft.Divider(height=10),
            self.phone_field,
            ft.Text("Message Preview:", size=12, weight=ft.FontWeight.W_500),
            self.message_preview,
        ]

        if pdf_indicator:
            content_controls.append(pdf_indicator)

        content_controls.append(pdf_note)

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHAT, color=ft.Colors.GREEN_700, size=24),
                ft.Text("Share via WhatsApp", size=16, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(content_controls, spacing=15, scroll=ft.ScrollMode.AUTO),
                width=450,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: self._close_dialog(page),
                ),
                ft.ElevatedButton(
                    "Open WhatsApp",
                    icon=ft.Icons.OPEN_IN_NEW,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                    ),
                    on_click=lambda e: self._share(page),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return self.dialog

    def _share(self, page: ft.Page):
        """Handle share button click."""
        phone = self.phone_field.value

        if not phone or len(phone.replace(" ", "").replace("-", "")) < 10:
            page.open(ft.SnackBar(
                content=ft.Text("Please enter a valid phone number"),
                bgcolor=ft.Colors.RED_700,
            ))
            return

        # Get the message
        message = format_prescription_message(
            patient=self.patient,
            prescription=self.prescription,
            clinic_name=self.clinic_name
        )

        # Open WhatsApp
        success = open_whatsapp_web(phone, message)

        if success:
            page.open(ft.SnackBar(
                content=ft.Text("WhatsApp opened. Please attach the PDF and send."),
                bgcolor=ft.Colors.GREEN_700,
            ))

            if self.on_shared:
                self.on_shared()

            self._close_dialog(page)
        else:
            page.open(ft.SnackBar(
                content=ft.Text("Failed to open WhatsApp. Check phone number."),
                bgcolor=ft.Colors.RED_700,
            ))

    def _close_dialog(self, page: ft.Page):
        """Close the dialog."""
        if self.dialog:
            self.dialog.open = False
            page.update()

    def show(self, page: ft.Page):
        """Show the dialog."""
        dialog = self._build_dialog(page)
        page.open(dialog)
        page.update()


def show_whatsapp_share(
    page: ft.Page,
    patient: Patient,
    prescription: Prescription,
    pdf_path: Optional[str] = None,
    clinic_name: str = "Kumar Clinic",
    on_shared: callable = None
):
    """Show WhatsApp share dialog.

    Args:
        page: Flet page
        patient: Patient to share with
        prescription: Prescription to share
        pdf_path: Path to PDF file (optional)
        clinic_name: Name of clinic
        on_shared: Callback when shared successfully
    """
    dialog = WhatsAppShareDialog(
        patient=patient,
        prescription=prescription,
        pdf_path=pdf_path,
        clinic_name=clinic_name,
        on_shared=on_shared
    )
    dialog.show(page)
