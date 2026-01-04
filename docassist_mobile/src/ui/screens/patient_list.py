"""
Patient List Screen - Searchable patient directory.

Premium patient list with search and quick access.
"""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..components.patient_card import PatientCard
from ..components.search_bar import SearchBar


@dataclass
class PatientData:
    """Patient display data."""
    id: int
    name: str
    age: Optional[int] = None
    gender: str = "O"
    phone: Optional[str] = None
    last_visit: Optional[str] = None


class PatientListScreen(ft.Container):
    """
    Patient list screen with search functionality.

    Usage:
        patients = PatientListScreen(
            on_patient_click=handle_patient_select,
            on_search=handle_search,
        )
    """

    def __init__(
        self,
        on_patient_click: Optional[Callable[[int], None]] = None,
        on_search: Optional[Callable[[str], None]] = None,
    ):
        self.on_patient_click = on_patient_click
        self.on_search = on_search
        self._patients: List[PatientData] = []

        # Search bar
        self.search_bar = SearchBar(
            hint_text="Search patients...",
            on_search=self._handle_search,
            on_clear=self._handle_clear_search,
        )

        # Patient list
        self.patient_list = ft.ListView(
            spacing=MobileSpacing.XS,
            padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
            expand=True,
        )

        # Loading indicator
        self.loading = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=32, height=32, stroke_width=3),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        "Loading patients...",
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
            visible=False,
        )

        # Empty state
        self.empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.PERSON_SEARCH,
                        size=64,
                        color=Colors.NEUTRAL_300,
                    ),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        "No patients found",
                        size=MobileTypography.TITLE_MEDIUM,
                        color=Colors.NEUTRAL_600,
                    ),
                    ft.Text(
                        "Try a different search term",
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
            visible=False,
        )

        # No data state (before first sync)
        self.no_data_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.CLOUD_DOWNLOAD,
                        size=64,
                        color=Colors.NEUTRAL_300,
                    ),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        "No data yet",
                        size=MobileTypography.TITLE_MEDIUM,
                        color=Colors.NEUTRAL_600,
                    ),
                    ft.Text(
                        "Sync with your desktop to see patients",
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=MobileSpacing.LG),
                    ft.ElevatedButton(
                        text="Sync Now",
                        icon=ft.Icons.SYNC,
                        style=ft.ButtonStyle(
                            bgcolor=Colors.PRIMARY_500,
                            color=Colors.NEUTRAL_0,
                            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
            visible=False,
        )

        # Results count
        self.results_count = ft.Container(
            content=ft.Text(
                "0 patients",
                size=MobileTypography.BODY_SMALL,
                color=Colors.NEUTRAL_600,
            ),
            padding=ft.padding.only(
                left=MobileSpacing.SCREEN_PADDING,
                bottom=MobileSpacing.XS,
            ),
            visible=False,
        )

        # Build content
        content = ft.Column(
            [
                self.search_bar,
                self.results_count,
                ft.Stack(
                    [
                        self.patient_list,
                        self.loading,
                        self.empty_state,
                        self.no_data_state,
                    ],
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )

    def set_patients(self, patients: List[PatientData]):
        """Update patient list."""
        self._patients = patients
        self._render_patients(patients)

    def _render_patients(self, patients: List[PatientData]):
        """Render patient list."""
        self.patient_list.controls.clear()
        self._hide_all_states()

        if not patients:
            self.empty_state.visible = True
            self.results_count.visible = False
        else:
            self.patient_list.visible = True
            self.results_count.visible = True
            self.results_count.content.value = f"{len(patients)} patient{'s' if len(patients) != 1 else ''}"

            for patient in patients:
                card = PatientCard(
                    name=patient.name,
                    age=patient.age,
                    gender=patient.gender,
                    phone=patient.phone,
                    last_visit=patient.last_visit,
                    on_click=lambda e, pid=patient.id: self._on_patient_click(pid),
                )
                self.patient_list.controls.append(card)

        self.update()

    def _on_patient_click(self, patient_id: int):
        """Handle patient card click."""
        if self.on_patient_click:
            self.on_patient_click(patient_id)

    def _handle_search(self, query: str):
        """Handle search input."""
        if self.on_search:
            self.on_search(query)

        # Filter local patients for immediate feedback
        if query:
            filtered = [
                p for p in self._patients
                if query.lower() in p.name.lower()
                or (p.phone and query in p.phone)
            ]
            self._render_patients(filtered)
        else:
            self._render_patients(self._patients)

    def _handle_clear_search(self):
        """Handle search clear."""
        self._render_patients(self._patients)

    def _hide_all_states(self):
        """Hide all state containers."""
        self.loading.visible = False
        self.empty_state.visible = False
        self.no_data_state.visible = False
        self.patient_list.visible = False

    def show_loading(self):
        """Show loading state."""
        self._hide_all_states()
        self.loading.visible = True
        self.results_count.visible = False
        self.update()

    def show_no_data(self):
        """Show no data state."""
        self._hide_all_states()
        self.no_data_state.visible = True
        self.results_count.visible = False
        self.update()

    def scroll_to_top(self):
        """Scroll list to top."""
        if self.patient_list.controls:
            self.patient_list.scroll_to(offset=0, duration=300)
