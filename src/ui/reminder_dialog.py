"""Reminder settings and management dialogs."""

import flet as ft
from typing import Optional, Callable
from datetime import datetime

from ..services.reminders import ReminderService


class ReminderSettingsDialog:
    """Dialog for patient reminder settings."""

    def __init__(self, db, patient_id: int, patient_name: str, on_save: Callable = None):
        self.db = db
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.on_save = on_save
        self.dialog = None

    def _build_dialog(self, page: ft.Page) -> ft.AlertDialog:
        """Build the settings dialog."""
        # Get current preferences
        prefs = self.db.get_patient_preferences(self.patient_id) or {}

        # Reminder enabled checkbox
        self.enabled_checkbox = ft.Checkbox(
            label="Enable appointment reminders",
            value=not prefs.get('reminder_opted_out', False),
        )

        # Channel selection
        preferred = prefs.get('preferred_channel', 'whatsapp')
        self.channel_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="whatsapp", label="WhatsApp"),
                ft.Radio(value="sms", label="SMS"),
                ft.Radio(value="both", label="Both"),
            ]),
            value=preferred,
        )

        # Timing selection
        timing = prefs.get('reminder_timing', '1_day')
        self.timing_1day = ft.Checkbox(
            label="1 day before",
            value='1_day' in timing,
        )
        self.timing_1hour = ft.Checkbox(
            label="1 hour before",
            value='1_hour' in timing,
        )

        # Clinical reminders
        self.clinical_checkbox = ft.Checkbox(
            label="Enable clinical reminders (lab due, screening)",
            value=prefs.get('clinical_reminders', 1) == 1,
        )

        # Reminder history
        history = self.db.get_reminder_history(self.patient_id, limit=5)
        history_items = []
        for log in history:
            status_icon = ft.Icons.CHECK_CIRCLE if log['status'] == 'sent' else ft.Icons.ERROR
            status_color = ft.Colors.GREEN_700 if log['status'] == 'sent' else ft.Colors.RED_700
            sent_at = log.get('sent_at', '')[:16] if log.get('sent_at') else ''

            history_items.append(ft.Container(
                content=ft.Row([
                    ft.Icon(status_icon, size=14, color=status_color),
                    ft.Text(log.get('reminder_type', '').title(), size=11, width=80),
                    ft.Text(log.get('channel', '').upper(), size=10, width=50),
                    ft.Text(sent_at, size=10, color=ft.Colors.GREY_600),
                ], spacing=10),
                padding=5,
            ))

        # Build history column content
        history_content = [ft.Text("Recent Reminders", size=12, weight=ft.FontWeight.BOLD)]
        if history_items:
            history_content.extend(history_items)
        else:
            history_content.append(
                ft.Text("No reminders sent yet", size=11, italic=True, color=ft.Colors.GREY_600)
            )

        history_section = ft.Container(
            content=ft.Column(history_content, spacing=5),
            padding=10,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.NOTIFICATIONS, color=ft.Colors.BLUE_700),
                ft.Text(f"Reminder Settings"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Patient: {self.patient_name}", weight=ft.FontWeight.W_500),
                    ft.Divider(),
                    self.enabled_checkbox,
                    ft.Container(height=10),
                    ft.Text("Preferred Channel:", size=12, weight=ft.FontWeight.W_500),
                    self.channel_radio,
                    ft.Container(height=10),
                    ft.Text("Reminder Timing:", size=12, weight=ft.FontWeight.W_500),
                    self.timing_1day,
                    self.timing_1hour,
                    ft.Container(height=10),
                    self.clinical_checkbox,
                    ft.Divider(),
                    history_section,
                ], spacing=5, scroll=ft.ScrollMode.AUTO),
                width=380,
                height=420,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close(page)),
                ft.ElevatedButton(
                    "Save",
                    on_click=lambda e: self._save(page),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                ),
            ],
        )

        return self.dialog

    def _save(self, page: ft.Page):
        """Save preferences."""
        # Build timing string
        timing_parts = []
        if self.timing_1day.value:
            timing_parts.append('1_day')
        if self.timing_1hour.value:
            timing_parts.append('1_hour')
        timing = ','.join(timing_parts) if timing_parts else '1_day'

        prefs = {
            'reminder_opted_out': 0 if self.enabled_checkbox.value else 1,
            'preferred_channel': self.channel_radio.value,
            'reminder_timing': timing,
            'clinical_reminders': 1 if self.clinical_checkbox.value else 0,
        }

        self.db.set_patient_preferences(self.patient_id, prefs)

        page.open(ft.SnackBar(
            ft.Text("Reminder settings saved"),
            bgcolor=ft.Colors.GREEN_700
        ))

        if self.on_save:
            self.on_save()

        self._close(page)

    def _close(self, page: ft.Page):
        if self.dialog:
            self.dialog.open = False
            page.update()

    def show(self, page: ft.Page):
        dialog = self._build_dialog(page)
        page.open(dialog)
        page.update()


