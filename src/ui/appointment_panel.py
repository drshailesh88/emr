"""Appointment calendar panel and dialogs."""

import flet as ft
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Callable


# Appointment type colors and durations
APPOINTMENT_TYPES = {
    "new": {"color": ft.Colors.BLUE_600, "label": "New Patient", "duration": 30},
    "follow-up": {"color": ft.Colors.GREEN_600, "label": "Follow-up", "duration": 15},
    "procedure": {"color": ft.Colors.ORANGE_600, "label": "Procedure", "duration": 45},
    "lab-review": {"color": ft.Colors.PURPLE_600, "label": "Lab Review", "duration": 10},
}

# Status colors
STATUS_COLORS = {
    "scheduled": ft.Colors.GREY_600,
    "confirmed": ft.Colors.BLUE_600,
    "arrived": ft.Colors.GREEN_600,
    "in-progress": ft.Colors.ORANGE_600,
    "completed": ft.Colors.GREEN_800,
    "cancelled": ft.Colors.RED_600,
    "no-show": ft.Colors.RED_800,
}


class TodayAppointmentsPanel(ft.UserControl):
    """Compact panel showing today's appointments for sidebar."""

    def __init__(self, db, on_patient_click: Callable[[int], None] = None):
        super().__init__()
        self.db = db
        self.on_patient_click = on_patient_click
        self.appointments_list = None

    def build(self):
        self.appointments_list = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.BLUE_700),
                    ft.Text("TODAY", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                ], spacing=5),
                self.appointments_list,
                ft.TextButton(
                    "+ New Appointment",
                    icon=ft.Icons.ADD,
                    on_click=self._on_new_appointment,
                ),
            ], spacing=8),
            padding=10,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
        )

    def refresh(self):
        """Refresh today's appointments."""
        if not self.appointments_list:
            return

        self.appointments_list.controls.clear()

        # Get today's appointments
        today = date.today().isoformat()
        appointments = self.db.get_appointments_for_date(today)

        if not appointments:
            self.appointments_list.controls.append(
                ft.Text(
                    "No appointments today",
                    size=11,
                    color=ft.Colors.GREY_600,
                    italic=True,
                )
            )
        else:
            for appt in appointments:
                self.appointments_list.controls.append(
                    self._build_appointment_row(appt)
                )

        if self.appointments_list.page:
            self.appointments_list.update()

    def _build_appointment_row(self, appt: Dict) -> ft.Container:
        """Build a single appointment row."""
        appt_type = appt.get("appointment_type", "follow-up")
        type_info = APPOINTMENT_TYPES.get(appt_type, APPOINTMENT_TYPES["follow-up"])
        status = appt.get("status", "scheduled")

        # Status indicator
        status_icon = ft.Icons.CIRCLE
        if status == "completed":
            status_icon = ft.Icons.CHECK_CIRCLE
        elif status == "in-progress":
            status_icon = ft.Icons.PLAY_CIRCLE
        elif status == "arrived":
            status_icon = ft.Icons.LOCATION_ON
        elif status == "cancelled":
            status_icon = ft.Icons.CANCEL
        elif status == "no-show":
            status_icon = ft.Icons.ERROR

        return ft.Container(
            content=ft.Row([
                ft.Text(
                    appt.get("appointment_time", "")[:5] if appt.get("appointment_time") else "",
                    size=11,
                    weight=ft.FontWeight.W_500,
                    width=45,
                ),
                ft.Icon(status_icon, size=12, color=type_info["color"]),
                ft.Text(
                    appt.get("patient_name", "Unknown"),
                    size=11,
                    expand=True,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    type_info["label"][:3],
                    size=9,
                    color=ft.Colors.GREY_600,
                ),
            ], spacing=5),
            padding=ft.padding.symmetric(horizontal=5, vertical=3),
            border_radius=4,
            bgcolor=ft.Colors.WHITE,
            ink=True,
            on_click=lambda e, pid=appt.get("patient_id"): self._on_appointment_click(pid),
        )

    def _on_appointment_click(self, patient_id: int):
        """Handle appointment click."""
        if self.on_patient_click and patient_id:
            self.on_patient_click(patient_id)

    def _on_new_appointment(self, e):
        """Handle new appointment button."""
        if e.page:
            dialog = NewAppointmentDialog(self.db, on_save=lambda: self.refresh())
            dialog.show(e.page)


