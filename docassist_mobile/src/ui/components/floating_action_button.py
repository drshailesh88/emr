"""
Floating Action Button (FAB) Component with Expandable Mini-FABs.

Premium expandable FAB that shows quick action buttons in an arc pattern.
Features smooth animations, haptic feedback, and overlay backdrop.
"""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass
import math

from ..tokens import Colors, MobileSpacing, Radius
from ..animations import Animations, AnimationDuration
from ..haptics import HapticFeedback, HapticType


@dataclass
class FABAction:
    """Configuration for a mini-FAB action."""
    icon: str
    label: str
    on_click: Callable
    color: Optional[str] = None


class FloatingActionButton(ft.Stack):
    """
    Premium Floating Action Button with expandable mini-FABs.

    When tapped, expands to show mini-FABs in an arc pattern with labels.
    Features:
    - Smooth 60fps animations
    - Haptic feedback on interactions
    - Background overlay dims when expanded
    - Tap outside to collapse

    Usage:
        fab = FloatingActionButton(
            actions=[
                FABAction(
                    icon=ft.Icons.PERSON_ADD,
                    label="Add Patient",
                    on_click=handle_add_patient
                ),
                FABAction(
                    icon=ft.Icons.NOTE_ADD,
                    label="New Visit",
                    on_click=handle_new_visit
                ),
            ],
            haptic_feedback=haptics,
        )
    """

    def __init__(
        self,
        actions: List[FABAction],
        page: ft.Page,
        haptic_feedback: Optional[HapticFeedback] = None,
        primary_color: str = Colors.PRIMARY_500,
        on_primary_color: str = Colors.NEUTRAL_0,
    ):
        self.actions = actions
        self.page = page
        self.haptic_feedback = haptic_feedback
        self.primary_color = primary_color
        self.on_primary_color = on_primary_color
        self.is_expanded = False

        # Create UI components
        self.backdrop = self._create_backdrop()
        self.mini_fabs = self._create_mini_fabs()
        self.main_fab = self._create_main_fab()

        # Build stack with all elements
        super().__init__(
            controls=[
                self.backdrop,
                *self.mini_fabs,
                self.main_fab,
            ],
            width=300,  # Wide enough for labels
            height=400,  # Tall enough for arc
        )

    def _create_backdrop(self) -> ft.Container:
        """Create dimming backdrop overlay."""
        return ft.Container(
            bgcolor="rgba(0, 0, 0, 0.5)",
            opacity=0,
            animate_opacity=Animations.fade_in(AnimationDuration.FAST.value),
            on_click=self._collapse,
            expand=True,
        )

    def _create_main_fab(self) -> ft.Container:
        """Create main FAB button."""
        # FAB content (icon that rotates when expanded)
        self.fab_icon = ft.Icon(
            ft.Icons.ADD,
            color=self.on_primary_color,
            size=28,
        )

        # FAB container
        fab_button = ft.Container(
            content=self.fab_icon,
            width=56,
            height=56,
            border_radius=Radius.FULL,
            bgcolor=self.primary_color,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color="rgba(0, 0, 0, 0.3)",
                offset=ft.Offset(0, 4),
            ),
            on_click=self._toggle,
            ink=True,
            animate_scale=Animations.scale_tap(),
            animate_rotate=Animations.fade_in(AnimationDuration.NORMAL.value),
            scale=1.0,
            rotate=0,
        )

        # Position FAB at bottom-right
        return ft.Container(
            content=fab_button,
            right=0,
            bottom=0,
        )

    def _create_mini_fabs(self) -> List[ft.Container]:
        """Create mini-FAB buttons arranged in arc pattern."""
        mini_fabs = []

        # Arc parameters
        arc_radius = 120  # Distance from main FAB
        start_angle = 180  # Start angle (degrees) - left side
        angle_span = 90   # Total angle span (degrees)

        for i, action in enumerate(self.actions):
            # Calculate position in arc
            if len(self.actions) == 1:
                angle = start_angle + angle_span / 2
            else:
                angle = start_angle + (angle_span * i / (len(self.actions) - 1))

            angle_rad = math.radians(angle)

            # Position relative to main FAB (bottom-right corner)
            x = arc_radius * math.cos(angle_rad)
            y = arc_radius * math.sin(angle_rad)

            # Create mini-FAB
            mini_fab = self._create_mini_fab(action, x, y, i)
            mini_fabs.append(mini_fab)

        return mini_fabs

    def _create_mini_fab(
        self,
        action: FABAction,
        x: float,
        y: float,
        index: int,
    ) -> ft.Container:
        """Create a single mini-FAB with label."""
        # Mini-FAB button
        fab_color = action.color or Colors.NEUTRAL_0

        mini_fab_button = ft.Container(
            content=ft.Icon(
                action.icon,
                color=Colors.NEUTRAL_700,
                size=20,
            ),
            width=40,
            height=40,
            border_radius=Radius.FULL,
            bgcolor=fab_color,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color="rgba(0, 0, 0, 0.2)",
                offset=ft.Offset(0, 2),
            ),
            on_click=lambda e, a=action: self._handle_action_click(a),
            ink=True,
            animate_scale=Animations.scale_tap(),
            scale=1.0,
        )

        # Label
        label = ft.Container(
            content=ft.Text(
                action.label,
                size=12,
                weight=ft.FontWeight.W_500,
                color=Colors.NEUTRAL_900,
            ),
            bgcolor=Colors.NEUTRAL_0,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=Radius.MD,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color="rgba(0, 0, 0, 0.15)",
                offset=ft.Offset(0, 2),
            ),
        )

        # Row with label and button
        content_row = ft.Row(
            [label, mini_fab_button],
            spacing=8,
            alignment=ft.MainAxisAlignment.END,
        )

        # Container positioned in arc
        # Start collapsed (at FAB position)
        return ft.Container(
            content=content_row,
            right=0,  # Will animate to final position
            bottom=0,  # Will animate to final position
            opacity=0,
            animate_opacity=Animations.fade_in(AnimationDuration.NORMAL.value),
            animate=Animations.fade_in(AnimationDuration.NORMAL.value),
            data={"target_x": x, "target_y": y},  # Store target position
        )

    def _toggle(self, e):
        """Toggle FAB expansion."""
        if self.is_expanded:
            self._collapse(e)
        else:
            self._expand(e)

    def _expand(self, e):
        """Expand FAB to show mini-FABs."""
        if self.is_expanded:
            return

        self.is_expanded = True

        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        # Rotate main FAB icon (+ becomes ×)
        self.fab_icon.name = ft.Icons.CLOSE
        self.main_fab.content.rotate = 0.125  # 45 degrees (1/8 turn)

        # Show backdrop
        self.backdrop.opacity = 1

        # Animate mini-FABs into position with stagger
        for i, mini_fab in enumerate(self.mini_fabs):
            # Delay each mini-FAB slightly for stagger effect
            def animate_mini_fab(mf=mini_fab, delay=i):
                import time
                if delay > 0:
                    time.sleep(delay * 0.03)  # 30ms stagger

                target_x = mf.data["target_x"]
                target_y = mf.data["target_y"]

                # Calculate final position (offset from bottom-right)
                mf.right = -target_x
                mf.bottom = -target_y
                mf.opacity = 1

                if self.page:
                    mf.update()

            # Run animation in separate thread for stagger effect
            import threading
            threading.Thread(target=animate_mini_fab, daemon=True).start()

        self.update()

    def _collapse(self, e=None):
        """Collapse FAB to hide mini-FABs."""
        if not self.is_expanded:
            return

        self.is_expanded = False

        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.light()

        # Rotate main FAB icon back (× becomes +)
        self.fab_icon.name = ft.Icons.ADD
        self.main_fab.content.rotate = 0

        # Hide backdrop
        self.backdrop.opacity = 0

        # Collapse mini-FABs back to FAB position
        for mini_fab in self.mini_fabs:
            mini_fab.right = 0
            mini_fab.bottom = 0
            mini_fab.opacity = 0
            mini_fab.update()

        self.update()

    def _handle_action_click(self, action: FABAction):
        """Handle mini-FAB action click."""
        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.light()

        # Collapse FAB
        self._collapse()

        # Call action handler
        if action.on_click:
            action.on_click()


