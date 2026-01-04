"""Micro-interaction Components.

Loading skeletons, feedback animations, and transition effects.
"""

import flet as ft
from typing import Optional

from ..tokens import Colors, Typography, Spacing, Radius, Motion


class SkeletonLoader(ft.Container):
    """Animated skeleton placeholder for loading states."""

    def __init__(
        self,
        width: Optional[int] = None,
        height: int = 16,
        border_radius: int = Radius.SM,
        is_dark: bool = False,
    ):
        super().__init__(
            width=width,
            height=height,
            border_radius=border_radius,
            bgcolor=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700,
            animate=ft.Animation(Motion.SLOW, ft.AnimationCurve.EASE_IN_OUT),
        )


class SkeletonText(ft.Column):
    """Multi-line skeleton text placeholder."""

    def __init__(
        self,
        lines: int = 3,
        line_height: int = 14,
        spacing: int = Spacing.XS,
        is_dark: bool = False,
    ):
        controls = []
        for i in range(lines):
            # Last line is shorter
            width_percent = 0.6 if i == lines - 1 else (0.9 if i % 2 == 0 else 1.0)
            controls.append(
                ft.Container(
                    height=line_height,
                    border_radius=Radius.XS,
                    bgcolor=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700,
                    expand=True if width_percent == 1.0 else False,
                    width=None,
                )
            )

        super().__init__(
            controls=controls,
            spacing=spacing,
        )


class SkeletonCard(ft.Container):
    """Skeleton placeholder for card content."""

    def __init__(
        self,
        show_avatar: bool = True,
        show_title: bool = True,
        show_subtitle: bool = True,
        show_body: bool = False,
        is_dark: bool = False,
    ):
        content_items = []

        # Header with avatar
        if show_avatar or show_title:
            header_items = []
            if show_avatar:
                header_items.append(
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=Radius.AVATAR,
                        bgcolor=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700,
                    )
                )
            if show_title:
                header_items.append(
                    ft.Column([
                        ft.Container(
                            width=120,
                            height=14,
                            border_radius=Radius.XS,
                            bgcolor=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700,
                        ),
                        ft.Container(
                            width=80,
                            height=10,
                            border_radius=Radius.XS,
                            bgcolor=Colors.NEUTRAL_150 if not is_dark else Colors.NEUTRAL_800,
                        ) if show_subtitle else ft.Container(),
                    ], spacing=Spacing.XXS)
                )
            content_items.append(ft.Row(header_items, spacing=Spacing.SM))

        # Body text
        if show_body:
            content_items.append(
                ft.Column([
                    ft.Container(
                        height=12,
                        border_radius=Radius.XS,
                        bgcolor=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700,
                        expand=True,
                    ),
                    ft.Container(
                        height=12,
                        border_radius=Radius.XS,
                        bgcolor=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700,
                        expand=True,
                    ),
                    ft.Container(
                        width=150,
                        height=12,
                        border_radius=Radius.XS,
                        bgcolor=Colors.NEUTRAL_150 if not is_dark else Colors.NEUTRAL_800,
                    ),
                ], spacing=Spacing.XS)
            )

        super().__init__(
            content=ft.Column(content_items, spacing=Spacing.MD),
            padding=Spacing.MD,
            border_radius=Radius.CARD,
            bgcolor=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_900,
            border=ft.border.all(1, Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700),
        )


class LoadingOverlay(ft.Container):
    """Semi-transparent loading overlay with spinner."""

    def __init__(
        self,
        message: str = "Loading...",
        visible: bool = True,
        is_dark: bool = False,
    ):
        super().__init__(
            content=ft.Column([
                ft.ProgressRing(
                    width=40,
                    height=40,
                    stroke_width=3,
                    color=Colors.PRIMARY_500,
                ),
                ft.Text(
                    message,
                    size=Typography.BODY_MEDIUM.size,
                    color=Colors.NEUTRAL_700 if not is_dark else Colors.NEUTRAL_300,
                ),
            ], spacing=Spacing.MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            bgcolor="rgba(255, 255, 255, 0.9)" if not is_dark else "rgba(18, 18, 18, 0.9)",
            visible=visible,
            expand=True,
        )


class SuccessFeedback(ft.Container):
    """Animated success feedback indicator."""

    def __init__(
        self,
        message: str = "Success!",
        on_dismiss: Optional[callable] = None,
        auto_dismiss: bool = True,
        is_dark: bool = False,
    ):
        super().__init__(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.CHECK_CIRCLE_ROUNDED,
                        color=Colors.SUCCESS_MAIN,
                        size=20,
                    ),
                    width=32,
                    height=32,
                    bgcolor=Colors.SUCCESS_LIGHT,
                    border_radius=Radius.FULL,
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    message,
                    size=Typography.BODY_MEDIUM.size,
                    weight=ft.FontWeight.W_500,
                    color=Colors.SUCCESS_DARK,
                ),
            ], spacing=Spacing.SM),
            padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            bgcolor=Colors.SUCCESS_LIGHT,
            border_radius=Radius.MD,
            border=ft.border.all(1, Colors.SUCCESS_MAIN),
            animate=ft.Animation(Motion.NORMAL, ft.AnimationCurve.EASE_OUT),
            animate_opacity=ft.Animation(Motion.NORMAL, ft.AnimationCurve.EASE_OUT),
        )


