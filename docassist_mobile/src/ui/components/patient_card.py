"""Patient Card Component - Displays patient info in a list."""

import flet as ft
from typing import Optional, Callable
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations


class PatientCard(ft.Container):
    """Patient list item card with avatar, name, and demographics."""

    def __init__(
        self,
        name: str,
        age: Optional[int] = None,
        gender: str = "O",
        phone: Optional[str] = None,
        last_visit: Optional[str] = None,
        on_click: Optional[Callable] = None,
        selected: bool = False,
        haptic_feedback=None,
    ):
        # Generate initials
        initials = "".join([n[0] for n in name.split()[:2]]).upper()

        # Demographics text
        demo_parts = []
        if gender:
            demo_parts.append(gender)
        if age:
            demo_parts.append(f"{age}y")
        demographics = ", ".join(demo_parts) if demo_parts else ""

        # Build content
        content = ft.Row(
            [
                # Avatar
                ft.Container(
                    content=ft.Text(
                        initials,
                        size=MobileTypography.BODY_MEDIUM,
                        weight=ft.FontWeight.W_600,
                        color=Colors.PRIMARY_500,
                    ),
                    width=48,
                    height=48,
                    border_radius=Radius.FULL,
                    bgcolor=Colors.PRIMARY_50,
                    alignment=ft.alignment.center,
                ),
                # Info
                ft.Column(
                    [
                        ft.Text(
                            name,
                            size=MobileTypography.BODY_LARGE,
                            weight=ft.FontWeight.W_500,
                            color=Colors.NEUTRAL_900,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    demographics,
                                    size=MobileTypography.BODY_SMALL,
                                    color=Colors.NEUTRAL_600,
                                ),
                                ft.Text("•", size=10, color=Colors.NEUTRAL_400) if last_visit else ft.Container(),
                                ft.Text(
                                    last_visit or "",
                                    size=MobileTypography.BODY_SMALL,
                                    color=Colors.NEUTRAL_500,
                                ),
                            ],
                            spacing=MobileSpacing.XS,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                # Chevron
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=Colors.NEUTRAL_400),
            ],
            spacing=MobileSpacing.MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Store haptic feedback for click handler
        self.haptic_feedback = haptic_feedback
        self._original_on_click = on_click

        super().__init__(
            content=content,
            bgcolor=Colors.PRIMARY_50 if selected else Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            border=ft.border.all(2, Colors.PRIMARY_500) if selected else None,
            ink=True,
            on_click=self._handle_click if on_click else None,
            # Add tap animation
            animate_scale=Animations.scale_tap(),
            scale=1.0,
        )

    def _handle_click(self, e):
        """Handle click with haptic feedback and animation."""
        # Trigger haptic
        if self.haptic_feedback:
            self.haptic_feedback.light()

        # Scale animation
        self.scale = 0.97
        self.update()

        # Call original handler
        if self._original_on_click:
            self._original_on_click(e)

        # Scale back
        self.scale = 1.0
        self.update()
