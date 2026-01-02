"""Drug autocomplete component for prescription form."""

import flet as ft
from typing import Callable, Optional


class DrugAutocomplete(ft.UserControl):
    """Drug autocomplete field with dropdown suggestions."""

    def __init__(
        self,
        db_service,
        on_select: Callable[[dict], None],
        label: str = "Drug Name",
        width: int = 400
    ):
        super().__init__()
        self.db = db_service
        self.on_select = on_select
        self.label = label
        self.width = width
        self.search_field: Optional[ft.TextField] = None
        self.dropdown_container: Optional[ft.Container] = None
        self.suggestions_column: Optional[ft.Column] = None
        self.is_dropdown_visible = False

    def build(self):
        """Build the autocomplete UI."""
        # Search field
        self.search_field = ft.TextField(
            label=self.label,
            hint_text="Type to search drugs...",
            width=self.width,
            on_change=self._on_search_change,
            on_focus=self._on_focus,
            on_blur=self._on_blur,
            border_radius=8,
        )

        # Suggestions dropdown
        self.suggestions_column = ft.Column(
            [],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        self.dropdown_container = ft.Container(
            content=self.suggestions_column,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            padding=5,
            width=self.width,
            max_height=300,
            visible=False,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

        return ft.Column([
            self.search_field,
            self.dropdown_container,
        ], spacing=2)

    def _on_search_change(self, e):
        """Handle search field changes."""
        query = self.search_field.value.strip()

        if len(query) < 2:
            self._hide_dropdown()
            return

        # Search drugs
        results = self.db.search_drugs(query, limit=10)

        if not results:
            self._hide_dropdown()
            return

        # Update suggestions
        self.suggestions_column.controls.clear()

        for drug in results:
            self.suggestions_column.controls.append(
                self._create_suggestion_item(drug)
            )

        self._show_dropdown()

    def _create_suggestion_item(self, drug: dict) -> ft.Control:
        """Create a suggestion item for the dropdown."""
        # Drug name and strength
        drug_name = drug.get('generic_name', '')
        strengths = drug.get('strengths', [])
        strength_text = f" ({', '.join(strengths)})" if strengths else ""

        # Brand names
        brands = drug.get('brand_names', [])
        brand_text = f"  {', '.join(brands[:3])}" if brands else ""
        if len(brands) > 3:
            brand_text += "..."

        # Usage count
        usage_count = drug.get('usage_count', 0)
        usage_text = f" - used {usage_count}x" if usage_count > 0 else ""

        # Forms
        forms = drug.get('forms', [])
        form_text = f" [{', '.join(forms)}]" if forms else ""

        # Create item
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        f"{drug_name}{strength_text}",
                        size=13,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        form_text,
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                ], spacing=5),
                ft.Text(
                    f"{brand_text}{usage_text}",
                    size=11,
                    color=ft.Colors.GREY_600,
                    italic=True,
                ),
            ], spacing=2),
            padding=10,
            on_click=lambda e, d=drug: self._on_drug_select(d),
            on_hover=lambda e: self._on_item_hover(e),
            border_radius=5,
        )

    def _on_item_hover(self, e):
        """Handle hover on suggestion item."""
        if e.data == "true":
            e.control.bgcolor = ft.Colors.GREY_100
        else:
            e.control.bgcolor = None
        e.control.update()

    def _on_drug_select(self, drug: dict):
        """Handle drug selection."""
        # Fill search field with drug name
        self.search_field.value = drug.get('generic_name', '')
        self.search_field.update()

        # Hide dropdown
        self._hide_dropdown()

        # Call callback
        if self.on_select:
            self.on_select(drug)

        # Increment usage count
        drug_id = drug.get('id')
        if drug_id:
            self.db.increment_drug_usage(drug_id)

    def _on_focus(self, e):
        """Handle focus on search field."""
        if self.search_field.value and len(self.search_field.value) >= 2:
            self._on_search_change(e)

    def _on_blur(self, e):
        """Handle blur on search field."""
        # Delay hiding to allow click on suggestion
        # Note: In real implementation, we might need more sophisticated handling
        pass

    def _show_dropdown(self):
        """Show the dropdown."""
        self.dropdown_container.visible = True
        self.is_dropdown_visible = True
        if self.dropdown_container.page:
            self.dropdown_container.update()

    def _hide_dropdown(self):
        """Hide the dropdown."""
        self.dropdown_container.visible = False
        self.is_dropdown_visible = False
        if self.dropdown_container.page:
            self.dropdown_container.update()

    def clear(self):
        """Clear the search field."""
        self.search_field.value = ""
        self._hide_dropdown()
        if self.search_field.page:
            self.search_field.update()

    def set_value(self, value: str):
        """Set the search field value."""
        self.search_field.value = value
        if self.search_field.page:
            self.search_field.update()

    def get_value(self) -> str:
        """Get the search field value."""
        return self.search_field.value or ""
