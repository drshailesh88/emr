"""
Page Indicator Component - Dot indicators for multi-page flows.

Shows current page position in a multi-page carousel/slider.
Premium smooth animations between states.
"""

import flet as ft
from typing import Optional

from ..tokens import Colors, MobileSpacing
from ..animations import Animations


class PageIndicator(ft.Row):
    """
    Page indicator with animated dots.

    Shows a row of dots where the active dot is larger and primary-colored.
    Smooth transitions when changing pages.

    Usage:
        indicator = PageIndicator(
            total_pages=4,
            current_page=0,
            on_page_click=handle_page_click,
        )
    """

    def __init__(
        self,
        total_pages: int,
        current_page: int = 0,
        on_page_click: Optional[callable] = None,
        active_color: str = Colors.PRIMARY_500,
        inactive_color: str = Colors.NEUTRAL_300,
        active_size: int = 10,
        inactive_size: int = 6,
        spacing: int = 8,
    ):
        self.total_pages = total_pages
        self.current_page = current_page
        self.on_page_click = on_page_click
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.active_size = active_size
        self.inactive_size = inactive_size

        # Create dots
        self.dots: list[ft.Container] = []
        for i in range(total_pages):
            dot = self._create_dot(i)
            self.dots.append(dot)

        super().__init__(
            controls=self.dots,
            spacing=spacing,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Update initial state
        self._update_dots()

    def _create_dot(self, index: int) -> ft.Container:
        """
        Create a single dot indicator.

        Args:
            index: Page index for this dot

        Returns:
            Container with animated dot
        """
        is_active = index == self.current_page

        dot_container = ft.Container(
            width=self.active_size if is_active else self.inactive_size,
            height=self.active_size if is_active else self.inactive_size,
            border_radius=100,
            bgcolor=self.active_color if is_active else self.inactive_color,
            animate=Animations.scale_tap(),
            animate_size=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            animate_bgcolor=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            data=index,  # Store index in data
        )

        # Add click handler if provided
        if self.on_page_click:
            dot_container.on_click = self._handle_dot_click
            dot_container.ink = True

        return dot_container

    def _handle_dot_click(self, e):
        """Handle dot click."""
        page_index = e.control.data
        if self.on_page_click:
            self.on_page_click(page_index)

    def _update_dots(self):
        """Update dot states based on current page."""
        for i, dot in enumerate(self.dots):
            is_active = i == self.current_page

            # Animate size and color
            dot.width = self.active_size if is_active else self.inactive_size
            dot.height = self.active_size if is_active else self.inactive_size
            dot.bgcolor = self.active_color if is_active else self.inactive_color

    def set_page(self, page: int):
        """
        Set the current page.

        Args:
            page: Page index (0-based)
        """
        if 0 <= page < self.total_pages:
            self.current_page = page
            self._update_dots()
            self.update()

    def next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages - 1:
            self.set_page(self.current_page + 1)

    def previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.set_page(self.current_page - 1)


class ProgressIndicator(ft.Container):
    """
    Linear progress indicator for step-by-step flows.

    Alternative to dots for showing progress through multi-step processes.

    Usage:
        progress = ProgressIndicator(
            total_steps=4,
            current_step=1,
        )
    """

    def __init__(
        self,
        total_steps: int,
        current_step: int = 0,
        height: int = 4,
        active_color: str = Colors.PRIMARY_500,
        inactive_color: str = Colors.NEUTRAL_200,
    ):
        self.total_steps = total_steps
        self.current_step = current_step
        self.active_color = active_color
        self.inactive_color = inactive_color

        # Progress bar
        self.progress_bar = ft.Container(
            width=0,  # Will be calculated
            height=height,
            bgcolor=active_color,
            border_radius=height // 2,
            animate_size=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

        # Background bar
        self.background_bar = ft.Container(
            content=self.progress_bar,
            height=height,
            bgcolor=inactive_color,
            border_radius=height // 2,
            expand=True,
        )

        super().__init__(
            content=self.background_bar,
            padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
        )

    def set_step(self, step: int):
        """
        Set the current step.

        Args:
            step: Step index (0-based)
        """
        if 0 <= step < self.total_steps:
            self.current_step = step
            self._update_progress()

    def _update_progress(self):
        """Update progress bar width."""
        # Calculate progress percentage
        progress = (self.current_step + 1) / self.total_steps

        # Get parent width (this is tricky in Flet, use percentage)
        # For now, we'll use a fixed calculation
        # In practice, this would need to be calculated after layout
        self.progress_bar.expand = progress
        self.update()

    def next_step(self):
        """Go to next step."""
        if self.current_step < self.total_steps - 1:
            self.set_step(self.current_step + 1)

    def previous_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.set_step(self.current_step - 1)


class StepIndicator(ft.Row):
    """
    Step indicator with numbered circles.

    Shows numbered steps with lines connecting them.
    Good for linear multi-step forms.

    Usage:
        steps = StepIndicator(
            steps=["Account", "Profile", "Preferences", "Done"],
            current_step=1,
        )
    """

    def __init__(
        self,
        steps: list[str],
        current_step: int = 0,
        active_color: str = Colors.PRIMARY_500,
        inactive_color: str = Colors.NEUTRAL_300,
        completed_color: str = Colors.SUCCESS_MAIN,
    ):
        self.steps = steps
        self.current_step = current_step
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.completed_color = completed_color

        # Create step controls
        step_controls = []
        for i, step_name in enumerate(steps):
            # Add step circle
            step_controls.append(self._create_step_circle(i))

            # Add connecting line (except after last step)
            if i < len(steps) - 1:
                step_controls.append(self._create_connecting_line(i))

        super().__init__(
            controls=step_controls,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
        )

    def _create_step_circle(self, index: int) -> ft.Container:
        """Create a numbered step circle."""
        is_completed = index < self.current_step
        is_active = index == self.current_step

        if is_completed:
            color = self.completed_color
            content = ft.Icon(ft.Icons.CHECK, size=16, color=Colors.NEUTRAL_0)
        else:
            color = self.active_color if is_active else self.inactive_color
            content = ft.Text(
                str(index + 1),
                color=Colors.NEUTRAL_0 if is_active else self.inactive_color,
                weight=ft.FontWeight.BOLD,
                size=14,
            )

        return ft.Container(
            content=content,
            width=32,
            height=32,
            border_radius=16,
            bgcolor=color if (is_active or is_completed) else Colors.NEUTRAL_0,
            border=ft.border.all(2, color),
            alignment=ft.alignment.center,
            animate_bgcolor=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    def _create_connecting_line(self, index: int) -> ft.Container:
        """Create a line connecting two steps."""
        is_completed = index < self.current_step

        return ft.Container(
            width=40,
            height=2,
            bgcolor=self.completed_color if is_completed else self.inactive_color,
            animate_bgcolor=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    def set_step(self, step: int):
        """Set the current step."""
        if 0 <= step < len(self.steps):
            self.current_step = step
            # Rebuild controls
            self.controls.clear()

            step_controls = []
            for i, step_name in enumerate(self.steps):
                step_controls.append(self._create_step_circle(i))
                if i < len(self.steps) - 1:
                    step_controls.append(self._create_connecting_line(i))

            self.controls = step_controls
            self.update()


__all__ = [
    'PageIndicator',
    'ProgressIndicator',
    'StepIndicator',
]
