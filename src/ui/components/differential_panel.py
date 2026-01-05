"""
Differential Diagnosis Panel

Displays AI-calculated differential diagnoses with probabilities,
supporting evidence, and suggested investigations.
"""

import flet as ft
from typing import List, Optional, Callable
from ...services.diagnosis.differential_engine import Differential


class DifferentialPanel(ft.UserControl):
    """
    Collapsible panel showing differential diagnoses.

    Features:
    - Sorted by probability (highest first)
    - Color-coded probability bars
    - Supporting features (green)
    - Against features (red)
    - Suggested investigations
    - Expandable/collapsible per diagnosis
    - Overall panel expand/collapse
    """

    def __init__(
        self,
        on_test_requested: Optional[Callable[[List[str]], None]] = None,
        is_dark: bool = False,
    ):
        """Initialize differential panel.

        Args:
            on_test_requested: Callback when user clicks to order tests
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_test_requested = on_test_requested
        self.is_dark = is_dark

        self.differentials: List[Differential] = []
        self.expanded = True
        self.container: Optional[ft.Container] = None
        self.content_column: Optional[ft.Column] = None
        self.expand_icon: Optional[ft.IconButton] = None

    def build(self):
        """Build the differential panel UI."""
        # Content column (initially empty)
        self.content_column = ft.Column(
            controls=[],
            spacing=8,
            visible=self.expanded,
        )

        # Expand/collapse button
        self.expand_icon = ft.IconButton(
            icon=ft.Icons.EXPAND_LESS if self.expanded else ft.Icons.EXPAND_MORE,
            icon_size=20,
            on_click=self._toggle_expand,
            tooltip="Expand/Collapse",
        )

        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.MEDICAL_INFORMATION, size=20, color=ft.Colors.PURPLE_700),
                ft.Text(
                    "Differential Diagnoses",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_700,
                ),
                ft.Container(expand=True),  # Spacer
                self.expand_icon,
            ], spacing=8),
            padding=ft.padding.only(left=12, right=8, top=8, bottom=8),
            bgcolor=ft.Colors.PURPLE_50 if not self.is_dark else "#2D1B3D",
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

        # Main container
        self.container = ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    content=self.content_column,
                    padding=12,
                    bgcolor=ft.Colors.WHITE if not self.is_dark else "#1A1A1A",
                ),
            ], spacing=0),
            border=ft.border.all(2, ft.Colors.PURPLE_300 if not self.is_dark else ft.Colors.PURPLE_700),
            border_radius=8,
            visible=False,  # Hidden until differentials are loaded
        )

        return self.container

    def update_differentials(self, differentials: List[Differential]):
        """Update the displayed differentials.

        Args:
            differentials: List of Differential objects from DifferentialEngine
        """
        self.differentials = differentials
        self._rebuild_content()

        # Show panel if there are differentials
        if self.container:
            self.container.visible = len(differentials) > 0
            if self.page:
                self.container.update()

    def _rebuild_content(self):
        """Rebuild the content column with current differentials."""
        if not self.content_column:
            return

        self.content_column.controls.clear()

        if not self.differentials:
            self.content_column.controls.append(
                ft.Text(
                    "No differentials calculated yet",
                    size=12,
                    italic=True,
                    color=ft.Colors.GREY_500,
                )
            )
        else:
            for diff in self.differentials:
                diff_card = self._create_differential_card(diff)
                self.content_column.controls.append(diff_card)

        if self.page:
            self.content_column.update()

    def _create_differential_card(self, diff: Differential) -> ft.Control:
        """Create a card for a single differential diagnosis.

        Args:
            diff: Differential object

        Returns:
            Flet control for the differential card
        """
        # Probability percentage
        prob_percent = diff.probability * 100

        # Color coding based on probability
        if prob_percent >= 50:
            prob_color = ft.Colors.RED_700
        elif prob_percent >= 30:
            prob_color = ft.Colors.ORANGE_700
        elif prob_percent >= 15:
            prob_color = ft.Colors.YELLOW_700
        else:
            prob_color = ft.Colors.GREEN_700

        # Expandable details
        details_expanded = ft.Ref[bool]()
        details_column = ft.Ref[ft.Column]()

        def toggle_details(e):
            """Toggle expanded state of this differential."""
            details_column.current.visible = not details_column.current.visible
            expand_btn.current.icon = ft.Icons.EXPAND_LESS if details_column.current.visible else ft.Icons.EXPAND_MORE
            if e.page:
                e.page.update()

        expand_btn = ft.Ref[ft.IconButton]()

        # Build details content
        details_controls = []

        # Supporting features
        if diff.supporting_features:
            details_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("Supporting:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                        *[
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=ft.Colors.GREEN_600),
                                ft.Text(
                                    self._format_feature_name(feature),
                                    size=11,
                                    color=ft.Colors.GREEN_700,
                                ),
                            ], spacing=4)
                            for feature in diff.supporting_features
                        ],
                    ], spacing=4),
                    padding=ft.padding.only(left=8, top=4),
                )
            )

        # Against features
        if diff.against_features:
            details_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("Against:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                        *[
                            ft.Row([
                                ft.Icon(ft.Icons.CANCEL, size=14, color=ft.Colors.RED_600),
                                ft.Text(
                                    self._format_feature_name(feature),
                                    size=11,
                                    color=ft.Colors.RED_700,
                                ),
                            ], spacing=4)
                            for feature in diff.against_features
                        ],
                    ], spacing=4),
                    padding=ft.padding.only(left=8, top=4),
                )
            )

        # Suggested tests
        if diff.suggested_tests:
            test_buttons = []
            for test in diff.suggested_tests[:5]:  # Limit to 5 tests
                test_buttons.append(
                    ft.Container(
                        content=ft.Text(test, size=10),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=ft.Colors.BLUE_50 if not self.is_dark else "#1A2A3D",
                        border=ft.border.all(1, ft.Colors.BLUE_300),
                        border_radius=12,
                    )
                )

            details_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("Suggested Tests:", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ft.Row(
                            test_buttons,
                            spacing=6,
                            wrap=True,
                        ),
                    ], spacing=6),
                    padding=ft.padding.only(left=8, top=4),
                )
            )

        # Create card
        return ft.Container(
            content=ft.Column([
                # Header row
                ft.Row([
                    # Diagnosis name and probability
                    ft.Column([
                        ft.Text(
                            self._format_diagnosis_name(diff.diagnosis),
                            size=13,
                            weight=ft.FontWeight.W_500,
                        ),
                        # Probability bar
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        width=100,
                                        height=6,
                                        bgcolor=ft.Colors.GREY_200,
                                        border_radius=3,
                                        content=ft.Container(
                                            width=prob_percent,
                                            bgcolor=prob_color,
                                            border_radius=3,
                                        ),
                                    ),
                                    ft.Text(
                                        f"{prob_percent:.1f}%",
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        color=prob_color,
                                    ),
                                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ]),
                        ),
                    ], spacing=4, expand=True),
                    # Expand button
                    ft.IconButton(
                        ref=expand_btn,
                        icon=ft.Icons.EXPAND_MORE,
                        icon_size=18,
                        on_click=toggle_details,
                        tooltip="Show details",
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                # Expandable details
                ft.Column(
                    ref=details_column,
                    controls=details_controls,
                    spacing=8,
                    visible=False,
                ),
            ], spacing=6),
            padding=10,
            bgcolor=ft.Colors.GREY_50 if not self.is_dark else "#2A2A2A",
            border=ft.border.all(1, ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700),
            border_radius=6,
        )

    def _format_diagnosis_name(self, diagnosis: str) -> str:
        """Format diagnosis name for display.

        Args:
            diagnosis: Raw diagnosis key (e.g., "acute_coronary_syndrome")

        Returns:
            Formatted name (e.g., "Acute Coronary Syndrome")
        """
        # Replace underscores with spaces and title case
        return diagnosis.replace('_', ' ').title()

    def _format_feature_name(self, feature: str) -> str:
        """Format feature name for display.

        Args:
            feature: Raw feature key (e.g., "chest_pain_radiating_to_arm")

        Returns:
            Formatted name (e.g., "Chest pain radiating to arm")
        """
        # Replace underscores with spaces and capitalize first letter
        return feature.replace('_', ' ').capitalize()

    def _toggle_expand(self, e):
        """Toggle expand/collapse of entire panel."""
        self.expanded = not self.expanded

        if self.content_column:
            self.content_column.visible = self.expanded

        if self.expand_icon:
            self.expand_icon.icon = ft.Icons.EXPAND_LESS if self.expanded else ft.Icons.EXPAND_MORE

        if e.page:
            e.page.update()

    def clear(self):
        """Clear all differentials and hide panel."""
        self.differentials = []
        if self.container:
            self.container.visible = False
        if self.content_column:
            self.content_column.controls.clear()
        if self.page:
            self.update()