class SendRemindersDialog:
    """Dialog for sending pending reminders."""

    def __init__(self, db, clinic_name: str = "Kumar Clinic", clinic_phone: str = ""):
        self.db = db
        self.clinic_name = clinic_name
        self.clinic_phone = clinic_phone
        self.dialog = None
        self.progress_text = None
        self.progress_bar = None
        self.result_text = None
        self.send_btn = None

    def _build_dialog(self, page: ft.Page) -> ft.AlertDialog:
        """Build the send reminders dialog."""
        pending_count = self.db.get_pending_reminder_count(days_ahead=1)

        self.progress_text = ft.Text(
            f"{pending_count} reminders pending for tomorrow",
            size=14,
        )

        self.progress_bar = ft.ProgressBar(
            width=300,
            visible=False,
        )

        self.result_text = ft.Text(
            "",
            size=12,
            visible=False,
        )

        self.send_btn = ft.ElevatedButton(
            "Send All Reminders",
            icon=ft.Icons.SEND,
            on_click=lambda e: self._send_reminders(page),
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            disabled=pending_count == 0,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color=ft.Colors.GREEN_700),
                ft.Text("Send Reminders"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    self.progress_text,
                    ft.Container(height=10),
                    self.progress_bar,
                    self.result_text,
                    ft.Container(height=10),
                    ft.Text(
                        "Reminders will be sent via WhatsApp (opens in browser).\n"
                        "You'll need to click Send in WhatsApp for each message.",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                ], spacing=5),
                width=350,
                height=180,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close(page)),
                self.send_btn,
            ],
        )

        return self.dialog

    def _send_reminders(self, page: ft.Page):
        """Send all pending reminders."""
        self.send_btn.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = None  # Indeterminate
        page.update()

        # Create reminder service
        service = ReminderService(self.db, self.clinic_name, self.clinic_phone)

        def on_progress(current: int, total: int, patient_name: str):
            self.progress_text.value = f"Sending {current}/{total}: {patient_name}"
            self.progress_bar.value = current / total if total > 0 else 0
            if page:
                page.update()

        # Send reminders
        result = service.send_all_pending_reminders(on_progress=on_progress)

        # Show result
        self.progress_bar.visible = False
        self.result_text.visible = True
        self.result_text.value = f"Sent: {result['sent']} | Failed: {result['failed']}"
        self.result_text.color = ft.Colors.GREEN_700 if result['failed'] == 0 else ft.Colors.ORANGE_700
        self.progress_text.value = "Complete!"

        page.update()

    def _close(self, page: ft.Page):
        if self.dialog:
            self.dialog.open = False
            page.update()

    def show(self, page: ft.Page):
        dialog = self._build_dialog(page)
        page.open(dialog)
        page.update()


class ReminderQueuePanel(ft.UserControl):
    """Panel showing pending reminders queue."""

    def __init__(self, db, on_patient_click: Callable[[int], None] = None):
        super().__init__()
        self.db = db
        self.on_patient_click = on_patient_click
        self.queue_list = None

    def build(self):
        self.queue_list = ft.Column(spacing=5)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SCHEDULE_SEND, size=16, color=ft.Colors.ORANGE_700),
                    ft.Text("Pending Reminders", size=12, weight=ft.FontWeight.BOLD),
                ], spacing=5),
                self.queue_list,
            ], spacing=10),
            padding=10,
            bgcolor=ft.Colors.ORANGE_50,
            border_radius=8,
        )

    def refresh(self):
        """Refresh the queue."""
        if not self.queue_list:
            return

        self.queue_list.controls.clear()

        # Get pending reminders
        from datetime import date, timedelta
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        appointments = self.db.get_appointments_for_date(tomorrow)

        if not appointments:
            self.queue_list.controls.append(
                ft.Text("No reminders pending", size=11, italic=True, color=ft.Colors.GREY_600)
            )
        else:
            for appt in appointments[:5]:  # Show max 5
                prefs = self.db.get_patient_preferences(appt['patient_id'])
                if prefs and prefs.get('reminder_opted_out'):
                    continue

                self.queue_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(
                                appt.get('patient_name', 'Unknown')[:15],
                                size=11,
                                expand=True,
                            ),
                            ft.Text(
                                appt.get('appointment_time', '')[:5],
                                size=10,
                                color=ft.Colors.GREY_600,
                            ),
                        ]),
                        padding=5,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=4,
                        ink=True,
                        on_click=lambda e, pid=appt['patient_id']: self._on_click(pid),
                    )
                )

            if len(appointments) > 5:
                self.queue_list.controls.append(
                    ft.Text(f"+{len(appointments) - 5} more", size=10, color=ft.Colors.GREY_600)
                )

        if self.queue_list.page:
            self.queue_list.update()

    def _on_click(self, patient_id: int):
        if self.on_patient_click:
            self.on_patient_click(patient_id)


def show_reminder_settings(page: ft.Page, db, patient_id: int, patient_name: str, on_save: Callable = None):
    """Show reminder settings dialog for a patient."""
    dialog = ReminderSettingsDialog(db, patient_id, patient_name, on_save)
    dialog.show(page)


def show_send_reminders(page: ft.Page, db, clinic_name: str = "Kumar Clinic", clinic_phone: str = ""):
    """Show send reminders dialog."""
    dialog = SendRemindersDialog(db, clinic_name, clinic_phone)
    dialog.show(page)