class SimpleFAB(ft.Container):
    """
    Simple FAB without expansion (single action).

    Usage:
        fab = SimpleFAB(
            icon=ft.Icons.ADD,
            on_click=handle_add,
            haptic_feedback=haptics,
        )
    """

    def __init__(
        self,
        icon: str,
        on_click: Callable,
        haptic_feedback: Optional[HapticFeedback] = None,
        tooltip: Optional[str] = None,
        bgcolor: str = Colors.PRIMARY_500,
        icon_color: str = Colors.NEUTRAL_0,
    ):
        self.haptic_feedback = haptic_feedback
        self._original_on_click = on_click

        # FAB button
        fab_button = ft.Container(
            content=ft.Icon(icon, color=icon_color, size=28),
            width=56,
            height=56,
            border_radius=Radius.FULL,
            bgcolor=bgcolor,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color="rgba(0, 0, 0, 0.3)",
                offset=ft.Offset(0, 4),
            ),
            tooltip=tooltip,
            ink=True,
            on_click=self._handle_click,
            animate_scale=Animations.scale_tap(),
            scale=1.0,
        )

        super().__init__(
            content=fab_button,
        )

    def _handle_click(self, e):
        """Handle click with haptic feedback."""
        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        # Scale animation
        self.content.scale = 0.9
        self.update()

        # Call original handler
        if self._original_on_click:
            self._original_on_click()

        # Scale back
        self.content.scale = 1.0
        self.update()


__all__ = [
    'FloatingActionButton',
    'SimpleFAB',
    'FABAction',
]
