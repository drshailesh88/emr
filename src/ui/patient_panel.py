"""
Left panel - Patient list and search with premium styling.

Uses design tokens for consistent, premium appearance.
"""

import flet as ft
from typing import List, Callable, Optional

from ..models.schemas import Patient
from ..services.database import DatabaseService
from ..services.rag import RAGService
from .dialogs import ConfirmationDialog
from .appointment_panel import TodayAppointmentsPanel

# Import premium design system
from .themes import (
    get_panel_colors,
    get_button_style,
    Colors,
    Typography,
    Spacing,
    Radius,
)


class PatientPanel:
    """Patient list panel with search functionality and premium styling."""

    def __init__(
        self,
        on_patient_selected: Callable[[Patient], None],
        on_search: Callable[[str], None],
        on_new_patient: Callable[[dict], None],
        on_patient_updated: Callable[[], None],
        db: DatabaseService,
        rag: RAGService
    ):
        self.on_patient_selected = on_patient_selected
        self.on_search = on_search
        self.on_new_patient = on_new_patient
        self.on_patient_updated = on_patient_updated
        self.db = db
        self.rag = rag

        self.patients: List[Patient] = []
        self.selected_patient_id: Optional[int] = None
        self.selected_patient: Optional[Patient] = None
        self.search_active: bool = False

        # UI components
        self.search_field: Optional[ft.TextField] = None
        self.patient_list: Optional[ft.ListView] = None
        self.patient_actions: Optional[ft.Row] = None
        self.page: Optional[ft.Page] = None
        self.appointments_panel: Optional[TodayAppointmentsPanel] = None

    def build(self) -> ft.Control:
        """Build the patient panel UI with premium styling."""
        colors = get_panel_colors(is_dark=False)

        # Today's appointments panel
        self.appointments_panel = TodayAppointmentsPanel(
            db=self.db,
            on_patient_click=self._on_appointment_patient_click
        )

        # Premium search field
        self.search_field = ft.TextField(
            hint_text="Search patients...",
            prefix_icon=ft.Icons.SEARCH,
            tooltip="Search patients (Ctrl+F)",
            border_radius=Radius.FULL,
            height=40,
            text_size=Typography.BODY_MEDIUM.size,
            border_color=Colors.NEUTRAL_200,
            focused_border_color=Colors.PRIMARY_500,
            bgcolor=Colors.NEUTRAL_0,
            on_change=self._on_search_change,
            on_submit=self._on_search_submit,
            content_padding=ft.padding.symmetric(
                horizontal=Spacing.MD,
                vertical=Spacing.XS,
            ),
        )

        # Patient actions row with premium styling
        self.patient_actions = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    tooltip="Edit patient",
                    icon_color=Colors.PRIMARY_500,
                    icon_size=20,
                    on_click=self._edit_selected_patient,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                        overlay_color=Colors.HOVER_OVERLAY,
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Delete patient",
                    icon_color=Colors.ERROR_MAIN,
                    icon_size=20,
                    on_click=self._delete_selected_patient,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                        overlay_color="rgba(234, 67, 53, 0.1)",
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False,
        )

        # Patient list with proper spacing
        self.patient_list = ft.ListView(
            spacing=Spacing.XXS,
            padding=Spacing.SM,
            expand=True,
        )

        # Premium new patient button
        new_patient_btn = ft.ElevatedButton(
            text="New Patient",
            icon=ft.Icons.PERSON_ADD_OUTLINED,
            tooltip="Add new patient (Ctrl+N)",
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                padding=ft.padding.symmetric(
                    horizontal=Spacing.LG,
                    vertical=Spacing.SM,
                ),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                elevation=2,
            ),
            on_click=self._show_new_patient_dialog,
            width=220,
        )

        return ft.Column(
            [
                # Today's appointments
                ft.Container(
                    content=self.appointments_panel.build(),
                    padding=ft.padding.only(
                        left=Spacing.SM,
                        right=Spacing.SM,
                        top=Spacing.SM,
                    ),
                ),
                ft.Divider(height=1, color=Colors.NEUTRAL_200),

                # Search section
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Patients",
                            size=Typography.TITLE_MEDIUM.size,
                            weight=ft.FontWeight.W_600,
                            color=Colors.NEUTRAL_900,
                        ),
                        self.search_field,
                        self.patient_actions,
                    ], spacing=Spacing.SM),
                    padding=Spacing.MD,
                ),
                ft.Divider(height=1, color=Colors.NEUTRAL_200),

                # Patient list
                self.patient_list,

                # New patient button
                ft.Container(
                    content=new_patient_btn,
                    padding=Spacing.MD,
                    alignment=ft.alignment.center,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def set_patients(self, patients: List[Patient]):
        """Update the patient list (for search results)."""
        self.patients = patients
        self.search_active = True
        self._refresh_list()

    def load_all_patients(self):
        """Load and display all patients with sections."""
        self.patients = []
        self.search_active = False
        self._refresh_list()
        self._refresh_appointments()

    def _refresh_appointments(self):
        """Refresh today's appointments panel."""
        if self.appointments_panel:
            self.appointments_panel.refresh()

    def _on_appointment_patient_click(self, patient_id: int):
        """Handle click on appointment to select patient."""
        patient_data = self.db.get_patient(patient_id)
        if patient_data:
            patient = Patient(**patient_data)
            self.selected_patient_id = patient.id
            self.selected_patient = patient
            self.on_patient_selected(patient)

    def _refresh_list(self):
        """Refresh the patient list UI with sections."""
        if not self.patient_list:
            return

        self.patient_list.controls.clear()

        # If search is active, show search results without sections
        if self.search_active and self.search_field and self.search_field.value.strip():
            for patient in self.patients:
                self.patient_list.controls.append(self._create_patient_tile(patient))
            if self.patient_list.page:
                self.patient_list.update()
            return

        # Get organized sections
        favorites_data = self.db.get_favorite_patients()
        favorites = [Patient(**data) for data in favorites_data]

        todays_data = self.db.get_todays_patients()
        todays = [Patient(**data) for data in todays_data]

        recent_data = self.db.get_recent_patients(limit=10)
        recent = [Patient(**data) for data in recent_data]

        all_patients = self.patients if self.patients else [
            Patient(**data) for data in self.db.get_all_patients()
        ]

        sections_added = False

        # FAVORITES section
        if favorites:
            sections_added = True
            self.patient_list.controls.append(self._section_header(
                "FAVORITES", ft.Icons.STAR, Colors.ACCENT_500
            ))
            for patient in favorites:
                self.patient_list.controls.append(self._create_patient_tile(patient))

        # TODAY section
        if todays:
            if sections_added:
                self.patient_list.controls.append(
                    ft.Divider(height=1, color=Colors.NEUTRAL_200)
                )
            sections_added = True
            self.patient_list.controls.append(self._section_header(
                f"TODAY ({len(todays)})", ft.Icons.TODAY, Colors.SUCCESS_MAIN
            ))
            for patient in todays:
                self.patient_list.controls.append(self._create_patient_tile(patient))

        # RECENT section
        if recent:
            if sections_added:
                self.patient_list.controls.append(
                    ft.Divider(height=1, color=Colors.NEUTRAL_200)
                )
            sections_added = True
            self.patient_list.controls.append(self._section_header(
                "RECENT", ft.Icons.HISTORY, Colors.PRIMARY_500
            ))
            for patient in recent:
                self.patient_list.controls.append(self._create_patient_tile(patient))

            # Clear recent button
            self.patient_list.controls.append(
                ft.Container(
                    content=ft.TextButton(
                        "Clear recent",
                        icon=ft.Icons.CLEAR_ALL,
                        on_click=self._clear_recent,
                        style=ft.ButtonStyle(
                            color=Colors.NEUTRAL_500,
                            padding=ft.padding.symmetric(
                                horizontal=Spacing.SM,
                                vertical=Spacing.XXS,
                            ),
                        ),
                    ),
                    padding=ft.padding.only(left=Spacing.XS, bottom=Spacing.XS),
                )
            )

        # ALL PATIENTS section
        if sections_added:
            self.patient_list.controls.append(
                ft.Divider(height=1, color=Colors.NEUTRAL_200)
            )

        self.patient_list.controls.append(self._section_header(
            "ALL PATIENTS", ft.Icons.PEOPLE_OUTLINE, Colors.NEUTRAL_600
        ))
        for patient in all_patients:
            self.patient_list.controls.append(self._create_patient_tile(patient))

        if self.patient_list.page:
            self.patient_list.update()

    def _section_header(self, title: str, icon, color: str) -> ft.Container:
        """Create a premium section header."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=14, color=color),
                ft.Text(
                    title,
                    size=Typography.LABEL_SMALL.size,
                    weight=ft.FontWeight.W_600,
                    color=Colors.NEUTRAL_600,
                    letter_spacing=0.5,
                ),
            ], spacing=Spacing.XS),
            padding=ft.padding.only(
                left=Spacing.SM,
                right=Spacing.SM,
                top=Spacing.SM,
                bottom=Spacing.XXS,
            ),
        )

    def _create_patient_tile(self, patient: Patient) -> ft.Control:
        """Create a premium patient tile with avatar and vitals."""
        is_selected = patient.id == self.selected_patient_id
        is_favorite = getattr(patient, 'is_favorite', 0)

        # Demographics subtitle
        subtitle_parts = []
        if patient.age:
            subtitle_parts.append(f"{patient.age}y")
        if patient.gender:
            subtitle_parts.append(patient.gender)
        if patient.uhid:
            subtitle_parts.append(patient.uhid)
        subtitle = " · ".join(subtitle_parts)

        # Avatar with initials
        initials = "".join([part[0].upper() for part in patient.name.split()[:2]])
        avatar_bg = Colors.PRIMARY_500 if is_selected else Colors.PRIMARY_100
        avatar_color = Colors.NEUTRAL_0 if is_selected else Colors.PRIMARY_700

        avatar = ft.Container(
            content=ft.Text(
                initials,
                size=Typography.LABEL_MEDIUM.size,
                weight=ft.FontWeight.W_600,
                color=avatar_color,
            ),
            width=36,
            height=36,
            border_radius=Radius.FULL,
            bgcolor=avatar_bg,
            alignment=ft.alignment.center,
        )

        # Star icon for favorite
        star_icon = ft.IconButton(
            icon=ft.Icons.STAR if is_favorite else ft.Icons.STAR_BORDER,
            icon_color=Colors.ACCENT_500 if is_favorite else (
                Colors.NEUTRAL_0 if is_selected else Colors.NEUTRAL_300
            ),
            icon_size=18,
            tooltip="Toggle favorite",
            on_click=lambda e, p=patient: self._toggle_favorite(e, p),
            style=ft.ButtonStyle(
                padding=ft.padding.all(4),
                shape=ft.RoundedRectangleBorder(radius=Radius.FULL),
            ),
        )

        # Patient info
        text_color = Colors.NEUTRAL_0 if is_selected else Colors.NEUTRAL_900
        subtitle_color = Colors.NEUTRAL_200 if is_selected else Colors.NEUTRAL_500

        info_column = ft.Column([
            ft.Text(
                patient.name,
                size=Typography.BODY_MEDIUM.size,
                weight=ft.FontWeight.W_500,
                color=text_color,
                overflow=ft.TextOverflow.ELLIPSIS,
                max_lines=1,
            ),
            ft.Text(
                subtitle,
                size=Typography.BODY_SMALL.size,
                color=subtitle_color,
            ),
        ], spacing=2, expand=True)

        # Add vitals if selected
        if is_selected:
            latest_vitals = self.db.get_latest_vitals(patient.id)
            if latest_vitals:
                vitals_parts = []
                if latest_vitals.get('bp_systolic') and latest_vitals.get('bp_diastolic'):
                    vitals_parts.append(
                        f"BP: {latest_vitals['bp_systolic']}/{latest_vitals['bp_diastolic']}"
                    )
                if latest_vitals.get('pulse'):
                    vitals_parts.append(f"PR: {latest_vitals['pulse']}")
                if latest_vitals.get('spo2'):
                    vitals_parts.append(f"SpO2: {latest_vitals['spo2']}%")

                if vitals_parts:
                    info_column.controls.append(
                        ft.Container(
                            content=ft.Text(
                                " · ".join(vitals_parts),
                                size=Typography.CAPTION.size,
                                color=Colors.NEUTRAL_200,
                            ),
                            margin=ft.margin.only(top=2),
                        )
                    )

                # Weight and BMI
                vitals_parts2 = []
                if latest_vitals.get('weight'):
                    vitals_parts2.append(f"Wt: {latest_vitals['weight']}kg")
                if latest_vitals.get('bmi'):
                    vitals_parts2.append(f"BMI: {latest_vitals['bmi']}")

                if vitals_parts2:
                    info_column.controls.append(
                        ft.Text(
                            " · ".join(vitals_parts2),
                            size=Typography.CAPTION.size,
                            color=Colors.NEUTRAL_200,
                        )
                    )

        # Card styling
        bgcolor = Colors.PRIMARY_500 if is_selected else Colors.NEUTRAL_0
        border = (
            ft.border.all(2, Colors.PRIMARY_600) if is_selected
            else ft.border.all(1, Colors.NEUTRAL_100)
        )

        tile = ft.Container(
            content=ft.Row([
                avatar,
                info_column,
                star_icon,
            ], spacing=Spacing.SM),
            padding=ft.padding.symmetric(
                horizontal=Spacing.SM,
                vertical=Spacing.XS,
            ),
            bgcolor=bgcolor,
            border=border,
            border_radius=Radius.MD,
            on_click=lambda e, p=patient: self._select_patient(p),
            on_hover=lambda e, p=patient: self._on_tile_hover(e, p),
            animate=ft.animation.Animation(100, ft.AnimationCurve.EASE_OUT),
        )

        return tile

    def _on_tile_hover(self, e, patient: Patient):
        """Handle tile hover effect."""
        if patient.id != self.selected_patient_id:
            if e.data == "true":
                e.control.bgcolor = Colors.NEUTRAL_50
                e.control.border = ft.border.all(1, Colors.NEUTRAL_200)
            else:
                e.control.bgcolor = Colors.NEUTRAL_0
                e.control.border = ft.border.all(1, Colors.NEUTRAL_100)
            e.control.update()

    def _select_patient(self, patient: Patient):
        """Handle patient selection."""
        self.selected_patient_id = patient.id
        self.selected_patient = patient
        self.patient_actions.visible = True
        self._refresh_list()
        if self.patient_actions.page:
            self.patient_actions.page.update()
        self.on_patient_selected(patient)

    def _on_search_change(self, e):
        """Handle search field change."""
        if not self.search_field.value.strip():
            self.search_active = False
            self.patients = []
            self._refresh_list()

    def _on_search_submit(self, e):
        """Handle search submit."""
        query = self.search_field.value.strip()
        self.on_search(query)

    def _toggle_favorite(self, e, patient: Patient):
        """Toggle patient favorite status."""
        e.control.data = "stop"
        new_status = self.db.toggle_patient_favorite(patient.id)
        patient.is_favorite = 1 if new_status else 0
        self._refresh_list()

    def _clear_recent(self, e):
        """Clear recent patients list."""
        self.db.clear_recent_patients()
        self._refresh_list()

    def _show_new_patient_dialog(self, e):
        """Show dialog to add new patient."""
        self._show_patient_dialog(e.page, None)

    def _edit_selected_patient(self, e):
        """Edit the currently selected patient."""
        if self.selected_patient:
            self._show_patient_dialog(e.page, self.selected_patient)

    def _show_patient_dialog(self, page, patient: Optional[Patient] = None):
        """Show premium dialog to add or edit a patient."""
        is_new = patient is None

        # Premium form fields
        name_field = ft.TextField(
            label="Name *",
            value=patient.name if patient else "",
            autofocus=True,
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
        )
        age_field = ft.TextField(
            label="Age",
            value=str(patient.age) if patient and patient.age else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
        )
        gender_dropdown = ft.Dropdown(
            label="Gender",
            value=patient.gender if patient else None,
            options=[
                ft.dropdown.Option("M", "Male"),
                ft.dropdown.Option("F", "Female"),
                ft.dropdown.Option("O", "Other"),
            ],
            width=120,
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
        )
        phone_field = ft.TextField(
            label="Phone",
            value=patient.phone if patient and patient.phone else "",
            keyboard_type=ft.KeyboardType.PHONE,
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
        )
        address_field = ft.TextField(
            label="Address",
            value=patient.address if patient and patient.address else "",
            multiline=True,
            min_lines=2,
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
        )

        error_text = ft.Text("", color=Colors.ERROR_MAIN, size=Typography.BODY_SMALL.size)

        def save_patient(e):
            if not name_field.value.strip():
                error_text.value = "Name is required"
                page.update()
                return

            if is_new:
                patient_data = {
                    "name": name_field.value.strip(),
                    "age": int(age_field.value) if age_field.value else None,
                    "gender": gender_dropdown.value,
                    "phone": phone_field.value.strip() if phone_field.value else None,
                    "address": address_field.value.strip() if address_field.value else None,
                }
                dialog.open = False
                page.update()
                self.on_new_patient(patient_data)
            else:
                updated_patient = Patient(
                    id=patient.id,
                    uhid=patient.uhid,
                    name=name_field.value.strip(),
                    age=int(age_field.value) if age_field.value else None,
                    gender=gender_dropdown.value,
                    phone=phone_field.value.strip() if phone_field.value else None,
                    address=address_field.value.strip() if address_field.value else None,
                    created_at=patient.created_at
                )

                if self.db.update_patient(updated_patient):
                    dialog.open = False
                    page.update()
                    self._show_snackbar(page, "Patient updated successfully")
                    self.on_patient_updated()
                else:
                    error_text.value = "Failed to update patient"
                    page.update()

        def close_dialog(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(
                "Add New Patient" if is_new else "Edit Patient",
                size=Typography.HEADLINE_SMALL.size,
                weight=ft.FontWeight.W_500,
            ),
            content=ft.Container(
                content=ft.Column([
                    name_field,
                    ft.Row([age_field, gender_dropdown], spacing=Spacing.SM),
                    phone_field,
                    address_field,
                    error_text,
                ], spacing=Spacing.MD, tight=True),
                width=400,
                padding=Spacing.XS,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=close_dialog,
                    style=get_button_style("ghost"),
                ),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_patient,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.PRIMARY_500,
                        color=Colors.NEUTRAL_0,
                        shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=Radius.DIALOG),
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def _delete_selected_patient(self, e):
        """Delete the currently selected patient with confirmation."""
        if not self.selected_patient:
            return

        patient = self.selected_patient

        def confirm_delete():
            if self.db.delete_patient(patient.id):
                self._show_snackbar(e.page, "Patient deleted successfully")
                self.selected_patient_id = None
                self.selected_patient = None
                self.patient_actions.visible = False
                self.on_patient_updated()
            else:
                self._show_snackbar(e.page, "Failed to delete patient", error=True)

        message = (
            f"This will delete patient {patient.name} (UHID: {patient.uhid}).\n\n"
            f"All associated visits, investigations, and procedures will also be marked as deleted.\n\n"
            f"This is a soft delete and records can be recovered from backups."
        )

        ConfirmationDialog.show(
            e.page,
            "Delete Patient?",
            message,
            confirm_delete,
            confirm_text="Delete Patient"
        )

    def _show_snackbar(self, page, message: str, error: bool = False):
        """Show a premium snackbar message."""
        if page:
            page.open(
                ft.SnackBar(
                    content=ft.Text(message, color=Colors.NEUTRAL_0),
                    bgcolor=Colors.ERROR_MAIN if error else Colors.SUCCESS_MAIN,
                    behavior=ft.SnackBarBehavior.FLOATING,
                    shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                )
            )