class NewAppointmentDialog:
    """Dialog for creating a new appointment."""

    def __init__(self, db, patient_id: int = None, suggested_date: str = None, on_save: Callable = None):
        self.db = db
        self.patient_id = patient_id
        self.suggested_date = suggested_date
        self.on_save = on_save
        self.dialog = None
        self.patient_dropdown = None
        self.date_picker = None
        self.time_dropdown = None
        self.type_dropdown = None
        self.notes_field = None

    def _build_dialog(self, page: ft.Page) -> ft.AlertDialog:
        """Build the dialog."""

        # Get all patients for dropdown
        patients = self.db.search_patients("", limit=500)
        patient_options = [
            ft.dropdown.Option(key=str(p.id), text=f"{p.name} ({p.uhid or 'No UHID'})")
            for p in patients
        ]

        self.patient_dropdown = ft.Dropdown(
            label="Patient",
            options=patient_options,
            value=str(self.patient_id) if self.patient_id else None,
            width=300,
        )

        # Date field
        default_date = self.suggested_date or date.today().isoformat()
        self.date_field = ft.TextField(
            label="Date",
            value=default_date,
            hint_text="YYYY-MM-DD",
            width=150,
        )

        # Time dropdown
        time_options = []
        for hour in range(8, 20):
            for minute in [0, 15, 30, 45]:
                time_str = f"{hour:02d}:{minute:02d}"
                time_options.append(ft.dropdown.Option(time_str))

        self.time_dropdown = ft.Dropdown(
            label="Time",
            options=time_options,
            value="09:00",
            width=120,
        )

        # Type dropdown
        type_options = [
            ft.dropdown.Option(key=key, text=info["label"])
            for key, info in APPOINTMENT_TYPES.items()
        ]

        self.type_dropdown = ft.Dropdown(
            label="Type",
            options=type_options,
            value="follow-up",
            width=150,
        )

        # Notes
        self.notes_field = ft.TextField(
            label="Notes (optional)",
            hint_text="e.g., DM follow-up with labs",
            width=300,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Schedule Appointment"),
            content=ft.Container(
                content=ft.Column([
                    self.patient_dropdown,
                    ft.Row([self.date_field, self.time_dropdown], spacing=10),
                    self.type_dropdown,
                    self.notes_field,
                ], spacing=15),
                width=350,
                height=280,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close(page)),
                ft.ElevatedButton(
                    "Schedule",
                    on_click=lambda e: self._save(page),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                ),
            ],
        )

        return self.dialog

    def _save(self, page: ft.Page):
        """Save the appointment."""
        if not self.patient_dropdown.value:
            page.open(ft.SnackBar(ft.Text("Please select a patient"), bgcolor=ft.Colors.RED_700))
            return

        result = self.db.add_appointment(
            patient_id=int(self.patient_dropdown.value),
            date=self.date_field.value,
            time=self.time_dropdown.value,
            appt_type=self.type_dropdown.value,
            notes=self.notes_field.value or "",
        )

        if result:
            page.open(ft.SnackBar(ft.Text("Appointment scheduled"), bgcolor=ft.Colors.GREEN_700))
            if self.on_save:
                self.on_save()
            self._close(page)
        else:
            page.open(ft.SnackBar(ft.Text("Failed to schedule"), bgcolor=ft.Colors.RED_700))

    def _close(self, page: ft.Page):
        """Close the dialog."""
        if self.dialog:
            self.dialog.open = False
            page.update()

    def show(self, page: ft.Page):
        """Show the dialog."""
        dialog = self._build_dialog(page)
        page.open(dialog)
        page.update()


