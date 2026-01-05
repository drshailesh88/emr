"""First-run tutorial overlay for DocAssist EMR.

Interactive step-by-step tutorial that highlights different parts of the UI
and explains key features.
"""

import flet as ft
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class TutorialStep:
    """Represents a single tutorial step."""

    def __init__(
        self,
        title: str,
        description: str,
        icon: str,
        spotlight_position: str = "center",  # "left", "center", "right"
        spotlight_vertical: str = "middle",  # "top", "middle", "bottom"
    ):
        """Initialize tutorial step.

        Args:
            title: Step title
            description: Step description/explanation
            icon: Icon to display
            spotlight_position: Horizontal position of spotlight ("left", "center", "right")
            spotlight_vertical: Vertical position of spotlight ("top", "middle", "bottom")
        """
        self.title = title
        self.description = description
        self.icon = icon
        self.spotlight_position = spotlight_position
        self.spotlight_vertical = spotlight_vertical


class TutorialOverlay:
    """Interactive tutorial overlay with step-by-step guidance."""

    def __init__(
        self,
        page: ft.Page,
        on_complete: Callable[[], None],
        on_skip: Optional[Callable[[], None]] = None,
        is_dark: bool = False,
    ):
        """Initialize tutorial overlay.

        Args:
            page: Flet page instance
            on_complete: Callback when tutorial is completed
            on_skip: Optional callback when tutorial is skipped
            is_dark: Dark mode flag
        """
        self.page = page
        self.on_complete = on_complete
        self.on_skip = on_skip
        self.is_dark = is_dark
        self.current_step = 0

        # Define tutorial steps
        self.steps = [
            TutorialStep(
                title="Patient Panel",
                description="Search for patients by name, phone, or natural language. "
                "Add new patients with the + button. Click on a patient to view their records.",
                icon=ft.Icons.PEOPLE_ROUNDED,
                spotlight_position="left",
                spotlight_vertical="middle",
            ),
            TutorialStep(
                title="Recording Visits",
                description="Enter clinical notes for consultations. Use voice input for hands-free dictation. "
                "The AI will help structure your notes and suggest diagnoses.",
                icon=ft.Icons.EDIT_NOTE_ROUNDED,
                spotlight_position="center",
                spotlight_vertical="top",
            ),
            TutorialStep(
                title="AI Prescription Generation",
                description="Click 'Generate Rx' to let AI draft a prescription based on your notes. "
                "Review and edit before saving. The prescription is generated locally on your computer.",
                icon=ft.Icons.MEDICATION_ROUNDED,
                spotlight_position="center",
                spotlight_vertical="middle",
            ),
            TutorialStep(
                title="AI Assistant",
                description="Ask questions about patient history in natural language. "
                'Try: "What was the last creatinine level?" or "Show me all ECG reports." '
                "All queries run locally and privately.",
                icon=ft.Icons.CHAT_ROUNDED,
                spotlight_position="right",
                spotlight_vertical="top",
            ),
            TutorialStep(
                title="Settings & Backup",
                description="Access settings to configure your profile, clinic info, and backup preferences. "
                "Enable automatic backups to protect your data. All backups are encrypted.",
                icon=ft.Icons.SETTINGS_ROUNDED,
                spotlight_position="right",
                spotlight_vertical="top",
            ),
        ]

        # UI components
        self.overlay_container: Optional[ft.Container] = None
        self.content_card: Optional[ft.Container] = None
        self.progress_indicator: Optional[ft.Row] = None

    def build(self) -> ft.Stack:
        """Build the tutorial overlay UI.

        Returns:
            Stack containing overlay and content
        """
        # Semi-transparent overlay background
        overlay_bg = ft.Container(
            bgcolor="rgba(0,0,0,0.75)",
            expand=True,
        )

        # Spotlight effect container (varies based on current step)
        spotlight = self._build_spotlight()

        # Tutorial content card (centered)
        self.content_card = self._build_content_card()

        # Stack everything
        return ft.Stack(
            [
                overlay_bg,
                spotlight,
                self.content_card,
            ],
            expand=True,
        )

    def _build_spotlight(self) -> ft.Container:
        """Build spotlight effect that highlights the current UI area.

        Returns:
            Container with spotlight effect
        """
        step = self.steps[self.current_step]

        # Determine spotlight position
        if step.spotlight_position == "left":
            left = 50
            width = 280
        elif step.spotlight_position == "right":
            left = None
            right = 50
            width = 380
        else:  # center
            left = 320
            width = 800

        if step.spotlight_vertical == "top":
            top = 80
            height = 250
        elif step.spotlight_vertical == "bottom":
            top = None
            bottom = 80
            height = 200
        else:  # middle
            top = 200
            height = 400

        # Create spotlight container with white border and subtle glow
        spotlight_container = ft.Container(
            border=ft.border.all(3, ft.Colors.WHITE),
            border_radius=12,
            bgcolor="rgba(255,255,255,0.05)",
            shadow=ft.BoxShadow(
                spread_radius=10,
                blur_radius=30,
                color="rgba(255,255,255,0.3)",
            ),
            width=width,
            height=height,
            left=left if step.spotlight_position != "right" else None,
            right=right if step.spotlight_position == "right" else None,
            top=top if step.spotlight_vertical != "bottom" else None,
            bottom=bottom if step.spotlight_vertical == "bottom" else None,
            animate=ft.animation.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
        )

        return spotlight_container

    def _build_content_card(self) -> ft.Container:
        """Build the main tutorial content card.

        Returns:
            Container with tutorial content
        """
        step = self.steps[self.current_step]

        # Step icon and title
        header = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(
                        step.icon,
                        size=40,
                        color=ft.Colors.BLUE_400,
                    ),
                    width=60,
                    height=60,
                    bgcolor=ft.Colors.BLUE_900 if self.is_dark else ft.Colors.BLUE_50,
                    border_radius=30,
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        ft.Text(
                            step.title,
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            f"Step {self.current_step + 1} of {len(self.steps)}",
                            size=12,
                            color=ft.Colors.GREY_400,
                        ),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=15,
        )

        # Step description
        description = ft.Container(
            content=ft.Text(
                step.description,
                size=16,
                color=ft.Colors.GREY_300,
                text_align=ft.TextAlign.LEFT,
            ),
            padding=ft.padding.symmetric(vertical=20),
        )

        # Progress indicator (dots)
        self.progress_indicator = self._build_progress_dots()

        # Navigation buttons
        navigation = self._build_navigation_buttons()

        # Card content
        card_content = ft.Column(
            [
                header,
                ft.Divider(height=1, color=ft.Colors.GREY_700),
                description,
                self.progress_indicator,
                navigation,
            ],
            spacing=15,
            tight=True,
        )

        # Main card container (centered, bottom of screen)
        card = ft.Container(
            content=card_content,
            bgcolor="#1E1E1E" if self.is_dark else ft.Colors.GREY_900,
            border_radius=16,
            padding=30,
            width=550,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=30,
                color="rgba(0,0,0,0.5)",
            ),
            left=None,
            right=None,
            top=None,
            bottom=50,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        return card

    def _build_progress_dots(self) -> ft.Row:
        """Build progress indicator with dots.

        Returns:
            Row with progress dots
        """
        dots = []
        for i in range(len(self.steps)):
            if i == self.current_step:
                # Current step - larger, colored dot
                dot = ft.Container(
                    width=12,
                    height=12,
                    bgcolor=ft.Colors.BLUE_400,
                    border_radius=6,
                )
            elif i < self.current_step:
                # Completed step - filled dot
                dot = ft.Container(
                    width=8,
                    height=8,
                    bgcolor=ft.Colors.BLUE_700,
                    border_radius=4,
                )
            else:
                # Future step - empty dot
                dot = ft.Container(
                    width=8,
                    height=8,
                    bgcolor="transparent",
                    border=ft.border.all(1, ft.Colors.GREY_600),
                    border_radius=4,
                )
            dots.append(dot)

        return ft.Row(
            dots,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )

    def _build_navigation_buttons(self) -> ft.Row:
        """Build navigation buttons (Skip, Previous, Next).

        Returns:
            Row with navigation buttons
        """
        buttons = []

        # Skip button (always visible)
        skip_button = ft.TextButton(
            "Skip Tutorial",
            on_click=self._handle_skip,
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_400,
            ),
        )

        # Previous button (only if not on first step)
        if self.current_step > 0:
            prev_button = ft.OutlinedButton(
                "Previous",
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                on_click=self._handle_previous,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    side=ft.BorderSide(1, ft.Colors.GREY_600),
                ),
            )
            buttons.append(prev_button)

        # Next/Complete button
        is_last_step = self.current_step == len(self.steps) - 1
        next_button = ft.ElevatedButton(
            "Complete Tutorial" if is_last_step else "Next",
            icon=ft.Icons.CHECK_CIRCLE_ROUNDED if is_last_step else ft.Icons.ARROW_FORWARD_ROUNDED,
            on_click=self._handle_next,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700 if is_last_step else ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=30, vertical=15),
            ),
        )
        buttons.append(next_button)

        return ft.Row(
            [
                skip_button,
                ft.Container(expand=True),  # Spacer
                ft.Row(buttons, spacing=10),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _handle_skip(self, e):
        """Handle skip button click."""
        logger.info("Tutorial skipped")
        if self.on_skip:
            self.on_skip()
        else:
            self.on_complete()

    def _handle_previous(self, e):
        """Handle previous button click."""
        if self.current_step > 0:
            self.current_step -= 1
            self._refresh_tutorial()
            logger.debug(f"Tutorial: moved to step {self.current_step + 1}")

    def _handle_next(self, e):
        """Handle next button click."""
        if self.current_step < len(self.steps) - 1:
            # Move to next step
            self.current_step += 1
            self._refresh_tutorial()
            logger.debug(f"Tutorial: moved to step {self.current_step + 1}")
        else:
            # Complete tutorial
            logger.info("Tutorial completed")
            self.on_complete()

    def _refresh_tutorial(self):
        """Refresh the tutorial UI with new step content."""
        # Rebuild the content card with new step
        step = self.steps[self.current_step]

        # Update header
        header_container = self.content_card.content.controls[0]
        icon_container = header_container.controls[0]
        text_column = header_container.controls[1]

        icon_container.content.name = step.icon
        text_column.controls[0].value = step.title
        text_column.controls[1].value = f"Step {self.current_step + 1} of {len(self.steps)}"

        # Update description
        description_container = self.content_card.content.controls[2]
        description_container.content.value = step.description

        # Update progress dots
        self.content_card.content.controls[3] = self._build_progress_dots()

        # Update navigation buttons
        self.content_card.content.controls[4] = self._build_navigation_buttons()

        # Update the page
        self.page.update()


def show_tutorial_overlay(
    page: ft.Page,
    on_complete: Callable[[], None],
    on_skip: Optional[Callable[[], None]] = None,
    is_dark: bool = False,
) -> ft.Stack:
    """Show the tutorial overlay.

    Args:
        page: Flet page instance
        on_complete: Callback when tutorial is completed
        on_skip: Optional callback when tutorial is skipped
        is_dark: Dark mode flag

    Returns:
        Stack with tutorial overlay
    """
    tutorial = TutorialOverlay(
        page=page,
        on_complete=on_complete,
        on_skip=on_skip,
        is_dark=is_dark,
    )
    return tutorial.build()
