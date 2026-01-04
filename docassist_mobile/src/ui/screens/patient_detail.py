"""
Patient Detail Screen - Full patient information.

Premium patient detail view with tabs for visits, labs, procedures.
"""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..components.visit_card import VisitCard
from ..components.lab_card import LabCard


@dataclass
class PatientInfo:
    """Patient information."""
    id: int
    name: str
    uhid: str
    age: Optional[int] = None
    gender: str = "O"
    phone: Optional[str] = None
    address: Optional[str] = None


@dataclass
class VisitData:
    """Visit display data."""
    id: int
    date: str
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None


@dataclass
class LabData:
    """Lab result display data."""
    id: int
    test_name: str
    result: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    date: Optional[str] = None
    is_abnormal: bool = False


@dataclass
class ProcedureData:
    """Procedure display data."""
    id: int
    name: str
    date: str
    details: Optional[str] = None


class PatientDetailScreen(ft.Container):
    """
    Patient detail screen with tabbed view.

    Usage:
        detail = PatientDetailScreen(
            patient=patient_info,
            on_back=handle_back,
            on_call=handle_call,
        )
    """

    def __init__(
        self,
        patient: Optional[PatientInfo] = None,
        on_back: Optional[Callable] = None,
        on_call: Optional[Callable[[str], None]] = None,
        on_share: Optional[Callable[[int], None]] = None,
        on_add_appointment: Optional[Callable[[int], None]] = None,
    ):
        self.patient = patient
        self.on_back = on_back
        self.on_call = on_call
        self.on_share = on_share
        self.on_add_appointment = on_add_appointment

        # Tab content lists
        self.visits_list = ft.ListView(
            spacing=MobileSpacing.SM,
            padding=MobileSpacing.SCREEN_PADDING,
            expand=True,
        )
        self.labs_list = ft.ListView(
            spacing=MobileSpacing.SM,
            padding=MobileSpacing.SCREEN_PADDING,
            expand=True,
        )
        self.procedures_list = ft.ListView(
            spacing=MobileSpacing.SM,
            padding=MobileSpacing.SCREEN_PADDING,
            expand=True,
        )

        # Empty states for each tab
        self.visits_empty = self._create_empty_state("No visits recorded", ft.Icons.EVENT_NOTE)
        self.labs_empty = self._create_empty_state("No lab results", ft.Icons.SCIENCE)
        self.procedures_empty = self._create_empty_state("No procedures", ft.Icons.MEDICAL_SERVICES)

        # Build content
        content = self._build_content()

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )

    def _build_content(self) -> ft.Column:
        """Build screen content."""
        if not self.patient:
            return ft.Column([ft.Text("No patient selected")])

        # Generate initials
        initials = "".join([n[0] for n in self.patient.name.split()[:2]]).upper()

        # Demographics text
        demo_parts = []
        if self.patient.gender:
            demo_parts.append(self.patient.gender)
        if self.patient.age:
            demo_parts.append(f"{self.patient.age} years")
        if self.patient.phone:
            demo_parts.append(self.patient.phone)
        demographics = " • ".join(demo_parts)

        return ft.Column(
            [
                # Header with back button
                ft.Container(
                    content=ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=Colors.NEUTRAL_900,
                                icon_size=24,
                                on_click=lambda e: self.on_back() if self.on_back else None,
                            ),
                            ft.Text(
                                "Patient",
                                size=MobileTypography.TITLE_LARGE,
                                weight=ft.FontWeight.W_500,
                                color=Colors.NEUTRAL_900,
                            ),
                        ],
                    ),
                    bgcolor=Colors.NEUTRAL_0,
                    padding=ft.padding.only(
                        left=MobileSpacing.XS,
                        right=MobileSpacing.MD,
                        top=MobileSpacing.SM,
                        bottom=MobileSpacing.SM,
                    ),
                ),

                # Patient info card
                ft.Container(
                    content=ft.Column(
                        [
                            # Avatar and name
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            initials,
                                            size=MobileTypography.HEADLINE_LARGE,
                                            weight=ft.FontWeight.W_600,
                                            color=Colors.PRIMARY_500,
                                        ),
                                        width=72,
                                        height=72,
                                        border_radius=Radius.FULL,
                                        bgcolor=Colors.PRIMARY_50,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Container(width=MobileSpacing.MD),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                self.patient.name,
                                                size=MobileTypography.HEADLINE_MEDIUM,
                                                weight=ft.FontWeight.W_600,
                                                color=Colors.NEUTRAL_900,
                                            ),
                                            ft.Text(
                                                f"UHID: {self.patient.uhid}",
                                                size=MobileTypography.BODY_SMALL,
                                                color=Colors.NEUTRAL_600,
                                            ),
                                            ft.Text(
                                                demographics,
                                                size=MobileTypography.BODY_SMALL,
                                                color=Colors.NEUTRAL_500,
                                            ),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                ],
                            ),
                            ft.Container(height=MobileSpacing.MD),

                            # Quick action buttons
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        content=ft.Row(
                                            [
                                                ft.Icon(ft.Icons.PHONE, size=18),
                                                ft.Text("Call"),
                                            ],
                                            spacing=MobileSpacing.XS,
                                        ),
                                        style=ft.ButtonStyle(
                                            bgcolor=Colors.PRIMARY_500,
                                            color=Colors.NEUTRAL_0,
                                            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                                            padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                        ),
                                        height=40,
                                        on_click=lambda e: self._handle_call(),
                                    ),
                                    ft.OutlinedButton(
                                        content=ft.Row(
                                            [
                                                ft.Icon(ft.Icons.SHARE, size=18),
                                                ft.Text("Share Rx"),
                                            ],
                                            spacing=MobileSpacing.XS,
                                        ),
                                        style=ft.ButtonStyle(
                                            color=Colors.PRIMARY_500,
                                            side=ft.BorderSide(1, Colors.PRIMARY_500),
                                            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                                            padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                        ),
                                        height=40,
                                        on_click=lambda e: self._handle_share(),
                                    ),
                                    ft.OutlinedButton(
                                        content=ft.Row(
                                            [
                                                ft.Icon(ft.Icons.CALENDAR_TODAY, size=18),
                                                ft.Text("Appt"),
                                            ],
                                            spacing=MobileSpacing.XS,
                                        ),
                                        style=ft.ButtonStyle(
                                            color=Colors.PRIMARY_500,
                                            side=ft.BorderSide(1, Colors.PRIMARY_500),
                                            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                                            padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                        ),
                                        height=40,
                                        on_click=lambda e: self._handle_add_appointment(),
                                    ),
                                ],
                                spacing=MobileSpacing.SM,
                                wrap=True,
                            ),
                        ],
                    ),
                    bgcolor=Colors.NEUTRAL_0,
                    padding=MobileSpacing.SCREEN_PADDING,
                ),

                # Tabs
                ft.Tabs(
                    selected_index=0,
                    animation_duration=200,
                    tabs=[
                        ft.Tab(
                            text="Visits",
                            icon=ft.Icons.EVENT_NOTE,
                            content=ft.Stack(
                                [self.visits_list, self.visits_empty],
                                expand=True,
                            ),
                        ),
                        ft.Tab(
                            text="Labs",
                            icon=ft.Icons.SCIENCE,
                            content=ft.Stack(
                                [self.labs_list, self.labs_empty],
                                expand=True,
                            ),
                        ),
                        ft.Tab(
                            text="Procedures",
                            icon=ft.Icons.MEDICAL_SERVICES,
                            content=ft.Stack(
                                [self.procedures_list, self.procedures_empty],
                                expand=True,
                            ),
                        ),
                    ],
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _create_empty_state(self, message: str, icon: str) -> ft.Container:
        """Create an empty state container."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=48, color=Colors.NEUTRAL_300),
                    ft.Container(height=MobileSpacing.SM),
                    ft.Text(
                        message,
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    def set_visits(self, visits: List[VisitData]):
        """Set visit data."""
        self.visits_list.controls.clear()

        if not visits:
            self.visits_empty.visible = True
            self.visits_list.visible = False
        else:
            self.visits_empty.visible = False
            self.visits_list.visible = True

            for visit in visits:
                card = VisitCard(
                    visit_date=visit.date,
                    chief_complaint=visit.chief_complaint,
                    diagnosis=visit.diagnosis,
                )
                self.visits_list.controls.append(card)

        self.visits_list.update()

    def set_labs(self, labs: List[LabData]):
        """Set lab data."""
        self.labs_list.controls.clear()

        if not labs:
            self.labs_empty.visible = True
            self.labs_list.visible = False
        else:
            self.labs_empty.visible = False
            self.labs_list.visible = True

            for lab in labs:
                card = LabCard(
                    test_name=lab.test_name,
                    result=lab.result,
                    unit=lab.unit,
                    reference_range=lab.reference_range,
                    test_date=lab.date,
                    is_abnormal=lab.is_abnormal,
                )
                self.labs_list.controls.append(card)

        self.labs_list.update()

    def set_procedures(self, procedures: List[ProcedureData]):
        """Set procedure data."""
        self.procedures_list.controls.clear()

        if not procedures:
            self.procedures_empty.visible = True
            self.procedures_list.visible = False
        else:
            self.procedures_empty.visible = False
            self.procedures_list.visible = True

            for proc in procedures:
                card = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.MEDICAL_SERVICES,
                                        size=20,
                                        color=Colors.PRIMARY_500,
                                    ),
                                    ft.Text(
                                        proc.name,
                                        size=MobileTypography.BODY_LARGE,
                                        weight=ft.FontWeight.W_500,
                                        color=Colors.NEUTRAL_900,
                                    ),
                                ],
                                spacing=MobileSpacing.SM,
                            ),
                            ft.Text(
                                proc.date,
                                size=MobileTypography.BODY_SMALL,
                                color=Colors.NEUTRAL_600,
                            ),
                            ft.Text(
                                proc.details or "",
                                size=MobileTypography.BODY_SMALL,
                                color=Colors.NEUTRAL_500,
                            ) if proc.details else ft.Container(),
                        ],
                        spacing=4,
                    ),
                    bgcolor=Colors.NEUTRAL_0,
                    border_radius=Radius.CARD,
                    padding=MobileSpacing.CARD_PADDING,
                )
                self.procedures_list.controls.append(card)

        self.procedures_list.update()

    def _handle_call(self):
        """Handle call button."""
        if self.on_call and self.patient and self.patient.phone:
            self.on_call(self.patient.phone)

    def _handle_share(self):
        """Handle share button."""
        if self.on_share and self.patient:
            self.on_share(self.patient.id)

    def _handle_add_appointment(self):
        """Handle add appointment button."""
        if self.on_add_appointment and self.patient:
            self.on_add_appointment(self.patient.id)
