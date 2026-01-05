"""Premium Text Field Components.

Styled input fields with floating labels, focus states, and animations.
"""

import flet as ft
from typing import Optional, Callable, Any

from ..tokens import Colors, Typography, Spacing, Radius, Motion


class PremiumTextField(ft.TextField):
    """Premium styled text field with consistent design tokens."""

    def __init__(
        self,
        label: str = "",
        hint_text: str = "",
        prefix_icon: Optional[ft.Icons] = None,
        suffix_icon: Optional[ft.Icons] = None,
        on_change: Optional[Callable] = None,
        on_submit: Optional[Callable] = None,
        password: bool = False,
        multiline: bool = False,
        min_lines: int = 1,
        max_lines: int = 1,
        read_only: bool = False,
        disabled: bool = False,
        expand: bool = False,
        width: Optional[int] = None,
        is_dark: bool = False,
        **kwargs
    ):
        # Build prefix/suffix icons
        prefix = ft.Icon(
            prefix_icon,
            size=20,
            color=Colors.NEUTRAL_500 if not is_dark else Colors.NEUTRAL_400
        ) if prefix_icon else None

        suffix = ft.Icon(
            suffix_icon,
            size=20,
            color=Colors.NEUTRAL_500 if not is_dark else Colors.NEUTRAL_400
        ) if suffix_icon else None

        super().__init__(
            label=label,
            hint_text=hint_text,
            prefix_icon=prefix_icon,
            suffix_icon=suffix_icon,
            password=password,
            can_reveal_password=password,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            read_only=read_only,
            disabled=disabled,
            expand=expand,
            width=width,
            on_change=on_change,
            on_submit=on_submit,
            # Styling
            text_size=Typography.BODY_MEDIUM.size,
            label_style=ft.TextStyle(
                size=Typography.LABEL_MEDIUM.size,
                color=Colors.NEUTRAL_600 if not is_dark else Colors.NEUTRAL_400,
            ),
            hint_style=ft.TextStyle(
                size=Typography.BODY_MEDIUM.size,
                color=Colors.NEUTRAL_400 if not is_dark else Colors.NEUTRAL_500,
            ),
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300 if not is_dark else Colors.NEUTRAL_600,
            focused_border_color=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_300,
            focused_border_width=2,
            cursor_color=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_300,
            selection_color=Colors.SELECTED_OVERLAY,
            content_padding=ft.padding.symmetric(
                horizontal=Spacing.INPUT_PADDING,
                vertical=Spacing.INPUT_PADDING
            ),
            **kwargs
        )


class PremiumSearchField(ft.TextField):
    """Premium search field with rounded design and search icon."""

    def __init__(
        self,
        hint_text: str = "Search...",
        on_change: Optional[Callable] = None,
        on_submit: Optional[Callable] = None,
        expand: bool = True,
        is_dark: bool = False,
        **kwargs
    ):
        super().__init__(
            hint_text=hint_text,
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_change,
            on_submit=on_submit,
            expand=expand,
            # Styling
            text_size=Typography.BODY_MEDIUM.size,
            hint_style=ft.TextStyle(
                size=Typography.BODY_MEDIUM.size,
                color=Colors.NEUTRAL_400 if not is_dark else Colors.NEUTRAL_500,
            ),
            border_radius=Radius.FULL,
            border_color=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_700,
            focused_border_color=Colors.PRIMARY_400 if not is_dark else Colors.PRIMARY_400,
            focused_border_width=2,
            cursor_color=Colors.PRIMARY_500,
            bgcolor=Colors.NEUTRAL_50 if not is_dark else Colors.NEUTRAL_800,
            content_padding=ft.padding.only(
                left=Spacing.XS,
                right=Spacing.MD,
                top=Spacing.SM,
                bottom=Spacing.SM
            ),
            **kwargs
        )


class PremiumTextArea(ft.TextField):
    """Premium multi-line text area with auto-resize feel."""

    def __init__(
        self,
        label: str = "",
        hint_text: str = "",
        on_change: Optional[Callable] = None,
        min_lines: int = 3,
        max_lines: int = 8,
        expand: bool = False,
        is_dark: bool = False,
        **kwargs
    ):
        super().__init__(
            label=label,
            hint_text=hint_text,
            multiline=True,
            min_lines=min_lines,
            max_lines=max_lines,
            expand=expand,
            on_change=on_change,
            # Styling
            text_size=Typography.BODY_MEDIUM.size,
            label_style=ft.TextStyle(
                size=Typography.LABEL_MEDIUM.size,
                color=Colors.NEUTRAL_600 if not is_dark else Colors.NEUTRAL_400,
            ),
            hint_style=ft.TextStyle(
                size=Typography.BODY_SMALL.size,
                color=Colors.NEUTRAL_400 if not is_dark else Colors.NEUTRAL_500,
            ),
            border_radius=Radius.INPUT,
            border_color=Colors.NEUTRAL_300 if not is_dark else Colors.NEUTRAL_600,
            focused_border_color=Colors.PRIMARY_500 if not is_dark else Colors.PRIMARY_300,
            focused_border_width=2,
            cursor_color=Colors.PRIMARY_500,
            content_padding=ft.padding.all(Spacing.INPUT_PADDING),
            **kwargs
        )


class ChatInputField(ft.TextField):
    """Premium chat input field with pill shape and send affordance."""

    def __init__(
        self,
        hint_text: str = "Type a message...",
        on_submit: Optional[Callable] = None,
        on_change: Optional[Callable] = None,
        expand: bool = True,
        is_dark: bool = False,
        **kwargs
    ):
        super().__init__(
            hint_text=hint_text,
            on_submit=on_submit,
            on_change=on_change,
            expand=expand,
            multiline=True,
            min_lines=1,
            max_lines=4,
            shift_enter=True,  # Enter sends, Shift+Enter for newline
            # Styling
            text_size=Typography.BODY_MEDIUM.size,
            hint_style=ft.TextStyle(
                size=Typography.BODY_MEDIUM.size,
                color=Colors.NEUTRAL_400 if not is_dark else Colors.NEUTRAL_500,
            ),
            border_radius=Radius.XXL,
            border_color=Colors.NEUTRAL_200 if not is_dark else Colors.NEUTRAL_600,
            focused_border_color=Colors.PRIMARY_400,
            focused_border_width=2,
            cursor_color=Colors.PRIMARY_500,
            bgcolor=Colors.NEUTRAL_0 if not is_dark else Colors.NEUTRAL_800,
            content_padding=ft.padding.symmetric(
                horizontal=Spacing.MD,
                vertical=Spacing.SM
            ),
            **kwargs
        )