class ScheduleFollowupDialog:
    """Quick dialog to schedule a follow-up after visit."""

    def __init__(self, db, patient, suggested_days: int = 14, on_save: Callable = None):
        self.db = db
        self.patient = patient
        self.suggested_days = suggested_days
        self.on_save = on_save
        self.dialog = None

    def _build_dialog(self, page: ft.Page) -> ft.AlertDialog:
        """Build the dialog."""
        # Calculate suggested date
        suggested_date = date.today() + timedelta(days=self.suggested_days)

        self.date_field = ft.TextField(
            label="Follow-up Date",
            value=suggested_date.isoformat(),
            hint_text="YYYY-MM-DD",
            width=150,
        )

        # Time dropdown
        time_options = [ft.dropdown.Option(f"{h:02d}:00") for h in range(8, 20)]

        self.time_dropdown = ft.Dropdown(
            label="Time",
            options=time_options,
            value="10:00",
            width=120,
        )

        # Quick date buttons
        quick_dates = ft.Row([
            ft.TextButton("1 week", on_click=lambda e: self._set_days(7)),
            ft.TextButton("2 weeks", on_click=lambda e: self._set_days(14)),
            ft.TextButton("1 month", on_click=lambda e: self._set_days(30)),
            ft.TextButton("3 months", on_click=lambda e: self._set_days(90)),
        ], spacing=0)

        self.notes_field = ft.TextField(
            label="Notes",
            hint_text="e.g., Bring lab reports",
            width=280,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.BLUE_700),
                ft.Text("Schedule Follow-up"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Patient: {self.patient.name}", weight=ft.FontWeight.W_500),
                    ft.Text(f"Suggested: {self.suggested_days} days", size=12, color=ft.Colors.GREY_600),
                    quick_dates,
                    ft.Divider(),
                    ft.Row([self.date_field, self.time_dropdown], spacing=10),
                    self.notes_field,
                ], spacing=10),
                width=320,
                height=220,
            ),
            actions=[
                ft.TextButton("Skip", on_click=lambda e: self._close(page)),
                ft.ElevatedButton(
                    "Schedule",
                    on_click=lambda e: self._save(page),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                ),
            ],
        )

        return self.dialog

    def _set_days(self, days: int):
        """Set date based on days from today."""
        new_date = date.today() + timedelta(days=days)
        self.date_field.value = new_date.isoformat()
        if self.date_field.page:
            self.date_field.update()

    def _save(self, page: ft.Page):
        """Save the follow-up."""
        result = self.db.add_appointment(
            patient_id=self.patient.id,
            date=self.date_field.value,
            time=self.time_dropdown.value,
            appt_type="follow-up",
            notes=self.notes_field.value or "",
        )

        if result:
            page.open(ft.SnackBar(ft.Text("Follow-up scheduled"), bgcolor=ft.Colors.GREEN_700))
            if self.on_save:
                self.on_save()
            self._close(page)
        else:
            page.open(ft.SnackBar(ft.Text("Failed to schedule"), bgcolor=ft.Colors.RED_700))

    def _close(self, page: ft.Page):
        """Close the dialog."""
        if self.dialog:
            self.dialog.open = False
            page.update()

    def show(self, page: ft.Page):
        """Show the dialog."""
        dialog = self._build_dialog(page)
        page.open(dialog)
        page.update()


