"""Dialog for sending WhatsApp messages to patients."""

import flet as ft
from typing import Optional, Callable
import asyncio
import threading
from datetime import datetime
from ...models.schemas import Patient, Prescription
from ...services.whatsapp.client import WhatsAppClient, MessageStatus
from ...services.whatsapp_settings import WhatsAppSettingsService
from ...services.whatsapp.templates import MessageTemplates
import logging

logger = logging.getLogger(__name__)


class SendMessageDialog:
    """Dialog for sending WhatsApp messages to patients."""

    def __init__(
        self,
        page: ft.Page,
        patient: Patient,
        whatsapp_client: Optional[WhatsAppClient] = None,
        settings_service: Optional[WhatsAppSettingsService] = None,
        on_sent: Optional[Callable] = None,
        prescription: Optional[Prescription] = None,
        pdf_path: Optional[str] = None
    ):
        """Initialize send message dialog.

        Args:
            page: Flet page
            patient: Patient to send message to
            whatsapp_client: WhatsApp client (optional)
            settings_service: WhatsApp settings service
            on_sent: Callback when message is sent successfully
            prescription: Prescription to include (optional)
            pdf_path: Path to prescription PDF (optional)
        """
        self.page = page
        self.patient = patient
        self.whatsapp_client = whatsapp_client
        self.settings_service = settings_service or WhatsAppSettingsService()
        self.on_sent = on_sent
        self.prescription = prescription
        self.pdf_path = pdf_path

        # UI components
        self.dialog: Optional[ft.AlertDialog] = None
        self.message_type_dropdown: Optional[ft.Dropdown] = None
        self.message_text: Optional[ft.TextField] = None
        self.template_selector: Optional[ft.Dropdown] = None
        self.template_params_column: Optional[ft.Column] = None
        self.preview_text: Optional[ft.Text] = None
        self.phone_field: Optional[ft.TextField] = None
        self.send_btn: Optional[ft.ElevatedButton] = None
        self.status_text: Optional[ft.Text] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None

    def build(self) -> ft.AlertDialog:
        """Build the send message dialog.

        Returns:
            AlertDialog with send message UI
        """
        # Phone number field
        self.phone_field = ft.TextField(
            label="Patient Phone Number",
            value=self.patient.phone or "",
            prefix_text="+91 ",
            hint_text="10-digit mobile number",
            keyboard_type=ft.KeyboardType.PHONE,
            width=300,
        )

        # Message type dropdown
        message_types = ["Text", "Template"]
        if self.prescription and self.pdf_path:
            message_types.append("Prescription PDF")

        self.message_type_dropdown = ft.Dropdown(
            label="Message Type",
            value="Text",
            options=[ft.dropdown.Option(t) for t in message_types],
            width=300,
            on_change=self._on_message_type_change
        )

        # Text message field
        self.message_text = ft.TextField(
            label="Message",
            hint_text="Type your message here...",
            multiline=True,
            min_lines=3,
            max_lines=10,
            width=400,
        )

        # Template selector (hidden by default)
        self.template_selector = ft.Dropdown(
            label="Select Template",
            value=MessageTemplates.APPOINTMENT_REMINDER,
            options=[
                ft.dropdown.Option(MessageTemplates.APPOINTMENT_REMINDER, "Appointment Reminder"),
                ft.dropdown.Option(MessageTemplates.PRESCRIPTION_DELIVERY, "Prescription Ready"),
                ft.dropdown.Option(MessageTemplates.FOLLOW_UP_REMINDER, "Follow-up Reminder"),
                ft.dropdown.Option(MessageTemplates.LAB_RESULT_READY, "Lab Results Ready"),
            ],
            width=400,
            visible=False,
            on_change=self._on_template_change
        )

        # Template parameters (dynamic)
        self.template_params_column = ft.Column(
            visible=False,
            spacing=10
        )

        # Preview section
        self.preview_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_700,
            selectable=True,
        )

        preview_container = ft.Container(
            content=ft.Column([
                ft.Text("Message Preview:", size=12, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=self.preview_text,
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    bgcolor=ft.Colors.GREEN_50,
                )
            ], spacing=5),
            visible=True,
        )

        # Send button
        self.send_btn = ft.ElevatedButton(
            "Send Message",
            icon=ft.Icons.SEND,
            on_click=self._on_send,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            )
        )

        # Status text and loading indicator
        self.status_text = ft.Text(
            "",
            size=12,
            visible=False
        )

        self.loading_indicator = ft.ProgressRing(
            width=20,
            height=20,
            visible=False
        )

        # Check if WhatsApp is configured
        credentials = self.settings_service.get_credentials()
        config_warning = None
        if not credentials.is_configured() or not credentials.enabled:
            config_warning = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER_700, size=20),
                    ft.Text(
                        "WhatsApp not configured. Messages will be logged in mock mode.",
                        size=12,
                        color=ft.Colors.AMBER_700
                    )
                ], spacing=10),
                padding=10,
                border_radius=5,
                bgcolor=ft.Colors.AMBER_50,
                border=ft.border.all(1, ft.Colors.AMBER_200)
            )

        # Build dialog
        content_controls = [
            ft.Text(
                f"Send WhatsApp message to {self.patient.name}",
                size=14,
                weight=ft.FontWeight.W_500
            ),
            ft.Divider(height=10),
        ]

        if config_warning:
            content_controls.append(config_warning)

        content_controls.extend([
            self.phone_field,
            self.message_type_dropdown,
            self.message_text,
            self.template_selector,
            self.template_params_column,
            preview_container,
            ft.Row([
                self.loading_indicator,
                self.send_btn,
            ], spacing=10),
            self.status_text,
        ])

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHAT, color=ft.Colors.GREEN_700, size=24),
                ft.Text("Send WhatsApp Message", size=16, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(
                    content_controls,
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO
                ),
                width=450,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: self._close_dialog(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Update preview
        self._update_preview()

        return self.dialog

    def _on_message_type_change(self, e):
        """Handle message type change."""
        message_type = self.message_type_dropdown.value

        if message_type == "Text":
            self.message_text.visible = True
            self.template_selector.visible = False
            self.template_params_column.visible = False
        elif message_type == "Template":
            self.message_text.visible = False
            self.template_selector.visible = True
            self.template_params_column.visible = True
            self._on_template_change(None)
        elif message_type == "Prescription PDF":
            self.message_text.visible = False
            self.template_selector.visible = False
            self.template_params_column.visible = False

        self._update_preview()
        self.page.update()

    def _on_template_change(self, e):
        """Handle template selection change."""
        # Clear existing params
        self.template_params_column.controls.clear()

        template = self.template_selector.value

        # Add template-specific parameter fields
        if template == MessageTemplates.APPOINTMENT_REMINDER:
            self.template_params_column.controls.extend([
                ft.TextField(label="Appointment Date", hint_text="Monday, 15 January 2024"),
                ft.TextField(label="Appointment Time", hint_text="10:00 AM"),
                ft.TextField(label="Clinic Address", hint_text="123 Main Street"),
            ])
        elif template == MessageTemplates.PRESCRIPTION_DELIVERY:
            self.template_params_column.controls.extend([
                ft.TextField(label="Visit Date", hint_text="15 January 2024"),
                ft.TextField(label="Medication Summary", hint_text="Metformin 500mg BD"),
                ft.TextField(label="Follow-up", hint_text="2 weeks"),
            ])
        elif template == MessageTemplates.FOLLOW_UP_REMINDER:
            self.template_params_column.controls.extend([
                ft.TextField(label="Due Date", hint_text="22 January 2024"),
                ft.TextField(label="Reason", hint_text="Check blood sugar levels"),
            ])
        elif template == MessageTemplates.LAB_RESULT_READY:
            self.template_params_column.controls.extend([
                ft.TextField(label="Test Name", hint_text="HbA1c, Lipid Profile"),
            ])

        self._update_preview()
        self.page.update()

    def _update_preview(self):
        """Update message preview."""
        message_type = self.message_type_dropdown.value

        if message_type == "Text":
            self.preview_text.value = self.message_text.value or "(Type your message above)"
        elif message_type == "Template":
            self.preview_text.value = f"Template: {self.template_selector.value}\n(Preview will be generated when sent)"
        elif message_type == "Prescription PDF":
            self.preview_text.value = f"Prescription PDF will be sent\nFile: {self.pdf_path or 'Not specified'}"

    def _on_send(self, e):
        """Handle send button click."""
        # Validate phone number
        phone = self.phone_field.value.strip()
        if not phone or len(phone.replace(" ", "").replace("-", "")) < 10:
            self._show_status("Please enter a valid phone number", is_error=True)
            return

        # Get credentials
        credentials = self.settings_service.get_credentials()

        if credentials.mock_mode:
            # Mock mode - just log
            self._send_mock_message(phone)
        else:
            # Real send
            self._send_real_message(phone)

    def _send_mock_message(self, phone: str):
        """Send message in mock mode (just log)."""
        self.loading_indicator.visible = True
        self.send_btn.disabled = True
        self.page.update()

        message_type = self.message_type_dropdown.value
        message = ""

        if message_type == "Text":
            message = self.message_text.value
        elif message_type == "Template":
            message = f"Template: {self.template_selector.value}"
        elif message_type == "Prescription PDF":
            message = f"Prescription PDF: {self.pdf_path}"

        # Log the message
        logger.info(f"[MOCK MODE] Would send WhatsApp message to {phone}: {message}")

        # Simulate delay
        import time
        time.sleep(1)

        self._show_status("Message logged (Mock Mode)", is_error=False)
        self.loading_indicator.visible = False
        self.send_btn.disabled = False

        # Show success snackbar
        self.page.open(ft.SnackBar(
            content=ft.Text(f"Mock message logged for {self.patient.name}"),
            bgcolor=ft.Colors.GREEN_700
        ))

        if self.on_sent:
            self.on_sent()

        # Close dialog after 1 second
        threading.Timer(1.0, self._close_dialog).start()

    def _send_real_message(self, phone: str):
        """Send actual WhatsApp message."""
        def send():
            self.loading_indicator.visible = True
            self.send_btn.disabled = True
            self.page.update()

            try:
                # Get or create WhatsApp client
                if not self.whatsapp_client:
                    credentials = self.settings_service.get_credentials()
                    self.whatsapp_client = WhatsAppClient(
                        phone_number_id=credentials.phone_number_id,
                        access_token=credentials.access_token
                    )

                # Send based on type
                message_type = self.message_type_dropdown.value

                if message_type == "Text":
                    # Send text message
                    result = asyncio.run(
                        self.whatsapp_client.send_text(
                            to=phone,
                            message=self.message_text.value
                        )
                    )
                elif message_type == "Prescription PDF" and self.pdf_path:
                    # Upload and send PDF
                    media_result = asyncio.run(
                        self.whatsapp_client.upload_media(
                            file_path=self.pdf_path,
                            mime_type="application/pdf"
                        )
                    )
                    result = asyncio.run(
                        self.whatsapp_client.send_document_by_id(
                            to=phone,
                            media_id=media_result.media_id,
                            filename="prescription.pdf",
                            caption=f"Prescription for {self.patient.name}"
                        )
                    )
                else:
                    # Template message
                    # TODO: Build template components
                    result = asyncio.run(
                        self.whatsapp_client.send_template(
                            to=phone,
                            template_name=self.template_selector.value
                        )
                    )

                # Check result
                if result.status in [MessageStatus.SENT, MessageStatus.DELIVERED]:
                    self._show_status("Message sent successfully!", is_error=False)
                    self.page.open(ft.SnackBar(
                        content=ft.Text(f"Message sent to {self.patient.name}"),
                        bgcolor=ft.Colors.GREEN_700
                    ))

                    if self.on_sent:
                        self.on_sent()

                    # Close dialog after 1 second
                    threading.Timer(1.0, self._close_dialog).start()
                else:
                    self._show_status(f"Failed: {result.error}", is_error=True)

            except Exception as ex:
                logger.error(f"Error sending WhatsApp message: {ex}")
                self._show_status(f"Error: {str(ex)}", is_error=True)

            finally:
                self.loading_indicator.visible = False
                self.send_btn.disabled = False
                self.page.update()

        # Run in thread
        thread = threading.Thread(target=send, daemon=True)
        thread.start()

    def _show_status(self, message: str, is_error: bool = False):
        """Show status message."""
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700
        self.status_text.visible = True
        self.page.update()

    def _close_dialog(self):
        """Close the dialog."""
        if self.dialog:
            self.dialog.open = False
            self.page.update()

    def show(self):
        """Show the dialog."""
        dialog = self.build()
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


def show_send_message_dialog(
    page: ft.Page,
    patient: Patient,
    whatsapp_client: Optional[WhatsAppClient] = None,
    settings_service: Optional[WhatsAppSettingsService] = None,
    on_sent: Optional[Callable] = None,
    prescription: Optional[Prescription] = None,
    pdf_path: Optional[str] = None
):
    """Show send message dialog.

    Args:
        page: Flet page
        patient: Patient to send message to
        whatsapp_client: WhatsApp client (optional)
        settings_service: WhatsApp settings service
        on_sent: Callback when message is sent
        prescription: Prescription to include (optional)
        pdf_path: Path to prescription PDF (optional)
    """
    dialog = SendMessageDialog(
        page=page,
        patient=patient,
        whatsapp_client=whatsapp_client,
        settings_service=settings_service,
        on_sent=on_sent,
        prescription=prescription,
        pdf_path=pdf_path
    )
    dialog.show()
