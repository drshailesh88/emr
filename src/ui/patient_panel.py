"""Left panel - Patient list and search."""

import flet as ft
from typing import List, Callable, Optional

from ..models.schemas import Patient
from ..services.database import DatabaseService
from ..services.rag import RAGService
from .dialogs import ConfirmationDialog


class PatientPanel:
    """Patient list panel with search functionality."""

    def __init__(
        self,
        on_patient_selected: Callable[[Patient], None],
        on_search: Callable[[str], None],
        on_new_patient: Callable[[dict], None],
        on_patient_updated: Callable[[], None],  # New callback to refresh patient list
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
        self.search_active: bool = False  # Track if user is searching

        # UI components
        self.search_field: Optional[ft.TextField] = None
        self.patient_list: Optional[ft.ListView] = None
        self.patient_actions: Optional[ft.Row] = None
        self.page: Optional[ft.Page] = None

    def build(self) -> ft.Control:
        """Build the patient panel UI."""

        # Search field
        self.search_field = ft.TextField(
            hint_text="Search patients...",
            prefix_icon=ft.Icons.SEARCH,
            tooltip="Search patients (Ctrl+F)",
            border_radius=20,
            height=45,
            text_size=14,
            on_change=self._on_search_change,
            on_submit=self._on_search_submit,
        )

        # Patient actions row (shown when patient selected)
        self.patient_actions = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Edit patient",
                    icon_color=ft.Colors.BLUE_700,
                    on_click=self._edit_selected_patient,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Delete patient",
                    icon_color=ft.Colors.RED_700,
                    on_click=self._delete_selected_patient,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False,
        )

        # Patient list
        self.patient_list = ft.ListView(
            spacing=2,
            padding=10,
            expand=True,
        )

        # New patient button
        new_patient_btn = ft.ElevatedButton(
            text="New Patient",
            icon=ft.Icons.PERSON_ADD,
            tooltip="Add new patient (Ctrl+N)",
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
            on_click=self._show_new_patient_dialog,
            width=240,
        )

        return ft.Column(
            [
                ft.Container(
                    content=ft.Column([
                        ft.Text("Patients", size=16, weight=ft.FontWeight.BOLD),
                        self.search_field,
                        self.patient_actions,
                    ], spacing=10),
                    padding=15,
                ),
                ft.Divider(height=1),
                self.patient_list,
                ft.Container(
                    content=new_patient_btn,
                    padding=15,
                    alignment=ft.alignment.center,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def set_patients(self, patients: List[Patient]):
        """Update the patient list (for search results)."""
        self.patients = patients
        self.search_active = True  # Mark that search results are being shown
        self._refresh_list()

    def load_all_patients(self):
        """Load and display all patients with sections."""
        self.patients = []
        self.search_active = False
        self._refresh_list()

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

        # Otherwise, show organized sections
        # Get favorites
        favorites_data = self.db.get_favorite_patients()
        favorites = [Patient(**data) for data in favorites_data]

        # Get today's patients
        todays_data = self.db.get_todays_patients()
        todays = [Patient(**data) for data in todays_data]

        # Get recent patients
        recent_data = self.db.get_recent_patients(limit=10)
        recent = [Patient(**data) for data in recent_data]

        # All patients (use self.patients if available, otherwise fetch)
        all_patients = self.patients if self.patients else [Patient(**data) for data in self.db.get_all_patients()]

        # Build sections
        sections_added = False

        # FAVORITES section
        if favorites:
            sections_added = True
            self.patient_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.STAR, size=16, color=ft.Colors.AMBER_700),
                        ft.Text("FAVORITES", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ], spacing=5),
                    padding=ft.padding.only(left=10, right=10, top=10, bottom=5),
                )
            )
            for patient in favorites:
                self.patient_list.controls.append(self._create_patient_tile(patient))

        # TODAY section
        if todays:
            if sections_added:
                self.patient_list.controls.append(ft.Divider(height=1))
            sections_added = True
            self.patient_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TODAY, size=16, color=ft.Colors.GREEN_700),
                        ft.Text(f"TODAY ({len(todays)})", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ], spacing=5),
                    padding=ft.padding.only(left=10, right=10, top=10, bottom=5),
                )
            )
            for patient in todays:
                self.patient_list.controls.append(self._create_patient_tile(patient))

        # RECENT section
        if recent:
            if sections_added:
                self.patient_list.controls.append(ft.Divider(height=1))
            sections_added = True
            self.patient_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.HISTORY, size=16, color=ft.Colors.BLUE_700),
                        ft.Text("RECENT", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ], spacing=5),
                    padding=ft.padding.only(left=10, right=10, top=10, bottom=5),
                )
            )
            for patient in recent:
                self.patient_list.controls.append(self._create_patient_tile(patient))

            # Add "Clear recent" button
            self.patient_list.controls.append(
                ft.Container(
                    content=ft.TextButton(
                        "Clear recent",
                        icon=ft.Icons.CLEAR_ALL,
                        on_click=self._clear_recent,
                        style=ft.ButtonStyle(color=ft.Colors.GREY_600),
                    ),
                    padding=ft.padding.only(left=5, right=5, bottom=5),
                )
            )

        # ALL PATIENTS section
        if sections_added:
            self.patient_list.controls.append(ft.Divider(height=1))

        self.patient_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.PEOPLE, size=16, color=ft.Colors.GREY_600),
                    ft.Text("ALL PATIENTS", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ], spacing=5),
                padding=ft.padding.only(left=10, right=10, top=10, bottom=5),
            )
        )
        for patient in all_patients:
            self.patient_list.controls.append(self._create_patient_tile(patient))

        if self.patient_list.page:
            self.patient_list.update()

    def _create_patient_tile(self, patient: Patient) -> ft.Control:
        """Create a patient tile with star icon and vitals for selected patient."""
        is_selected = patient.id == self.selected_patient_id
        is_favorite = getattr(patient, 'is_favorite', 0)

        # Patient info
        subtitle_parts = []
        if patient.age:
            subtitle_parts.append(f"{patient.age}y")
        if patient.gender:
            subtitle_parts.append(patient.gender)
        if patient.uhid:
            subtitle_parts.append(patient.uhid)
        subtitle = " | ".join(subtitle_parts)

        # Star icon for favorite
        star_icon = ft.IconButton(
            icon=ft.Icons.STAR if is_favorite else ft.Icons.STAR_BORDER,
            icon_color=ft.Colors.AMBER_700 if is_favorite else (ft.Colors.WHITE70 if is_selected else ft.Colors.GREY_400),
            icon_size=18,
            tooltip="Toggle favorite",
            on_click=lambda e, p=patient: self._toggle_favorite(e, p),
        )

        # Create base patient info column
        patient_info = ft.Column([
            ft.Text(
                patient.name,
                size=14,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.WHITE if is_selected else ft.Colors.BLACK,
            ),
            ft.Text(
                subtitle,
                size=11,
                color=ft.Colors.WHITE70 if is_selected else ft.Colors.GREY_600,
            ),
        ], spacing=2, expand=True)

        # Add vitals if selected
        if is_selected:
            latest_vitals = self.db.get_latest_vitals(patient.id)
            if latest_vitals:
                vitals_parts = []

                # BP
                if latest_vitals.get('bp_systolic') and latest_vitals.get('bp_diastolic'):
                    bp_text = f"BP: {latest_vitals['bp_systolic']}/{latest_vitals['bp_diastolic']}"
                    vitals_parts.append(bp_text)

                # Pulse
                if latest_vitals.get('pulse'):
                    vitals_parts.append(f"PR: {latest_vitals['pulse']}")

                # SpO2
                if latest_vitals.get('spo2'):
                    vitals_parts.append(f"SpO2: {latest_vitals['spo2']}%")

                if vitals_parts:
                    patient_info.controls.append(
                        ft.Container(
                            content=ft.Text(
                                " | ".join(vitals_parts),
                                size=10,
                                color=ft.Colors.WHITE70,
                                weight=ft.FontWeight.W_400,
                            ),
                            margin=ft.margin.only(top=3),
                        )
                    )

                # Weight and BMI on second line
                vitals_parts2 = []
                if latest_vitals.get('weight'):
                    vitals_parts2.append(f"Wt: {latest_vitals['weight']} kg")

                if latest_vitals.get('bmi'):
                    vitals_parts2.append(f"BMI: {latest_vitals['bmi']}")

                if vitals_parts2:
                    patient_info.controls.append(
                        ft.Text(
                            " | ".join(vitals_parts2),
                            size=10,
                            color=ft.Colors.WHITE70,
                            weight=ft.FontWeight.W_400,
                        )
                    )

        tile = ft.Container(
            content=ft.Row([
                patient_info,
                star_icon,
            ], spacing=5),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=ft.Colors.BLUE_700 if is_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            on_click=lambda e, p=patient: self._select_patient(p),
            ink=True,
        )

        return tile

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
        # If search is cleared, reset to section view
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
        e.stop_propagation()  # Prevent patient selection
        new_status = self.db.toggle_patient_favorite(patient.id)
        # Update the patient object
        patient.is_favorite = 1 if new_status else 0
        # Refresh the list to show updated star
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
        """Show dialog to add or edit a patient."""
        is_new = patient is None

        name_field = ft.TextField(
            label="Name *",
            value=patient.name if patient else "",
            autofocus=True
        )
        age_field = ft.TextField(
            label="Age",
            value=str(patient.age) if patient and patient.age else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100
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
        )
        phone_field = ft.TextField(
            label="Phone",
            value=patient.phone if patient and patient.phone else "",
            keyboard_type=ft.KeyboardType.PHONE
        )
        address_field = ft.TextField(
            label="Address",
            value=patient.address if patient and patient.address else "",
            multiline=True,
            min_lines=2
        )

        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

        def save_patient(e):
            if not name_field.value.strip():
                error_text.value = "Name is required"
                page.update()
                return

            if is_new:
                # Create new patient
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
                # Update existing patient
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
            title=ft.Text("Add New Patient" if is_new else "Edit Patient"),
            content=ft.Container(
                content=ft.Column([
                    name_field,
                    ft.Row([age_field, gender_dropdown], spacing=10),
                    phone_field,
                    address_field,
                    error_text,
                ], spacing=15, tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Save", on_click=save_patient),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
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
        """Show a snackbar message."""
        if page:
            page.open(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
                )
            )
