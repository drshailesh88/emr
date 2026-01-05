"""Reminder scheduler UI for WhatsApp appointment reminders."""

import flet as ft
from typing import Callable, Optional, List, Dict
from datetime import datetime, timedelta, date, time
import logging
from ...models.schemas import Patient
from ...services.communications.notification_queue import (
    NotificationQueue,
    Notification,
    NotificationPriority,
    NotificationStatus
)
from ...services.whatsapp.templates import MessageTemplates

logger = logging.getLogger(__name__)


class ReminderScheduler(ft.UserControl):
    """UI component for scheduling WhatsApp appointment reminders."""

    def __init__(
        self,
        page: ft.Page,
        notification_queue: NotificationQueue,
        db_service,
        on_reminder_scheduled: Optional[Callable] = None
    ):
        """Initialize reminder scheduler.

        Args:
            page: Flet page
            notification_queue: Notification queue service
            db_service: Database service
            on_reminder_scheduled: Callback when reminder is scheduled
        """
        super().__init__()
        self.page = page
        self.notification_queue = notification_queue
        self.db_service = db_service
        self.on_reminder_scheduled = on_reminder_scheduled

        # State
        self.appointments: List[Dict] = []
        self.scheduled_reminders: List[Notification] = []

        # UI components
        self.appointments_list: Optional[ft.ListView] = None
        self.reminder_time_dropdown: Optional[ft.Dropdown] = None
        self.bulk_schedule_btn: Optional[ft.ElevatedButton] = None
        self.status_text: Optional[ft.Text] = None

    def build(self):
        """Build the reminder scheduler UI."""
        # Reminder time options
        self.reminder_time_dropdown = ft.Dropdown(
            label="Send Reminder",
            value="1_day_before",
            options=[
                ft.dropdown.Option("2_hours_before", "2 hours before"),
                ft.dropdown.Option("4_hours_before", "4 hours before"),
                ft.dropdown.Option("1_day_before", "1 day before"),
                ft.dropdown.Option("2_days_before", "2 days before"),
                ft.dropdown.Option("3_days_before", "3 days before"),
            ],
            width=200
        )

        # Appointments list
        self.appointments_list = ft.ListView(
            spacing=10,
            expand=True
        )

        # Bulk schedule button
        self.bulk_schedule_btn = ft.ElevatedButton(
            "Schedule Reminders for All",
            icon=ft.Icons.SCHEDULE_SEND,
            on_click=self._on_bulk_schedule,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE
            )
        )

        # Status text
        self.status_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
            visible=False
        )

        # Load appointments
        self._load_appointments()

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Schedule Appointment Reminders",
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Divider(height=10),

                ft.Row([
                    ft.Text("Default Reminder Time:", size=14),
                    self.reminder_time_dropdown,
                ], spacing=10),

                ft.Container(height=10),

                ft.Text(
                    "Upcoming Appointments:",
                    size=14,
                    weight=ft.FontWeight.W_500
                ),

                ft.Container(
                    content=self.appointments_list,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    padding=10,
                    expand=True
                ),

                ft.Row([
                    self.bulk_schedule_btn,
                    self.status_text,
                ], spacing=10),

            ], spacing=15),
            padding=20,
            expand=True
        )

    def _load_appointments(self):
        """Load upcoming appointments from database."""
        # Mock data - in production, load from database
        # TODO: Add appointments table and load real data
        today = datetime.now().date()

        self.appointments = [
            {
                "id": 1,
                "patient_id": 1,
                "patient_name": "Rajesh Kumar",
                "patient_phone": "9876543210",
                "appointment_date": today + timedelta(days=2),
                "appointment_time": "10:00 AM",
                "reminder_scheduled": False
            },
            {
                "id": 2,
                "patient_id": 2,
                "patient_name": "Priya Sharma",
                "patient_phone": "9876543211",
                "appointment_date": today + timedelta(days=3),
                "appointment_time": "11:30 AM",
                "reminder_scheduled": False
            },
            {
                "id": 3,
                "patient_id": 3,
                "patient_name": "Amit Patel",
                "patient_phone": "9876543212",
                "appointment_date": today + timedelta(days=5),
                "appointment_time": "2:00 PM",
                "reminder_scheduled": True
            },
        ]

        self._update_appointments_list()

    def _update_appointments_list(self):
        """Update the appointments list view."""
        if not self.appointments_list:
            return

        self.appointments_list.controls.clear()

        if not self.appointments:
            self.appointments_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(
                            ft.Icons.EVENT_BUSY,
                            size=48,
                            color=ft.Colors.GREY_400
                        ),
                        ft.Text(
                            "No upcoming appointments",
                            size=14,
                            color=ft.Colors.GREY_500
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            self.update()
            return

        for appointment in self.appointments:
            # Calculate days until appointment
            days_until = (appointment["appointment_date"] - datetime.now().date()).days

            if days_until < 0:
                continue  # Skip past appointments

            # Format date string
            date_str = appointment["appointment_date"].strftime("%A, %d %B %Y")

            # Reminder status
            if appointment["reminder_scheduled"]:
                reminder_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=20)
                reminder_text = ft.Text("Reminder scheduled", size=11, color=ft.Colors.GREEN_700)
                schedule_btn_disabled = True
            else:
                reminder_icon = ft.Icon(ft.Icons.SCHEDULE, color=ft.Colors.GREY_600, size=20)
                reminder_text = ft.Text("Not scheduled", size=11, color=ft.Colors.GREY_600)
                schedule_btn_disabled = False

            appointment_item = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(
                                appointment["patient_name"],
                                size=14,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Text(
                                f"{date_str} at {appointment['appointment_time']}",
                                size=12,
                                color=ft.Colors.GREY_600
                            ),
                            ft.Text(
                                f"In {days_until} day{'s' if days_until != 1 else ''}",
                                size=11,
                                color=ft.Colors.BLUE_700
                            ),
                        ], spacing=2, expand=True),
                        ft.Column([
                            ft.Row([reminder_icon, reminder_text], spacing=5),
                            ft.ElevatedButton(
                                "Schedule Reminder",
                                icon=ft.Icons.SEND,
                                on_click=lambda e, apt=appointment: self._on_schedule_single(apt),
                                disabled=schedule_btn_disabled,
                                height=32,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_600,
                                    color=ft.Colors.WHITE,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5)
                                )
                            )
                        ], spacing=5)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], spacing=5),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5,
                bgcolor=ft.Colors.WHITE
            )

            self.appointments_list.controls.append(appointment_item)

        self.update()

    def _on_schedule_single(self, appointment: Dict):
        """Schedule reminder for a single appointment."""
        try:
            # Calculate when to send reminder
            reminder_time_option = self.reminder_time_dropdown.value
            scheduled_datetime = self._calculate_reminder_time(
                appointment["appointment_date"],
                appointment["appointment_time"],
                reminder_time_option
            )

            # Create notification
            message = self._generate_reminder_message(appointment)

            notification = Notification(
                patient_id=appointment["patient_id"],
                phone=appointment["patient_phone"],
                message=message,
                priority=NotificationPriority.NORMAL,
                scheduled_for=scheduled_datetime,
                channel="whatsapp",
                metadata={
                    "type": "appointment_reminder",
                    "appointment_id": appointment["id"],
                    "appointment_date": appointment["appointment_date"].isoformat(),
                    "appointment_time": appointment["appointment_time"]
                }
            )

            # Enqueue notification
            notification_id = self.notification_queue.enqueue(notification)

            # Mark appointment as scheduled
            appointment["reminder_scheduled"] = True

            # Update UI
            self._update_appointments_list()
            self._show_status(f"Reminder scheduled for {appointment['patient_name']}", is_error=False)

            logger.info(f"Scheduled reminder {notification_id} for appointment {appointment['id']}")

            if self.on_reminder_scheduled:
                self.on_reminder_scheduled()

        except Exception as e:
            logger.error(f"Error scheduling reminder: {e}")
            self._show_status(f"Error: {str(e)}", is_error=True)

    def _on_bulk_schedule(self, e):
        """Schedule reminders for all unscheduled appointments."""
        unscheduled = [apt for apt in self.appointments if not apt["reminder_scheduled"]]

        if not unscheduled:
            self._show_status("All appointments already have reminders scheduled", is_error=False)
            return

        scheduled_count = 0
        for appointment in unscheduled:
            try:
                self._on_schedule_single(appointment)
                scheduled_count += 1
            except Exception as ex:
                logger.error(f"Error scheduling reminder for {appointment['patient_name']}: {ex}")

        self._show_status(
            f"Scheduled {scheduled_count} reminder{'s' if scheduled_count != 1 else ''}",
            is_error=False
        )

    def _calculate_reminder_time(
        self,
        appointment_date: date,
        appointment_time_str: str,
        reminder_option: str
    ) -> datetime:
        """Calculate when to send the reminder."""
        # Parse appointment time
        try:
            apt_time = datetime.strptime(appointment_time_str, "%I:%M %p").time()
        except:
            apt_time = time(10, 0)  # Default to 10:00 AM

        # Combine date and time
        appointment_datetime = datetime.combine(appointment_date, apt_time)

        # Calculate reminder time based on option
        if reminder_option == "2_hours_before":
            reminder_datetime = appointment_datetime - timedelta(hours=2)
        elif reminder_option == "4_hours_before":
            reminder_datetime = appointment_datetime - timedelta(hours=4)
        elif reminder_option == "1_day_before":
            reminder_datetime = appointment_datetime - timedelta(days=1)
        elif reminder_option == "2_days_before":
            reminder_datetime = appointment_datetime - timedelta(days=2)
        elif reminder_option == "3_days_before":
            reminder_datetime = appointment_datetime - timedelta(days=3)
        else:
            reminder_datetime = appointment_datetime - timedelta(days=1)

        return reminder_datetime

    def _generate_reminder_message(self, appointment: Dict) -> str:
        """Generate reminder message text."""
        date_str = appointment["appointment_date"].strftime("%A, %d %B %Y")

        message = f"""Dear {appointment['patient_name']},

This is a reminder for your appointment.

📅 Date: {date_str}
🕐 Time: {appointment['appointment_time']}
📍 Location: Kumar Clinic, Main Street

Please arrive 10 minutes early. If you need to reschedule, please contact us.

Thank you!
- Kumar Clinic"""

        return message

    def _show_status(self, message: str, is_error: bool = False):
        """Show status message."""
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700
        self.status_text.visible = True
        self.update()

    def refresh(self):
        """Refresh appointments list."""
        self._load_appointments()