class ErrorFeedback(ft.Container):
    """Animated error feedback indicator."""

    def __init__(
        self,
        message: str = "Error occurred",
        on_dismiss: Optional[callable] = None,
        is_dark: bool = False,
    ):
        super().__init__(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.ERROR_ROUNDED,
                        color=Colors.ERROR_MAIN,
                        size=20,
                    ),
                    width=32,
                    height=32,
                    bgcolor=Colors.ERROR_LIGHT,
                    border_radius=Radius.FULL,
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    message,
                    size=Typography.BODY_MEDIUM.size,
                    weight=ft.FontWeight.W_500,
                    color=Colors.ERROR_DARK,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    icon_color=Colors.ERROR_MAIN,
                    on_click=on_dismiss,
                ) if on_dismiss else ft.Container(),
            ], spacing=Spacing.SM),
            padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            bgcolor=Colors.ERROR_LIGHT,
            border_radius=Radius.MD,
            border=ft.border.all(1, Colors.ERROR_MAIN),
            animate=ft.Animation(Motion.NORMAL, ft.AnimationCurve.EASE_OUT),
        )


class InfoBanner(ft.Container):
    """Informational banner with icon."""

    def __init__(
        self,
        message: str,
        icon: ft.Icons = ft.Icons.INFO_OUTLINE,
        dismissible: bool = True,
        on_dismiss: Optional[callable] = None,
        is_dark: bool = False,
    ):
        super().__init__(
            content=ft.Row([
                ft.Icon(icon, color=Colors.INFO_MAIN, size=20),
                ft.Text(
                    message,
                    size=Typography.BODY_SMALL.size,
                    color=Colors.INFO_DARK if not is_dark else Colors.INFO_MAIN,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    icon_color=Colors.INFO_MAIN,
                    on_click=on_dismiss,
                ) if dismissible and on_dismiss else ft.Container(),
            ], spacing=Spacing.SM),
            padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            bgcolor=Colors.INFO_LIGHT if not is_dark else "rgba(66, 133, 244, 0.15)",
            border_radius=Radius.MD,
            border=ft.border.all(1, Colors.INFO_MAIN),
        )


class PulsingDot(ft.Container):
    """Animated pulsing dot indicator."""

    def __init__(
        self,
        color: str = Colors.SUCCESS_MAIN,
        size: int = 8,
    ):
        super().__init__(
            width=size,
            height=size,
            border_radius=Radius.FULL,
            bgcolor=color,
            animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
        )


class AnimatedCounter(ft.Text):
    """Counter with animation for number changes."""

    def __init__(
        self,
        value: int = 0,
        prefix: str = "",
        suffix: str = "",
        size: int = Typography.HEADLINE_MEDIUM.size,
        color: str = Colors.NEUTRAL_900,
        weight: ft.FontWeight = ft.FontWeight.W_600,
    ):
        self._value = value
        self._prefix = prefix
        self._suffix = suffix

        super().__init__(
            f"{prefix}{value}{suffix}",
            size=size,
            color=color,
            weight=weight,
            animate_opacity=ft.Animation(Motion.FAST, ft.AnimationCurve.EASE_OUT),
        )

    def update_value(self, new_value: int):
        """Update counter value with animation."""
        self._value = new_value
        self.value = f"{self._prefix}{new_value}{self._suffix}"
        if self.page:
            self.update()


class ProgressIndicator(ft.Container):
    """Premium styled progress indicator."""

    def __init__(
        self,
        value: float = 0,  # 0 to 1
        height: int = 4,
        show_percentage: bool = False,
        color: str = Colors.PRIMARY_500,
        bg_color: str = Colors.NEUTRAL_200,
        is_dark: bool = False,
    ):
        self._value = value
        self._show_percentage = show_percentage

        progress_bar = ft.Container(
            width=f"{int(value * 100)}%",
            height=height,
            bgcolor=color,
            border_radius=Radius.FULL,
            animate=ft.Animation(Motion.NORMAL, ft.AnimationCurve.EASE_OUT),
        )

        content = ft.Stack([
            ft.Container(
                height=height,
                bgcolor=bg_color if not is_dark else Colors.NEUTRAL_700,
                border_radius=Radius.FULL,
                expand=True,
            ),
            progress_bar,
        ], expand=True)

        if show_percentage:
            content = ft.Row([
                ft.Container(content=content, expand=True),
                ft.Text(
                    f"{int(value * 100)}%",
                    size=Typography.LABEL_SMALL.size,
                    color=Colors.NEUTRAL_600 if not is_dark else Colors.NEUTRAL_400,
                    width=40,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ], spacing=Spacing.SM)

        super().__init__(content=content, expand=True)

    def set_progress(self, value: float):
        """Update progress value."""
        self._value = max(0, min(1, value))
        # Would need to rebuild to animate - simplified version
        if self.page:
            self.update()
