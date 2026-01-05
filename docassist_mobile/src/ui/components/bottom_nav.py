"""
Bottom Navigation Bar Component

Premium bottom navigation for mobile app with smooth transitions
and haptic feedback.
"""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..tokens import Colors, MobileSpacing


class NavTab(Enum):
    """Navigation tabs."""
    HOME = 0
    PATIENTS = 1
    QUICK_NOTE = 2
    SETTINGS = 3


@dataclass
class NavDestination:
    """Navigation destination configuration."""
    icon: str
    selected_icon: str
    label: str
    tab: NavTab


class BottomNavBar(ft.NavigationBar):
    """
    Premium bottom navigation bar with haptic feedback.

    Features:
    - Smooth tab transitions
    - Haptic feedback on selection
    - Badge support for notifications
    - Premium Material 3 design

    Usage:
        nav = BottomNavBar(
            selected_tab=NavTab.HOME,
            on_change=handle_nav_change,
            haptic_feedback=haptic,
        )
    """

    def __init__(
        self,
        selected_tab: NavTab = NavTab.HOME,
        on_change: Optional[Callable[[NavTab], None]] = None,
        notification_count: int = 0,
        haptic_feedback=None,
    ):
        self._on_change = on_change
        self.haptic_feedback = haptic_feedback
        self.notification_count = notification_count

        # Define navigation destinations
        self.destinations = [
            NavDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="Home",
                tab=NavTab.HOME,
            ),
            NavDestination(
                icon=ft.Icons.PEOPLE_OUTLINED,
                selected_icon=ft.Icons.PEOPLE,
                label="Patients",
                tab=NavTab.PATIENTS,
            ),
            NavDestination(
                icon=ft.Icons.NOTE_ADD_OUTLINED,
                selected_icon=ft.Icons.NOTE_ADD,
                label="Quick Note",
                tab=NavTab.QUICK_NOTE,
            ),
            NavDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Settings",
                tab=NavTab.SETTINGS,
            ),
        ]

        super().__init__(
            selected_index=selected_tab.value,
            height=MobileSpacing.NAV_HEIGHT,
            bgcolor=Colors.NEUTRAL_0,
            indicator_color=Colors.PRIMARY_50,
            destinations=self._build_destinations(),
            on_change=self._handle_change,
            border=ft.border.only(top=ft.BorderSide(1, Colors.NEUTRAL_200)),
        )

    def _build_destinations(self) -> List[ft.NavigationBarDestination]:
        """Build navigation destinations."""
        nav_destinations = []

        for dest in self.destinations:
            # Add badge for Quick Note if there are notifications
            badge = None
            if dest.tab == NavTab.QUICK_NOTE and self.notification_count > 0:
                badge = self.notification_count

            nav_destinations.append(
                ft.NavigationBarDestination(
                    icon=dest.icon,
                    selected_icon=dest.selected_icon,
                    label=dest.label,
                    badge=badge,
                )
            )

        return nav_destinations

    def _handle_change(self, e):
        """Handle navigation change with haptic feedback."""
        # Trigger haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.light()

        # Get selected tab
        index = e.control.selected_index
        selected_tab = NavTab(index)

        # Call callback
        if self._on_change:
            self._on_change(selected_tab)

    def set_notification_count(self, count: int):
        """Update notification count badge."""
        self.notification_count = count
        self.destinations = self._build_destinations()
        self.update()

    def select_tab(self, tab: NavTab):
        """Programmatically select a tab."""
        self.selected_index = tab.value
        self.update()

    def get_selected_tab(self) -> NavTab:
        """Get currently selected tab."""
        return NavTab(self.selected_index)
