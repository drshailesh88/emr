#!/usr/bin/env python3
"""
Demo script for the tutorial overlay component.

This script demonstrates how to use the tutorial overlay in a minimal Flet app.
Run this to see the tutorial in action.

Usage:
    python examples/tutorial_overlay_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import flet as ft
    from src.ui.components.tutorial_overlay import show_tutorial_overlay
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)


def main(page: ft.Page):
    """Main demo application."""
    page.title = "Tutorial Overlay Demo"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    # Set window size
    page.window.width = 1400
    page.window.height = 800

    # Tutorial completion state
    tutorial_shown = [False]  # Use list for mutable closure

    def on_tutorial_complete():
        """Handle tutorial completion."""
        print("Tutorial completed!")
        # Remove overlay
        if tutorial_overlay in page.overlay:
            page.overlay.remove(tutorial_overlay)
            tutorial_shown[0] = True
            page.update()

        # Show completion message
        show_completion_message()

    def on_tutorial_skip():
        """Handle tutorial skip."""
        print("Tutorial skipped!")
        # Remove overlay
        if tutorial_overlay in page.overlay:
            page.overlay.remove(tutorial_overlay)
            tutorial_shown[0] = True
            page.update()

        # Show skip message
        show_skip_message()

    def show_completion_message():
        """Show completion confirmation."""
        snackbar = ft.SnackBar(
            content=ft.Text("Tutorial completed! 🎉"),
            bgcolor=ft.Colors.GREEN_700,
        )
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()

    def show_skip_message():
        """Show skip confirmation."""
        snackbar = ft.SnackBar(
            content=ft.Text("Tutorial skipped. You can restart it anytime."),
            bgcolor=ft.Colors.ORANGE_700,
        )
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()

    def restart_tutorial(e):
        """Restart the tutorial."""
        tutorial_shown[0] = False
        start_tutorial(e)

    def start_tutorial(e):
        """Start the tutorial."""
        if tutorial_shown[0]:
            # Tutorial already shown, ask to restart
            dialog = ft.AlertDialog(
                title=ft.Text("Restart Tutorial?"),
                content=ft.Text("The tutorial has already been completed. Do you want to see it again?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog)),
                    ft.ElevatedButton(
                        "Restart",
                        on_click=lambda e: (close_dialog(dialog), show_tutorial()),
                        bgcolor=ft.Colors.BLUE_700,
                    ),
                ],
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
        else:
            show_tutorial()

    def show_tutorial():
        """Show the tutorial overlay."""
        nonlocal tutorial_overlay

        # Create tutorial overlay
        tutorial_overlay = show_tutorial_overlay(
            page=page,
            on_complete=on_tutorial_complete,
            on_skip=on_tutorial_skip,
            is_dark=False,
        )

        # Add to page overlay
        page.overlay.append(tutorial_overlay)
        page.update()

    def close_dialog(dialog):
        """Close a dialog."""
        dialog.open = False
        page.update()

    # Mock UI layout (represents actual DocAssist layout)
    def build_mock_ui():
        """Build mock UI to demonstrate tutorial spotlight."""
        return ft.Row(
            [
                # Left panel (patient list)
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Patients", size=20, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.PERSON),
                                title=ft.Text("Ram Lal"),
                                subtitle=ft.Text("65 years, Male"),
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.PERSON),
                                title=ft.Text("Priya Sharma"),
                                subtitle=ft.Text("42 years, Female"),
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.PERSON),
                                title=ft.Text("Amit Kumar"),
                                subtitle=ft.Text("28 years, Male"),
                            ),
                        ]
                    ),
                    width=280,
                    bgcolor=ft.Colors.GREY_50,
                    padding=20,
                    border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)),
                ),
                # Center panel (prescription)
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Prescription", size=20, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.TextField(
                                label="Chief Complaint",
                                multiline=False,
                            ),
                            ft.TextField(
                                label="Clinical Notes",
                                multiline=True,
                                min_lines=5,
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Generate Rx",
                                        icon=ft.Icons.AUTO_AWESOME,
                                        bgcolor=ft.Colors.BLUE_700,
                                    ),
                                    ft.OutlinedButton("Save"),
                                ],
                                spacing=10,
                            ),
                        ],
                        spacing=10,
                    ),
                    expand=True,
                    bgcolor=ft.Colors.WHITE,
                    padding=20,
                ),
                # Right panel (AI Assistant)
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("AI Assistant", size=20, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.Container(
                                content=ft.Text("Ask me anything about the patient..."),
                                expand=True,
                            ),
                            ft.Row(
                                [
                                    ft.TextField(
                                        hint_text="Type your question...",
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.SEND,
                                        bgcolor=ft.Colors.BLUE_700,
                                    ),
                                ],
                            ),
                        ],
                        spacing=10,
                    ),
                    width=380,
                    bgcolor=ft.Colors.BLUE_50,
                    padding=20,
                    border=ft.border.only(left=ft.BorderSide(1, ft.Colors.GREY_300)),
                ),
            ],
            spacing=0,
            expand=True,
        )

    # Header
    header = ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LOCAL_HOSPITAL, color=ft.Colors.BLUE_700, size=28),
                        ft.Text(
                            "DocAssist EMR - Tutorial Demo",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_700,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Show Tutorial",
                            icon=ft.Icons.SCHOOL,
                            on_click=start_tutorial,
                            bgcolor=ft.Colors.BLUE_700,
                        ),
                    ],
                    spacing=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
    )

    # Info banner
    info_banner = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=20),
                ft.Text(
                    "This is a demo of the tutorial overlay. Click 'Show Tutorial' to see it in action.",
                    size=14,
                ),
            ],
            spacing=10,
        ),
        padding=15,
        bgcolor=ft.Colors.BLUE_50,
        border=ft.border.all(1, ft.Colors.BLUE_200),
        margin=20,
        border_radius=8,
    )

    # Main layout
    page.add(
        ft.Column(
            [
                header,
                info_banner,
                build_mock_ui(),
            ],
            spacing=0,
            expand=True,
        )
    )

    # Initialize tutorial overlay (will be shown when button is clicked)
    tutorial_overlay = None

    # Auto-show tutorial on first load
    show_tutorial()


if __name__ == "__main__":
    ft.app(target=main)
