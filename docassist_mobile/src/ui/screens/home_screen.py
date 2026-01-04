"""
Home Screen - Today's appointments and quick access.

Premium home screen showing today's schedule and recent patients.
"""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..components.appointment_card import AppointmentCard
from ..components.sync_indicator import SyncIndicator


@dataclass
class AppointmentData:
    """Appointment display data."""
    id: int
    patient_id: int
    patient_name: str
    time: str
    reason: Optional[str] = None


class HomeScreen(ft.Container):
    """
    Home screen with today's appointments and quick access.

    Usage:
        home = HomeScreen(
            on_appointment_click=handle_appointment,
            on_refresh=handle_refresh,
        )
    """

    def __init__(
        self,
        on_appointment_click: Optional[Callable[[int], None]] = None,
        on_patient_click: Optional[Callable[[int], None]] = None,
        on_refresh: Optional[Callable] = None,
        sync_status: str = "synced",
        last_sync: str = "Just now",
    ):
        self.on_appointment_click = on_appointment_click
        self.on_patient_click = on_patient_click
        self.on_refresh = on_refresh

        # Sync indicator
        self.sync_indicator = SyncIndicator(
            status=sync_status,
            last_sync=last_sync,
        )

        # Appointments list
        self.appointments_list = ft.ListView(
            spacing=MobileSpacing.SM,
            padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
            expand=True,
        )

        # Empty state
        self.empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.EVENT_AVAILABLE,
                        size=64,
                        color=Colors.NEUTRAL_300,
                    ),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        "No appointments today",
                        size=MobileTypography.TITLE_MEDIUM,
                        color=Colors.NEUTRAL_600,
                    ),
                    ft.Text(
                        "Your schedule is clear",
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

        # Build content
        content = ft.Column(
            [
                # Header with sync status
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Today",
                                size=MobileTypography.HEADLINE_LARGE,
                                weight=ft.FontWeight.W_600,
                                color=Colors.NEUTRAL_900,
                            ),
                            ft.Container(expand=True),
                            self.sync_indicator,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=MobileSpacing.SCREEN_PADDING,
                ),

                # Date
                ft.Container(
                    content=ft.Text(
                        datetime.now().strftime("%A, %B %d"),
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_600,
                    ),
                    padding=ft.padding.only(
                        left=MobileSpacing.SCREEN_PADDING,
                        bottom=MobileSpacing.MD,
                    ),
                ),

                # Appointments section
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Appointments",
                                size=MobileTypography.TITLE_MEDIUM,
                                weight=ft.FontWeight.W_600,
                                color=Colors.NEUTRAL_900,
                            ),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(
                                    "0",
                                    size=MobileTypography.LABEL_MEDIUM,
                                    color=Colors.NEUTRAL_0,
                                ),
                                bgcolor=Colors.PRIMARY_500,
                                border_radius=Radius.FULL,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            ),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
                ),
                ft.Container(height=MobileSpacing.SM),

                # Appointments list or empty state
                ft.Stack(
                    [
                        self.appointments_list,
                        self.empty_state,
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

        # Show empty state by default
        self._show_empty_state()

    def set_appointments(self, appointments: List[AppointmentData]):
        """Update appointments list."""
        self.appointments_list.controls.clear()

        if not appointments:
            self._show_empty_state()
            return

        self._hide_empty_state()

        for appt in appointments:
            card = AppointmentCard(
                time=appt.time,
                patient_name=appt.patient_name,
                reason=appt.reason,
                on_click=lambda e, pid=appt.patient_id: self._on_appointment_click(pid),
            )
            self.appointments_list.controls.append(card)

        # Update count badge
        self._update_count(len(appointments))
        self.appointments_list.update()

    def _on_appointment_click(self, patient_id: int):
        """Handle appointment card click."""
        if self.on_appointment_click:
            self.on_appointment_click(patient_id)

    def _show_empty_state(self):
        """Show empty state."""
        self.empty_state.visible = True
        self.appointments_list.visible = False
        self._update_count(0)

    def _hide_empty_state(self):
        """Hide empty state."""
        self.empty_state.visible = False
        self.appointments_list.visible = True

    def _update_count(self, count: int):
        """Update appointment count badge."""
        # Find and update the count badge
        # This is in the header Row
        pass  # TODO: implement if needed

    def update_sync_status(self, status: str, last_sync: str = ""):
        """Update sync indicator."""
        self.sync_indicator = SyncIndicator(status=status, last_sync=last_sync)
        self.update()

    def refresh(self):
        """Trigger refresh."""
        if self.on_refresh:
            self.on_refresh()