class ReminderSchedulerDialog:
    """Dialog for scheduling appointment reminders."""

    def __init__(
        self,
        page: ft.Page,
        notification_queue: NotificationQueue,
        db_service,
        on_reminder_scheduled: Optional[Callable] = None
    ):
        """Initialize reminder scheduler dialog.

        Args:
            page: Flet page
            notification_queue: Notification queue service
            db_service: Database service
            on_reminder_scheduled: Callback when reminder is scheduled
        """
        self.page = page
        self.notification_queue = notification_queue
        self.db_service = db_service
        self.on_reminder_scheduled = on_reminder_scheduled
        self.dialog: Optional[ft.AlertDialog] = None

    def show(self):
        """Show the reminder scheduler dialog."""
        scheduler = ReminderScheduler(
            page=self.page,
            notification_queue=self.notification_queue,
            db_service=self.db_service,
            on_reminder_scheduled=self.on_reminder_scheduled
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Schedule Appointment Reminders"),
            content=ft.Container(
                content=scheduler,
                width=600,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda e: self._close_dialog()
                ),
            ]
        )

        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _close_dialog(self):
        """Close the dialog."""
        if self.dialog:
            self.dialog.open = False
            self.page.update()


def show_reminder_scheduler(
    page: ft.Page,
    notification_queue: NotificationQueue,
    db_service,
    on_reminder_scheduled: Optional[Callable] = None
):
    """Show reminder scheduler dialog.

    Args:
        page: Flet page
        notification_queue: Notification queue service
        db_service: Database service
        on_reminder_scheduled: Callback when reminder is scheduled
    """
    dialog = ReminderSchedulerDialog(
        page=page,
        notification_queue=notification_queue,
        db_service=db_service,
        on_reminder_scheduled=on_reminder_scheduled
    )
    dialog.show()
