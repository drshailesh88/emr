"""Search Bar Component - Patient search input."""

import flet as ft
from typing import Optional, Callable
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius


class SearchBar(ft.Container):
    """Search bar with debounced input."""

    def __init__(
        self,
        hint_text: str = "Search patients...",
        on_search: Optional[Callable[[str], None]] = None,
        on_clear: Optional[Callable] = None,
    ):
        self.on_search = on_search
        self.on_clear = on_clear

        self.text_field = ft.TextField(
            hint_text=hint_text,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=Radius.FULL,
            height=48,
            bgcolor=Colors.NEUTRAL_0,
            border_color=Colors.NEUTRAL_200,
            focused_border_color=Colors.PRIMARY_500,
            text_size=MobileTypography.BODY_MEDIUM,
            on_change=self._on_change,
            suffix=ft.IconButton(
                icon=ft.Icons.CLEAR,
                icon_size=18,
                icon_color=Colors.NEUTRAL_400,
                on_click=self._on_clear_click,
                visible=False,
            ),
        )

        super().__init__(
            content=self.text_field,
            padding=MobileSpacing.SCREEN_PADDING,
        )

    def _on_change(self, e):
        """Handle text change with debounce."""
        value = e.control.value
        # Show/hide clear button
        e.control.suffix.visible = bool(value)
        e.control.update()

        # Trigger search callback
        if self.on_search:
            self.on_search(value)

    def _on_clear_click(self, e):
        """Handle clear button click."""
        self.text_field.value = ""
        self.text_field.suffix.visible = False
        self.text_field.update()

        if self.on_clear:
            self.on_clear()

    def set_value(self, value: str):
        """Set search value programmatically."""
        self.text_field.value = value
        self.text_field.suffix.visible = bool(value)
        self.text_field.update()

    def clear(self):
        """Clear the search bar."""
        self.set_value("")
