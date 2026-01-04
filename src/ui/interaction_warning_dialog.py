"""Drug interaction warning dialog."""

import flet as ft
from typing import Callable, List, Dict


class InteractionWarningDialog(ft.AlertDialog):
    """Dialog to display drug interaction warnings."""

    def __init__(
        self,
        interactions: List[Dict],
        on_proceed: Callable[[str], None],
        on_cancel: Callable[[], None]
    ):
        """Initialize the interaction warning dialog.

        Args:
            interactions: List of interaction dicts with severity, effect, etc.
            on_proceed: Callback with override reason when proceeding
            on_cancel: Callback when cancelling
        """
        self.interactions = interactions
        self.on_proceed = on_proceed
        self.on_cancel = on_cancel

        # Check if any are severe/contraindicated (require reason)
        self.requires_reason = any(
            i['severity'] in ('Severe', 'Contraindicated')
            for i in interactions
        )

        # Reason text field (only for severe/contraindicated)
        self.reason_field = ft.TextField(
            label="Clinical reason for proceeding",
            hint_text="Required for severe/contraindicated interactions",
            multiline=True,
            min_lines=2,
            max_lines=4,
            visible=self.requires_reason
        )

        # Build content
        content = self._build_content()

        super().__init__(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.RED_700, size=28),
                ft.Text("Drug Interaction Warning", weight=ft.FontWeight.BOLD, size=18)
            ]),
            content=content,
            actions=[
                ft.TextButton(
                    "Cancel Prescription",
                    on_click=self._on_cancel
                ),
                ft.ElevatedButton(
                    "Proceed Anyway" if not self.requires_reason else "Proceed with Reason",
                    on_click=self._on_proceed,
                    bgcolor=ft.colors.ORANGE_700 if not self.requires_reason else ft.colors.RED_700,
                    color=ft.colors.WHITE
                )
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _build_content(self) -> ft.Container:
        """Build the dialog content."""
        interaction_cards = []

        for interaction in self.interactions:
            severity = interaction['severity']

            # Color based on severity
            if severity == 'Contraindicated':
                color = ft.colors.RED_900
                bg_color = ft.colors.RED_50
                icon = ft.icons.BLOCK
            elif severity == 'Severe':
                color = ft.colors.RED_700
                bg_color = ft.colors.RED_50
                icon = ft.icons.ERROR
            elif severity == 'Moderate':
                color = ft.colors.ORANGE_700
                bg_color = ft.colors.ORANGE_50
                icon = ft.icons.WARNING
            else:  # Minor
                color = ft.colors.YELLOW_800
                bg_color = ft.colors.YELLOW_50
                icon = ft.icons.INFO

            card = ft.Container(
                content=ft.Column([
                    # Header with severity badge
                    ft.Row([
                        ft.Icon(icon, color=color, size=20),
                        ft.Container(
                            content=ft.Text(
                                severity.upper(),
                                weight=ft.FontWeight.BOLD,
                                size=12,
                                color=ft.colors.WHITE
                            ),
                            bgcolor=color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=4
                        ),
                        ft.Text(
                            f"{interaction['drug1']} + {interaction['drug2']}",
                            weight=ft.FontWeight.BOLD,
                            size=14
                        )
                    ], spacing=8),

                    # Effect
                    ft.Text(
                        f"Effect: {interaction['effect']}",
                        size=13,
                        color=ft.colors.GREY_800
                    ),

                    # Mechanism
                    ft.Text(
                        f"Mechanism: {interaction['mechanism']}",
                        size=12,
                        color=ft.colors.GREY_600,
                        italic=True
                    ),

                    # Recommendation
                    ft.Container(
                        content=ft.Text(
                            f"Recommendation: {interaction['recommendation']}",
                            size=12,
                            color=ft.colors.BLUE_800
                        ),
                        padding=ft.padding.all(8),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=4,
                        margin=ft.margin.only(top=4)
                    )
                ], spacing=6),
                padding=ft.padding.all(12),
                bgcolor=bg_color,
                border=ft.border.all(1, color),
                border_radius=8,
                margin=ft.margin.only(bottom=8)
            )
            interaction_cards.append(card)

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    f"Found {len(self.interactions)} drug interaction(s) in this prescription:",
                    size=13,
                    color=ft.colors.GREY_700
                ),
                ft.Container(
                    content=ft.Column(interaction_cards, spacing=0),
                    height=300 if len(self.interactions) > 2 else None,
                    padding=ft.padding.only(top=8, bottom=8)
                ),
                self.reason_field
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            width=550
        )

    def _on_cancel(self, e):
        """Handle cancel button."""
        self.open = False
        if self.page:
            self.page.update()
        self.on_cancel()

    def _on_proceed(self, e):
        """Handle proceed button."""
        reason = self.reason_field.value.strip() if self.requires_reason else "Acknowledged"

        if self.requires_reason and not reason:
            self.reason_field.error_text = "Please provide a clinical reason"
            self.reason_field.update()
            return

        self.open = False
        if self.page:
            self.page.update()
        self.on_proceed(reason)


def check_and_show_interactions(
    page: ft.Page,
    db,
    patient_id: int,
    drugs: List[str],
    on_proceed: Callable[[], None],
    on_cancel: Callable[[], None] = None
):
    """Check for drug interactions and show warning dialog if found.

    Args:
        page: Flet page
        db: Database service
        patient_id: Patient ID
        drugs: List of drug names in new prescription
        on_proceed: Callback when user decides to proceed
        on_cancel: Callback when user cancels
    """
    # Check interactions within new prescription
    interactions = db.check_drug_interactions(drugs)

    # Also check against patient's current medications
    current_interactions = db.check_against_current_meds(patient_id, drugs)

    # Combine and deduplicate
    all_interactions = interactions.copy()
    seen = {(i['drug1'], i['drug2']) for i in all_interactions}
    for i in current_interactions:
        key = (i['drug1'], i['drug2'])
        rev_key = (i['drug2'], i['drug1'])
        if key not in seen and rev_key not in seen:
            all_interactions.append(i)
            seen.add(key)

    if not all_interactions:
        # No interactions, proceed immediately
        on_proceed()
        return

    # Show warning dialog
    def handle_proceed(reason: str):
        # Log overrides for severe/contraindicated
        for interaction in all_interactions:
            if interaction['severity'] in ('Severe', 'Contraindicated'):
                db.log_interaction_override(
                    patient_id=patient_id,
                    visit_id=0,  # Will be updated when visit is saved
                    drug1=interaction['drug1'],
                    drug2=interaction['drug2'],
                    severity=interaction['severity'],
                    reason=reason
                )
        on_proceed()

    def handle_cancel():
        if on_cancel:
            on_cancel()

    dialog = InteractionWarningDialog(
        interactions=all_interactions,
        on_proceed=handle_proceed,
        on_cancel=handle_cancel
    )

    page.dialog = dialog
    dialog.open = True
    page.update()
