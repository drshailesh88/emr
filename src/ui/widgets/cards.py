"""
Premium Card Components for DocAssist EMR

Usage:
    from src.ui.widgets import PatientCard, PremiumCard

    card = PatientCard(
        patient=patient,
        selected=True,
        on_click=handle_select,
    )
"""

import flet as ft
from typing import Optional, Callable, List, Any

from ..tokens import Colors, Typography, Spacing, Radius, Shadows, Motion


class PremiumCard(ft.Container):
    """
    Base premium card component with subtle shadow and hover effects.

    Use as a container for grouped content.
    """

    def __init__(
        self,
        content: ft.Control,
        selected: bool = False,
        elevated: bool = True,
        on_click: Optional[Callable] = None,
        padding: int = Spacing.CARD_PADDING,
        margin: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        expand: bool = False,
        **kwargs
    ):
        self._selected = selected
        self._elevated = elevated

        super().__init__(
            content=content,
            padding=padding,
            margin=margin,
            width=width,
            height=height,
            expand=expand,
            border_radius=Radius.CARD,
            bgcolor=self._get_bgcolor(),
            border=self._get_border(),
            shadow=self._get_shadow() if elevated else None,
            on_click=on_click,
            on_hover=self._on_hover if on_click else None,
            animate=ft.animation.Animation(Motion.FAST, ft.AnimationCurve.EASE_OUT),
            **kwargs
        )

    def _get_bgcolor(self) -> str:
        if self._selected:
            return Colors.PRIMARY_50
        return Colors.NEUTRAL_0

    def _get_border(self) -> ft.Border:
        if self._selected:
            return ft.border.all(2, Colors.PRIMARY_500)
        return ft.border.all(1, Colors.NEUTRAL_200)

    def _get_shadow(self) -> ft.BoxShadow:
        shadow_def = Shadows.CARD_HOVER if self._selected else Shadows.CARD
        return shadow_def.to_flet_shadow()

    def _on_hover(self, e):
        """Handle hover state for interactive cards."""
        if e.data == "true":
            self.bgcolor = Colors.NEUTRAL_50 if not self._selected else Colors.PRIMARY_100
            self.shadow = Shadows.CARD_HOVER.to_flet_shadow()
        else:
            self.bgcolor = self._get_bgcolor()
            self.shadow = self._get_shadow() if self._elevated else None
        self.update()


class SelectableCard(ft.Container):
    """
    Card that can be selected with visual feedback.

    Use for list items that can be selected.
    """

    def __init__(
        self,
        content: ft.Control,
        selected: bool = False,
        on_click: Optional[Callable] = None,
        on_long_press: Optional[Callable] = None,
        padding: int = Spacing.SM,
        **kwargs
    ):
        self.is_selected = selected
        self._on_select = on_click

        super().__init__(
            content=content,
            padding=padding,
            border_radius=Radius.MD,
            bgcolor=self._get_bgcolor(),
            border=self._get_border(),
            on_click=self._handle_click,
            on_long_press=on_long_press,
            on_hover=self._on_hover,
            animate=ft.animation.Animation(Motion.FAST, ft.AnimationCurve.EASE_OUT),
            **kwargs
        )

    def _get_bgcolor(self) -> str:
        if self.is_selected:
            return Colors.PRIMARY_50
        return Colors.NEUTRAL_0

    def _get_border(self) -> ft.Border:
        if self.is_selected:
            return ft.border.all(2, Colors.PRIMARY_500)
        return ft.border.all(1, Colors.NEUTRAL_200)

    def _handle_click(self, e):
        if self._on_select:
            self._on_select(e)

    def _on_hover(self, e):
        if e.data == "true" and not self.is_selected:
            self.bgcolor = Colors.NEUTRAL_50
        else:
            self.bgcolor = self._get_bgcolor()
        self.update()

    def set_selected(self, selected: bool):
        """Update selection state."""
        self.is_selected = selected
        self.bgcolor = self._get_bgcolor()
        self.border = self._get_border()
        self.update()


