"""Left panel - Patient list and search."""

import flet as ft
from typing import List, Callable, Optional

from ..models.schemas import Patient
from ..services.database import DatabaseService
from ..services.rag import RAGService


class PatientPanel:
    """Patient list panel with search functionality."""

    def __init__(
        self,
        on_patient_selected: Callable[[Patient], None],
        on_search: Callable[[str], None],
        on_new_patient: Callable[[dict], None],
        db: DatabaseService,
        rag: RAGService
    ):
        self.on_patient_selected = on_patient_selected
        self.on_search = on_search
        self.on_new_patient = on_new_patient
        self.db = db
        self.rag = rag

        self.patients: List[Patient] = []
        self.selected_patient_id: Optional[int] = None

        # UI components
        self.search_field: Optional[ft.TextField] = None
        self.patient_list: Optional[ft.ListView] = None
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
        """Update the patient list."""
        self.patients = patients
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the patient list UI."""
        if not self.patient_list:
            return

        self.patient_list.controls.clear()

        for patient in self.patients:
            is_selected = patient.id == self.selected_patient_id

            # Patient info
            subtitle_parts = []
            if patient.age:
                subtitle_parts.append(f"{patient.age}y")
            if patient.gender:
                subtitle_parts.append(patient.gender)
            if patient.uhid:
                subtitle_parts.append(patient.uhid)
            subtitle = " | ".join(subtitle_parts)

            tile = ft.Container(
                content=ft.Column([
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
                ], spacing=2),
                padding=ft.padding.symmetric(horizontal=15, vertical=10),
                bgcolor=ft.Colors.BLUE_700 if is_selected else ft.Colors.TRANSPARENT,
                border_radius=8,
                on_click=lambda e, p=patient: self._select_patient(p),
                ink=True,
            )

            self.patient_list.controls.append(tile)

        if self.patient_list.page:
            self.patient_list.update()

    def _select_patient(self, patient: Patient):
        """Handle patient selection."""
        self.selected_patient_id = patient.id
        self._refresh_list()
        self.on_patient_selected(patient)

    def _on_search_change(self, e):
        """Handle search field change."""
        # Debounce could be added here for better UX
        pass

    def _on_search_submit(self, e):
        """Handle search submit."""
        query = self.search_field.value.strip()
        self.on_search(query)

    def _show_new_patient_dialog(self, e):
        """Show dialog to add new patient."""
        page = e.page

        name_field = ft.TextField(label="Name *", autofocus=True)
        age_field = ft.TextField(label="Age", keyboard_type=ft.KeyboardType.NUMBER, width=100)
        gender_dropdown = ft.Dropdown(
            label="Gender",
            options=[
                ft.dropdown.Option("M", "Male"),
                ft.dropdown.Option("F", "Female"),
                ft.dropdown.Option("O", "Other"),
            ],
            width=120,
        )
        phone_field = ft.TextField(label="Phone", keyboard_type=ft.KeyboardType.PHONE)
        address_field = ft.TextField(label="Address", multiline=True, min_lines=2)

        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

        def save_patient(e):
            if not name_field.value.strip():
                error_text.value = "Name is required"
                page.update()
                return

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

        def close_dialog(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Add New Patient"),
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
