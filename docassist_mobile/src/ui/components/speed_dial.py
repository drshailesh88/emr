"""
Speed Dial Component - Vertical Stack Alternative to Expandable FAB.

Provides a vertical stack of mini-FABs that appear from bottom with staggered animation.
Each mini-FAB displays icon with label to the left.
"""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass

from ..tokens import Colors, MobileSpacing, Radius
from ..animations import Animations, AnimationDuration, StaggeredAnimation
from ..haptics import HapticFeedback


@dataclass
class SpeedDialAction:
    """Configuration for a speed dial action."""
    icon: str
    label: str
    on_click: Callable
    color: Optional[str] = None
    icon_color: Optional[str] = None


class SpeedDial(ft.Stack):
    """
    Speed Dial component with vertical stack of actions.

    Mini-FABs appear from bottom in a staggered animation.
    Each action shows icon + label to the left.

    Features:
    - Staggered entrance animation (items appear one by one)
    - Background overlay when expanded
    - Haptic feedback on interactions
    - Premium 60fps animations

    Usage:
        speed_dial = SpeedDial(
            actions=[
                SpeedDialAction(
                    icon=ft.Icons.PERSON_ADD,
                    label="Add Patient",
                    on_click=handle_add_patient,
                ),
                SpeedDialAction(
                    icon=ft.Icons.NOTE_ADD,
                    label="New Visit",
                    on_click=handle_new_visit,
                ),
            ],
            page=page,
            haptic_feedback=haptics,
        )
    """

    def __init__(
        self,
        actions: List[SpeedDialAction],
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
        self.action_items = self._create_action_items()
        self.main_fab = self._create_main_fab()

        # Build stack
        super().__init__(
            controls=[
                self.backdrop,
                *self.action_items,
                self.main_fab,
            ],
            width=250,  # Wide enough for labels
            height=400,  # Tall enough for all items
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
        # FAB icon
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

    def _create_action_items(self) -> List[ft.Container]:
        """Create action items in vertical stack."""
        items = []

        # Spacing between items
        item_spacing = 72  # 56 (FAB height) + 16 (margin)

        for i, action in enumerate(self.actions):
            # Create action item
            item = self._create_action_item(action, i)

            # Position above main FAB
            # Reverse order so first action is closest to FAB
            index = len(self.actions) - i - 1
            bottom_offset = item_spacing * (index + 1)

            # Wrap in positioned container
            positioned_item = ft.Container(
                content=item,
                right=0,
                bottom=bottom_offset,
                opacity=0,
                scale=0.8,
                animate_opacity=Animations.fade_in(AnimationDuration.NORMAL.value),
                animate_scale=Animations.scale_in(),
            )

            items.append(positioned_item)

        return items

    def _create_action_item(self, action: SpeedDialAction, index: int) -> ft.Container:
        """Create a single action item."""
        # Mini-FAB button
        fab_color = action.color or Colors.NEUTRAL_0
        icon_color = action.icon_color or Colors.NEUTRAL_700

        mini_fab = ft.Container(
            content=ft.Icon(
                action.icon,
                color=icon_color,
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
                size=14,
                weight=ft.FontWeight.W_500,
                color=Colors.NEUTRAL_900,
            ),
            bgcolor=Colors.NEUTRAL_0,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=Radius.MD,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color="rgba(0, 0, 0, 0.15)",
                offset=ft.Offset(0, 2),
            ),
        )

        # Row with label on left, FAB on right
        return ft.Row(
            [label, mini_fab],
            spacing=12,
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _toggle(self, e):
        """Toggle speed dial expansion."""
        if self.is_expanded:
            self._collapse(e)
        else:
            self._expand(e)

    def _expand(self, e):
        """Expand speed dial to show action items."""
        if self.is_expanded:
            return

        self.is_expanded = True

        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        # Rotate main FAB icon (+ becomes ×)
        self.fab_icon.name = ft.Icons.CLOSE
        self.main_fab.content.rotate = 0.125  # 45 degrees

        # Show backdrop
        self.backdrop.opacity = 1
        self.backdrop.update()

        # Animate items in with stagger
        # Items appear from bottom to top
        for i, item in enumerate(reversed(self.action_items)):
            # Stagger delay
            def animate_item(it=item, delay=i):
                import time
                if delay > 0:
                    time.sleep(delay * 0.05)  # 50ms stagger

                it.opacity = 1
                it.scale = 1.0

                if self.page:
                    it.update()

            # Run in thread for stagger
            import threading
            threading.Thread(target=animate_item, daemon=True).start()

        self.update()

    def _collapse(self, e=None):
        """Collapse speed dial to hide action items."""
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
        self.backdrop.update()

        # Hide all action items
        for item in self.action_items:
            item.opacity = 0
            item.scale = 0.8
            item.update()

        self.update()

    def _handle_action_click(self, action: SpeedDialAction):
        """Handle action item click."""
        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.light()

        # Collapse speed dial
        self._collapse()

        # Call action handler
        if action.on_click:
            action.on_click()


class CompactSpeedDial(ft.Container):
    """
    Compact speed dial with minimal design.
    Actions appear in a simple vertical list without labels.

    Usage:
        speed_dial = CompactSpeedDial(
            actions=[
                SpeedDialAction(
                    icon=ft.Icons.PERSON_ADD,
                    label="Add Patient",  # Shows as tooltip
                    on_click=handle_add,
                ),
            ],
            page=page,
        )
    """

    def __init__(
        self,
        actions: List[SpeedDialAction],
        page: ft.Page,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.actions = actions
        self.page = page
        self.haptic_feedback = haptic_feedback
        self.is_expanded = False

        # Create main FAB
        self.main_fab_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=Colors.PRIMARY_500,
            on_click=self._toggle,
        )

        # Create action buttons
        self.action_buttons = []
        for action in actions:
            btn = ft.FloatingActionButton(
                icon=action.icon,
                mini=True,
                bgcolor=action.color or Colors.NEUTRAL_0,
                tooltip=action.label,
                on_click=lambda e, a=action: self._handle_action_click(a),
            )
            self.action_buttons.append(btn)

        # Column to hold buttons
        self.button_column = ft.Column(
            [*self.action_buttons, self.main_fab_button],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.END,
        )

        super().__init__(
            content=self.button_column,
        )

    def _toggle(self, e):
        """Toggle expansion."""
        if self.is_expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        """Show action buttons."""
        self.is_expanded = True

        if self.haptic_feedback:
            self.haptic_feedback.medium()

        self.main_fab_button.icon = ft.Icons.CLOSE

        # Show all action buttons
        for btn in self.action_buttons:
            btn.visible = True

        self.update()

    def _collapse(self):
        """Hide action buttons."""
        self.is_expanded = False

        if self.haptic_feedback:
            self.haptic_feedback.light()

        self.main_fab_button.icon = ft.Icons.ADD

        # Hide all action buttons
        for btn in self.action_buttons:
            btn.visible = False

        self.update()

    def _handle_action_click(self, action: SpeedDialAction):
        """Handle action click."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        self._collapse()

        if action.on_click:
            action.on_click()


__all__ = [
    'SpeedDial',
    'CompactSpeedDial',
    'SpeedDialAction',
]
