"""
Navigation Component - Bottom navigation bar for mobile app.

Premium bottom navigation with smooth transitions.
"""

import flet as ft
from typing import Callable, Optional
from enum import Enum

from .tokens import Colors, MobileSpacing


class NavDestination(Enum):
    """Navigation destinations."""
    HOME = 0
    PATIENTS = 1
    SETTINGS = 2


class BottomNavigation(ft.NavigationBar):
    """
    Premium bottom navigation bar.

    Usage:
        nav = BottomNavigation(on_change=handle_nav_change)
    """

    def __init__(
        self,
        selected_index: int = 0,
        on_change: Optional[Callable[[NavDestination], None]] = None,
    ):
        self._on_nav_change = on_change

        super().__init__(
            selected_index=selected_index,
            height=MobileSpacing.NAV_HEIGHT,
            bgcolor=Colors.NEUTRAL_0,
            indicator_color=Colors.PRIMARY_50,
            shadow_color=Colors.NEUTRAL_900,
            elevation=8,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PEOPLE_OUTLINED,
                    selected_icon=ft.Icons.PEOPLE,
                    label="Patients",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            on_change=self._handle_change,
        )

    def _handle_change(self, e):
        """Handle navigation change."""
        if self._on_nav_change:
            destination = NavDestination(e.control.selected_index)
            self._on_nav_change(destination)

    def set_index(self, index: int):
        """Set selected index programmatically."""
        self.selected_index = index
        self.update()

    def go_to(self, destination: NavDestination):
        """Navigate to a specific destination."""
        self.set_index(destination.value)


class AppHeader(ft.Container):
    """
    App header bar with title and actions.

    Usage:
        header = AppHeader(
            title="Patients",
            show_back=True,
            on_back=handle_back,
        )
    """

    def __init__(
        self,
        title: str = "",
        show_back: bool = False,
        on_back: Optional[Callable] = None,
        actions: Optional[list] = None,
    ):
        self.on_back = on_back

        # Build content
        row_items = []

        # Back button
        if show_back:
            row_items.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=Colors.NEUTRAL_900,
                    icon_size=24,
                    on_click=lambda e: self.on_back() if self.on_back else None,
                )
            )
        else:
            row_items.append(ft.Container(width=MobileSpacing.MD))

        # Title
        row_items.append(
            ft.Text(
                title,
                size=20,
                weight=ft.FontWeight.W_500,
                color=Colors.NEUTRAL_900,
                expand=True,
            )
        )

        # Actions
        if actions:
            row_items.extend(actions)

        super().__init__(
            content=ft.Row(
                row_items,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colors.NEUTRAL_0,
            padding=ft.padding.symmetric(
                horizontal=MobileSpacing.XS,
                vertical=MobileSpacing.SM,
            ),
            shadow=ft.BoxShadow(
                blur_radius=4,
                spread_radius=0,
                offset=ft.Offset(0, 2),
                color="rgba(0,0,0,0.08)",
            ),
        )


class PageTransition:
    """
    Page transition animations.

    Provides smooth transitions between screens.
    """

    @staticmethod
    def slide_in_right(control: ft.Control, duration: int = 200):
        """Slide in from right animation."""
        control.animate_offset = ft.animation.Animation(
            duration,
            ft.AnimationCurve.EASE_OUT,
        )
        control.offset = ft.transform.Offset(1, 0)
        control.update()
        control.offset = ft.transform.Offset(0, 0)
        control.update()

    @staticmethod
    def slide_out_left(control: ft.Control, duration: int = 200):
        """Slide out to left animation."""
        control.animate_offset = ft.animation.Animation(
            duration,
            ft.AnimationCurve.EASE_IN,
        )
        control.offset = ft.transform.Offset(-1, 0)
        control.update()

    @staticmethod
    def fade_in(control: ft.Control, duration: int = 200):
        """Fade in animation."""
        control.animate_opacity = ft.animation.Animation(
            duration,
            ft.AnimationCurve.EASE_OUT,
        )
        control.opacity = 0
        control.update()
        control.opacity = 1
        control.update()


class NavigationStack:
    """
    Navigation stack for managing screen history.

    Provides push/pop navigation with back handling.
    """

    def __init__(self):
        self._stack: list = []

    def push(self, screen_name: str, params: dict = None):
        """Push a screen onto the stack."""
        self._stack.append({
            'screen': screen_name,
            'params': params or {},
        })

    def pop(self) -> Optional[dict]:
        """Pop the top screen from the stack."""
        if len(self._stack) > 1:
            return self._stack.pop()
        return None

    def peek(self) -> Optional[dict]:
        """Peek at the top screen."""
        if self._stack:
            return self._stack[-1]
        return None

    def clear(self):
        """Clear the stack."""
        self._stack.clear()

    def replace(self, screen_name: str, params: dict = None):
        """Replace the top screen."""
        if self._stack:
            self._stack.pop()
        self.push(screen_name, params)

    @property
    def can_pop(self) -> bool:
        """Check if we can pop (has more than one screen)."""
        return len(self._stack) > 1

    @property
    def depth(self) -> int:
        """Get stack depth."""
        return len(self._stack)
