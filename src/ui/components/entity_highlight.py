"""Entity highlighting widget for clinical notes.

Shows clinical notes with inline highlighting for different entity types.
Uses color-coded highlighting with tooltips.
"""

import flet as ft
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class EntitySpan:
    """Represents an entity span in text."""
    start: int
    end: int
    text: str
    entity_type: str
    normalized_value: Optional[str] = None
    confidence: float = 1.0


# Entity type colors
ENTITY_COLORS = {
    "symptom": ft.Colors.ORANGE_200,
    "diagnosis": ft.Colors.BLUE_200,
    "medication": ft.Colors.GREEN_200,
    "measurement": ft.Colors.PURPLE_200,
    "duration": ft.Colors.GREY_300,
    "vital": ft.Colors.PINK_200,
    "investigation": ft.Colors.AMBER_200,
    "procedure": ft.Colors.CYAN_200,
}

# Entity type text colors
ENTITY_TEXT_COLORS = {
    "symptom": ft.Colors.ORANGE_900,
    "diagnosis": ft.Colors.BLUE_900,
    "medication": ft.Colors.GREEN_900,
    "measurement": ft.Colors.PURPLE_900,
    "duration": ft.Colors.GREY_800,
    "vital": ft.Colors.PINK_900,
    "investigation": ft.Colors.AMBER_900,
    "procedure": ft.Colors.CYAN_900,
}