class CalendarView(ft.UserControl):
    """Weekly calendar view for appointments."""

    def __init__(self, db, on_patient_click: Callable[[int], None] = None):
        super().__init__()
        self.db = db
        self.on_patient_click = on_patient_click
        self.current_week_start = self._get_week_start(date.today())
        self.calendar_container = None

    def _get_week_start(self, d: date) -> date:
        """Get Monday of the week containing the given date."""
        return d - timedelta(days=d.weekday())

    def build(self):
        self.calendar_container = ft.Container(
            content=self._build_week_view(),
            expand=True,
        )

        return ft.Column([
            # Navigation header
            ft.Row([
                ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=self._prev_week),
                ft.Text(
                    self._get_week_label(),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=self._next_week),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Today",
                    on_click=self._goto_today,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.calendar_container,
        ], spacing=10, expand=True)

    def _get_week_label(self) -> str:
        """Get label for current week."""
        end = self.current_week_start + timedelta(days=6)
        if self.current_week_start.month == end.month:
            return f"{self.current_week_start.strftime('%d')} - {end.strftime('%d %B %Y')}"
        else:
            return f"{self.current_week_start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"

    def _build_week_view(self) -> ft.Control:
        """Build the weekly calendar grid."""
        days = []

        for i in range(7):
            day = self.current_week_start + timedelta(days=i)
            is_today = day == date.today()
            is_weekend = i >= 5

            # Get appointments for this day
            appointments = self.db.get_appointments_for_date(day.isoformat())

            # Day header
            header_bg = ft.Colors.BLUE_100 if is_today else (ft.Colors.GREY_100 if is_weekend else ft.Colors.WHITE)

            day_column = ft.Container(
                content=ft.Column([
                    # Day header
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                day.strftime("%a"),
                                size=11,
                                weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL,
                            ),
                            ft.Text(
                                day.strftime("%d"),
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_700 if is_today else None,
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        padding=5,
                        bgcolor=header_bg,
                    ),
                    # Appointments
                    ft.Container(
                        content=ft.Column(
                            [self._build_calendar_appointment(appt) for appt in appointments],
                            spacing=2,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=3,
                        expand=True,
                    ),
                ], spacing=0, expand=True),
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5,
                expand=True,
            )

            days.append(day_column)

        return ft.Row(days, spacing=5, expand=True)

    def _build_calendar_appointment(self, appt: Dict) -> ft.Container:
        """Build a single appointment for the calendar."""
        appt_type = appt.get("appointment_type", "follow-up")
        type_info = APPOINTMENT_TYPES.get(appt_type, APPOINTMENT_TYPES["follow-up"])
        status = appt.get("status", "scheduled")

        # Dimmed if completed/cancelled
        opacity = 0.5 if status in ["completed", "cancelled", "no-show"] else 1.0

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    appt.get("appointment_time", "")[:5] if appt.get("appointment_time") else "",
                    size=9,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    appt.get("patient_name", "Unknown")[:12],
                    size=10,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ], spacing=1),
            padding=ft.padding.all(4),
            bgcolor=type_info["color"],
            border_radius=4,
            opacity=opacity,
            ink=True,
            on_click=lambda e, pid=appt.get("patient_id"): self._on_click(pid),
        )

    def _on_click(self, patient_id: int):
        """Handle appointment click."""
        if self.on_patient_click and patient_id:
            self.on_patient_click(patient_id)

    def _prev_week(self, e):
        """Go to previous week."""
        self.current_week_start -= timedelta(days=7)
        self._refresh()

    def _next_week(self, e):
        """Go to next week."""
        self.current_week_start += timedelta(days=7)
        self._refresh()

    def _goto_today(self, e):
        """Go to current week."""
        self.current_week_start = self._get_week_start(date.today())
        self._refresh()

    def _refresh(self):
        """Refresh the calendar view."""
        if self.calendar_container:
            self.calendar_container.content = self._build_week_view()
            if self.calendar_container.page:
                self.calendar_container.update()

    def refresh(self):
        """Public refresh method."""
        self._refresh()


def show_schedule_followup(page: ft.Page, db, patient, suggested_days: int = 14, on_save: Callable = None):
    """Show the schedule follow-up dialog."""
    dialog = ScheduleFollowupDialog(db, patient, suggested_days, on_save)
    dialog.show(page)


def show_new_appointment(page: ft.Page, db, patient_id: int = None, on_save: Callable = None):
    """Show the new appointment dialog."""
    dialog = NewAppointmentDialog(db, patient_id=patient_id, on_save=on_save)
    dialog.show(page)