class PatientCard(ft.Container):
    """
    Premium patient list item card.

    Shows patient name, UHID, and basic demographics.
    Supports selection state with visual feedback.
    """

    def __init__(
        self,
        name: str,
        uhid: str,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        last_visit: Optional[str] = None,
        selected: bool = False,
        on_click: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        **kwargs
    ):
        self.is_selected = selected
        self._on_select = on_click

        # Build demographics line
        demographics = []
        if age:
            demographics.append(f"{age}y")
        if gender:
            demographics.append(gender)
        demo_text = " · ".join(demographics) if demographics else ""

        # Avatar with initials
        initials = "".join([part[0].upper() for part in name.split()[:2]])
        avatar = ft.Container(
            content=ft.Text(
                initials,
                size=Typography.LABEL_MEDIUM.size,
                weight=ft.FontWeight.W_600,
                color=Colors.PRIMARY_700,
            ),
            width=36,
            height=36,
            border_radius=Radius.FULL,
            bgcolor=Colors.PRIMARY_100,
            alignment=ft.alignment.center,
        )

        # Content
        content_column = ft.Column(
            [
                ft.Text(
                    name,
                    size=Typography.BODY_MEDIUM.size,
                    weight=ft.FontWeight.W_500,
                    color=Colors.NEUTRAL_900,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    max_lines=1,
                ),
                ft.Text(
                    f"{uhid} · {demo_text}" if demo_text else uhid,
                    size=Typography.BODY_SMALL.size,
                    color=Colors.NEUTRAL_500,
                ),
            ],
            spacing=2,
            expand=True,
        )

        # Main row
        main_row = ft.Row(
            [
                avatar,
                content_column,
            ],
            spacing=Spacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=main_row,
            padding=Spacing.SM,
            border_radius=Radius.MD,
            bgcolor=self._get_bgcolor(),
            border=self._get_border(),
            on_click=self._handle_click,
            on_hover=self._on_hover,
            animate=ft.animation.Animation(Motion.FAST, ft.AnimationCurve.EASE_OUT),
            **kwargs
        )

    def _get_bgcolor(self) -> str:
        if self.is_selected:
            return Colors.PRIMARY_50
        return Colors.NEUTRAL_0

    def _get_border(self) -> ft.Border:
        if self.is_selected:
            return ft.border.all(2, Colors.PRIMARY_500)
        return ft.border.all(1, Colors.NEUTRAL_100)

    def _handle_click(self, e):
        if self._on_select:
            self._on_select(e)

    def _on_hover(self, e):
        if e.data == "true" and not self.is_selected:
            self.bgcolor = Colors.NEUTRAL_50
            self.border = ft.border.all(1, Colors.NEUTRAL_200)
        else:
            self.bgcolor = self._get_bgcolor()
            self.border = self._get_border()
        self.update()

    def set_selected(self, selected: bool):
        """Update selection state."""
        self.is_selected = selected
        self.bgcolor = self._get_bgcolor()
        self.border = self._get_border()
        self.update()


class InfoCard(ft.Container):
    """
    Premium information display card.

    Use for displaying read-only information with an icon.
    """

    def __init__(
        self,
        title: str,
        value: str,
        icon: Optional[str] = None,
        icon_color: str = Colors.PRIMARY_500,
        subtitle: Optional[str] = None,
        **kwargs
    ):
        # Icon
        icon_widget = None
        if icon:
            icon_widget = ft.Container(
                content=ft.Icon(icon, color=icon_color, size=20),
                width=40,
                height=40,
                border_radius=Radius.SM,
                bgcolor=f"{icon_color}15",  # 15% opacity
                alignment=ft.alignment.center,
            )

        # Content
        content_items = [
            ft.Text(
                title,
                size=Typography.BODY_SMALL.size,
                color=Colors.NEUTRAL_500,
            ),
            ft.Text(
                value,
                size=Typography.TITLE_MEDIUM.size,
                weight=ft.FontWeight.W_600,
                color=Colors.NEUTRAL_900,
            ),
        ]

        if subtitle:
            content_items.append(
                ft.Text(
                    subtitle,
                    size=Typography.BODY_SMALL.size,
                    color=Colors.NEUTRAL_400,
                )
            )

        content_column = ft.Column(content_items, spacing=2)

        # Main layout
        if icon_widget:
            main_content = ft.Row(
                [icon_widget, content_column],
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            main_content = content_column

        super().__init__(
            content=main_content,
            padding=Spacing.MD,
            border_radius=Radius.CARD,
            bgcolor=Colors.NEUTRAL_0,
            border=ft.border.all(1, Colors.NEUTRAL_200),
            **kwargs
        )