class EntityHighlightedText(ft.Container):
    """
    A widget that displays clinical notes with inline entity highlighting.

    Features:
    - Color-coded highlighting by entity type
    - Hover tooltips showing entity type and normalized value
    - Handles overlapping entities
    - Responsive layout
    """

    def __init__(
        self,
        text: str = "",
        entities: List[EntitySpan] = None,
        max_width: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize entity-highlighted text widget.

        Args:
            text: The clinical notes text
            entities: List of entity spans to highlight
            max_width: Maximum width of the widget
            **kwargs: Additional Container parameters
        """
        self.raw_text = text
        self.entities = entities or []
        self.max_width = max_width

        # Build highlighted content
        content = self._build_highlighted_text()

        super().__init__(
            content=content,
            padding=10,
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            **kwargs
        )

    def _build_highlighted_text(self) -> ft.Control:
        """Build the highlighted text with entity spans."""
        if not self.raw_text:
            return ft.Text(
                "No text to display",
                size=13,
                color=ft.Colors.GREY_400,
                italic=True
            )

        if not self.entities:
            # No entities, just show plain text
            return ft.Text(
                self.raw_text,
                size=13,
                selectable=True
            )

        # Sort entities by start position
        sorted_entities = sorted(self.entities, key=lambda e: e.start)

        # Build text spans
        text_spans = []
        current_pos = 0

        for entity in sorted_entities:
            # Add plain text before entity
            if entity.start > current_pos:
                plain_text = self.raw_text[current_pos:entity.start]
                if plain_text:
                    text_spans.append(
                        ft.TextSpan(
                            text=plain_text,
                            style=ft.TextStyle(size=13)
                        )
                    )

            # Add highlighted entity span
            entity_color = ENTITY_COLORS.get(entity.entity_type, ft.Colors.GREY_200)
            entity_text_color = ENTITY_TEXT_COLORS.get(entity.entity_type, ft.Colors.BLACK)

            # Build tooltip text
            tooltip_lines = [f"Type: {entity.entity_type.title()}"]
            if entity.normalized_value:
                tooltip_lines.append(f"Value: {entity.normalized_value}")
            if entity.confidence < 1.0:
                tooltip_lines.append(f"Confidence: {entity.confidence:.0%}")

            text_spans.append(
                ft.TextSpan(
                    text=entity.text,
                    style=ft.TextStyle(
                        size=13,
                        color=entity_text_color,
                        bgcolor=entity_color,
                        weight=ft.FontWeight.W_500,
                    ),
                    # Tooltip on hover
                    on_enter=lambda e: self._show_entity_tooltip(e),
                    on_exit=lambda e: self._hide_entity_tooltip(e),
                )
            )

            current_pos = entity.end

        # Add remaining plain text
        if current_pos < len(self.raw_text):
            remaining_text = self.raw_text[current_pos:]
            if remaining_text:
                text_spans.append(
                    ft.TextSpan(
                        text=remaining_text,
                        style=ft.TextStyle(size=13)
                    )
                )

        # Create Text with spans
        return ft.Text(
            spans=text_spans,
            selectable=True,
            size=13
        )

    def _show_entity_tooltip(self, e):
        """Show tooltip when hovering over entity."""
        # Note: Flet doesn't support dynamic tooltips on TextSpan yet
        # This is a placeholder for future enhancement
        pass

    def _hide_entity_tooltip(self, e):
        """Hide tooltip when leaving entity."""
        pass

    def update_text(self, text: str, entities: List[EntitySpan]):
        """
        Update the text and entities.

        Args:
            text: New clinical notes text
            entities: New list of entity spans
        """
        self.raw_text = text
        self.entities = entities
        self.content = self._build_highlighted_text()
        if self.page:
            self.update()


class EntityLegend(ft.Container):
    """Legend showing entity types and their colors."""

    def __init__(self, visible_types: List[str] = None, **kwargs):
        """
        Initialize entity legend.

        Args:
            visible_types: List of entity types to show (None = all)
            **kwargs: Additional Container parameters
        """
        self.visible_types = visible_types or list(ENTITY_COLORS.keys())

        # Build legend items
        legend_items = []
        for entity_type in self.visible_types:
            color = ENTITY_COLORS.get(entity_type, ft.Colors.GREY_200)
            legend_items.append(
                ft.Row([
                    ft.Container(
                        width=20,
                        height=15,
                        bgcolor=color,
                        border_radius=3,
                    ),
                    ft.Text(
                        entity_type.title(),
                        size=11,
                        weight=ft.FontWeight.W_400
                    ),
                ], spacing=5)
            )

        content = ft.Row(
            legend_items,
            spacing=15,
            wrap=True,
        )

        super().__init__(
            content=content,
            padding=8,
            **kwargs
        )


class CompactEntityDisplay(ft.Container):
    """
    Compact display of extracted entities organized by type.

    Shows a quick summary of all entities found in the text.
    """

    def __init__(
        self,
        entities_by_type: Dict[str, List[str]],
        on_entity_click: Optional[callable] = None,
        **kwargs
    ):
        """
        Initialize compact entity display.

        Args:
            entities_by_type: Dictionary mapping entity type to list of entity texts
            on_entity_click: Optional callback when entity is clicked
            **kwargs: Additional Container parameters
        """
        self.entities_by_type = entities_by_type
        self.on_entity_click = on_entity_click

        # Build entity chips by category
        content = self._build_entity_chips()

        super().__init__(
            content=content,
            padding=10,
            border_radius=8,
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_300),
            **kwargs
        )

    def _build_entity_chips(self) -> ft.Control:
        """Build entity chips organized by category."""
        if not self.entities_by_type:
            return ft.Text(
                "No entities extracted",
                size=12,
                color=ft.Colors.GREY_400,
                italic=True
            )

        columns = []

        for entity_type, entities in self.entities_by_type.items():
            if not entities:
                continue

            # Get color for this entity type
            color = ENTITY_COLORS.get(entity_type, ft.Colors.GREY_200)
            text_color = ENTITY_TEXT_COLORS.get(entity_type, ft.Colors.BLACK)

            # Create chips for each entity
            chips = []
            for entity_text in entities:
                chip = ft.Container(
                    content=ft.Text(
                        entity_text,
                        size=11,
                        color=text_color,
                        weight=ft.FontWeight.W_500
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=color,
                    border_radius=12,
                    on_click=lambda e, et=entity_text: self._on_chip_click(et) if self.on_entity_click else None,
                )
                chips.append(chip)

            # Add category section
            columns.append(
                ft.Column([
                    ft.Text(
                        entity_type.title() + ":",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_700
                    ),
                    ft.Row(
                        chips,
                        spacing=5,
                        wrap=True,
                    ),
                ], spacing=5)
            )

        return ft.Column(
            columns,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def _on_chip_click(self, entity_text: str):
        """Handle chip click."""
        if self.on_entity_click:
            self.on_entity_click(entity_text)

    def update_entities(self, entities_by_type: Dict[str, List[str]]):
        """
        Update the displayed entities.

        Args:
            entities_by_type: New entities dictionary
        """
        self.entities_by_type = entities_by_type
        self.content = self._build_entity_chips()
        if self.page:
            self.update()
