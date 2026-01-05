"""Navigation Component - Tab navigation for main content area."""

import flet as ft
from typing import Optional, Callable
from enum import Enum


class NavigationTab(str, Enum):
    """Available navigation tabs."""
    PRESCRIPTION = "prescription"
    TIMELINE = "timeline"
    GROWTH = "growth"
    SETTINGS = "settings"


class NavigationRail(ft.UserControl):
    """
    Navigation rail component for switching between main views.

    Features:
    - Prescription (Rx) tab
    - Timeline (patient history) tab
    - Growth (practice analytics) tab
    - Settings tab
    - Smooth transitions with animations
    - Vertical rail design for desktop
    """

    def __init__(
        self,
        on_tab_change: Optional[Callable[[NavigationTab], None]] = None,
        initial_tab: NavigationTab = NavigationTab.PRESCRIPTION,
        is_dark: bool = False,
    ):
        """Initialize navigation rail.

        Args:
            on_tab_change: Callback when tab is changed
            initial_tab: Initially selected tab
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_tab_change = on_tab_change
        self.selected_tab = initial_tab
        self.is_dark = is_dark

        # UI components
        self.rail: Optional[ft.NavigationRail] = None

    def build(self):
        """Build the navigation rail UI."""
        self.rail = ft.NavigationRail(
            selected_index=self._get_tab_index(self.selected_tab),
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.PRESCRIPTION_OUTLINED,
                    selected_icon=ft.Icons.PRESCRIPTION,
                    label="Prescription",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.TIMELINE_OUTLINED,
                    selected_icon=ft.Icons.TIMELINE,
                    label="Timeline",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.TRENDING_UP_OUTLINED,
                    selected_icon=ft.Icons.TRENDING_UP,
                    label="Growth",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            on_change=self._on_rail_change,
            bgcolor="#1A2332" if self.is_dark else ft.Colors.GREY_50,
        )

        return ft.Container(
            content=self.rail,
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_300)),
        )

    def _on_rail_change(self, e):
        """Handle navigation rail change."""
        index = e.control.selected_index
        self.selected_tab = self._get_tab_from_index(index)

        if self.on_tab_change:
            self.on_tab_change(self.selected_tab)

    def set_selected_tab(self, tab: NavigationTab):
        """Programmatically set the selected tab.

        Args:
            tab: Tab to select
        """
        self.selected_tab = tab

        if self.rail:
            self.rail.selected_index = self._get_tab_index(tab)
            self.update()

    def _get_tab_index(self, tab: NavigationTab) -> int:
        """Get index for tab.

        Args:
            tab: NavigationTab

        Returns:
            Index in destinations list
        """
        return {
            NavigationTab.PRESCRIPTION: 0,
            NavigationTab.TIMELINE: 1,
            NavigationTab.GROWTH: 2,
            NavigationTab.SETTINGS: 3,
        }.get(tab, 0)

    def _get_tab_from_index(self, index: int) -> NavigationTab:
        """Get tab from index.

        Args:
            index: Index in destinations list

        Returns:
            NavigationTab
        """
        return {
            0: NavigationTab.PRESCRIPTION,
            1: NavigationTab.TIMELINE,
            2: NavigationTab.GROWTH,
            3: NavigationTab.SETTINGS,
        }.get(index, NavigationTab.PRESCRIPTION)


class TabNavigationBar(ft.UserControl):
    """
    Alternative tab navigation using Flet Tabs (horizontal).

    Can be used instead of NavigationRail for a more traditional tab interface.
    """

    def __init__(
        self,
        on_tab_change: Optional[Callable[[NavigationTab], None]] = None,
        initial_tab: NavigationTab = NavigationTab.PRESCRIPTION,
        is_dark: bool = False,
    ):
        """Initialize tab navigation bar.

        Args:
            on_tab_change: Callback when tab is changed
            initial_tab: Initially selected tab
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_tab_change = on_tab_change
        self.selected_tab = initial_tab
        self.is_dark = is_dark

        # UI components
        self.tabs: Optional[ft.Tabs] = None

    def build(self):
        """Build the tab navigation bar UI."""
        self.tabs = ft.Tabs(
            selected_index=self._get_tab_index(self.selected_tab),
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Prescription",
                    icon=ft.Icons.PRESCRIPTION,
                ),
                ft.Tab(
                    text="Timeline",
                    icon=ft.Icons.TIMELINE,
                ),
                ft.Tab(
                    text="Growth",
                    icon=ft.Icons.TRENDING_UP,
                ),
                ft.Tab(
                    text="Settings",
                    icon=ft.Icons.SETTINGS,
                ),
            ],
            on_change=self._on_tab_change,
        )

        return ft.Container(
            content=self.tabs,
            bgcolor="#1A2332" if self.is_dark else ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_300)),
            padding=ft.padding.symmetric(horizontal=10),
        )

    def _on_tab_change(self, e):
        """Handle tab change."""
        index = e.control.selected_index
        self.selected_tab = self._get_tab_from_index(index)

        if self.on_tab_change:
            self.on_tab_change(self.selected_tab)

    def set_selected_tab(self, tab: NavigationTab):
        """Programmatically set the selected tab.

        Args:
            tab: Tab to select
        """
        self.selected_tab = tab

        if self.tabs:
            self.tabs.selected_index = self._get_tab_index(tab)
            self.update()

    def _get_tab_index(self, tab: NavigationTab) -> int:
        """Get index for tab.

        Args:
            tab: NavigationTab

        Returns:
            Index in tabs list
        """
        return {
            NavigationTab.PRESCRIPTION: 0,
            NavigationTab.TIMELINE: 1,
            NavigationTab.GROWTH: 2,
            NavigationTab.SETTINGS: 3,
        }.get(tab, 0)

    def _get_tab_from_index(self, index: int) -> NavigationTab:
        """Get tab from index.

        Args:
            index: Index in tabs list

        Returns:
            NavigationTab
        """
        return {
            0: NavigationTab.PRESCRIPTION,
            1: NavigationTab.TIMELINE,
            2: NavigationTab.GROWTH,
            3: NavigationTab.SETTINGS,
        }.get(index, NavigationTab.PRESCRIPTION)
