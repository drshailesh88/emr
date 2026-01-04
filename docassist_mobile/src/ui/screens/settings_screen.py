"""
Settings Screen - App configuration and account management.

Premium settings screen with sync controls and preferences.
"""

import flet as ft
from typing import Callable, Optional

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius


class SettingsScreen(ft.Container):
    """
    Settings screen with account, sync, and app preferences.

    Usage:
        settings = SettingsScreen(
            user_name="Dr. Shailesh",
            user_email="doctor@example.com",
            on_logout=handle_logout,
        )
    """

    def __init__(
        self,
        user_name: str = "",
        user_email: str = "",
        patient_count: int = 0,
        visit_count: int = 0,
        last_sync: str = "Never",
        is_dark_mode: bool = False,
        app_version: str = "1.0.0",
        on_sync: Optional[Callable] = None,
        on_toggle_dark_mode: Optional[Callable[[bool], None]] = None,
        on_logout: Optional[Callable] = None,
        on_help: Optional[Callable] = None,
    ):
        self.on_sync = on_sync
        self.on_toggle_dark_mode = on_toggle_dark_mode
        self.on_logout = on_logout
        self.on_help = on_help

        # Dark mode switch
        self.dark_mode_switch = ft.Switch(
            value=is_dark_mode,
            on_change=self._handle_dark_mode_toggle,
        )

        # Build content
        content = ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Text(
                        "Settings",
                        size=MobileTypography.HEADLINE_LARGE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.NEUTRAL_900,
                    ),
                    padding=MobileSpacing.SCREEN_PADDING,
                ),

                # Account section
                self._create_section("Account", [
                    self._create_item(
                        icon=ft.Icons.PERSON,
                        title=user_name or "Not logged in",
                        subtitle=user_email,
                    ),
                ]),

                # Sync section
                self._create_section("Sync", [
                    self._create_item(
                        icon=ft.Icons.SYNC,
                        title="Last synced",
                        subtitle=last_sync,
                        action=ft.TextButton(
                            text="Sync now",
                            style=ft.ButtonStyle(color=Colors.PRIMARY_500),
                            on_click=lambda e: self.on_sync() if self.on_sync else None,
                        ),
                    ),
                    self._create_item(
                        icon=ft.Icons.STORAGE,
                        title="Local data",
                        subtitle=f"{patient_count} patients • {visit_count} visits",
                    ),
                ]),

                # Appearance section
                self._create_section("Appearance", [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.DARK_MODE,
                                    color=Colors.NEUTRAL_600,
                                    size=24,
                                ),
                                ft.Container(width=MobileSpacing.MD),
                                ft.Column(
                                    [
                                        ft.Text(
                                            "Dark mode",
                                            size=MobileTypography.BODY_LARGE,
                                            color=Colors.NEUTRAL_900,
                                        ),
                                        ft.Text(
                                            "Reduce eye strain in low light",
                                            size=MobileTypography.BODY_SMALL,
                                            color=Colors.NEUTRAL_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                self.dark_mode_switch,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=Colors.NEUTRAL_0,
                        padding=MobileSpacing.CARD_PADDING,
                    ),
                ]),

                # About section
                self._create_section("About", [
                    self._create_item(
                        icon=ft.Icons.INFO,
                        title="Version",
                        subtitle=f"{app_version} (Mobile Lite)",
                    ),
                    self._create_item(
                        icon=ft.Icons.HELP,
                        title="Help & Support",
                        subtitle="Get help with DocAssist",
                        on_tap=lambda: self.on_help() if self.on_help else None,
                        show_chevron=True,
                    ),
                    self._create_item(
                        icon=ft.Icons.PRIVACY_TIP,
                        title="Privacy Policy",
                        subtitle="How we protect your data",
                        show_chevron=True,
                    ),
                ]),

                ft.Container(expand=True),

                # Logout button
                ft.Container(
                    content=ft.OutlinedButton(
                        text="Logout",
                        icon=ft.Icons.LOGOUT,
                        style=ft.ButtonStyle(
                            color=Colors.ERROR_MAIN,
                            side=ft.BorderSide(1.5, Colors.ERROR_MAIN),
                            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                        ),
                        width=float("inf"),
                        height=MobileSpacing.TOUCH_TARGET,
                        on_click=self._handle_logout,
                    ),
                    padding=MobileSpacing.SCREEN_PADDING,
                ),

                # Footer
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "DocAssist",
                                size=MobileTypography.BODY_SMALL,
                                color=Colors.NEUTRAL_400,
                            ),
                            ft.Text(
                                "Privacy-first EMR for Indian doctors",
                                size=MobileTypography.CAPTION,
                                color=Colors.NEUTRAL_400,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=MobileSpacing.MD,
                ),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )

    def _create_section(self, title: str, items: list) -> ft.Container:
        """Create a settings section."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            title.upper(),
                            size=MobileTypography.LABEL_MEDIUM,
                            weight=ft.FontWeight.W_600,
                            color=Colors.NEUTRAL_500,
                            letter_spacing=0.5,
                        ),
                        padding=ft.padding.only(
                            left=MobileSpacing.SCREEN_PADDING,
                            top=MobileSpacing.LG,
                            bottom=MobileSpacing.XS,
                        ),
                    ),
                    ft.Container(
                        content=ft.Column(items, spacing=1),
                        bgcolor=Colors.NEUTRAL_0,
                        border_radius=Radius.CARD,
                        margin=ft.margin.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                ],
                spacing=0,
            ),
        )

    def _create_item(
        self,
        icon: str,
        title: str,
        subtitle: str = "",
        action: Optional[ft.Control] = None,
        on_tap: Optional[Callable] = None,
        show_chevron: bool = False,
    ) -> ft.Container:
        """Create a settings item."""
        row_content = [
            ft.Icon(icon, color=Colors.NEUTRAL_600, size=24),
            ft.Container(width=MobileSpacing.MD),
            ft.Column(
                [
                    ft.Text(
                        title,
                        size=MobileTypography.BODY_LARGE,
                        color=Colors.NEUTRAL_900,
                    ),
                    ft.Text(
                        subtitle,
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_600,
                    ) if subtitle else ft.Container(),
                ],
                spacing=2,
                expand=True,
            ),
        ]

        if action:
            row_content.append(action)
        elif show_chevron:
            row_content.append(
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=Colors.NEUTRAL_400)
            )

        return ft.Container(
            content=ft.Row(
                row_content,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=MobileSpacing.CARD_PADDING,
            ink=on_tap is not None,
            on_click=lambda e: on_tap() if on_tap else None,
        )

    def _handle_dark_mode_toggle(self, e):
        """Handle dark mode toggle."""
        if self.on_toggle_dark_mode:
            self.on_toggle_dark_mode(e.control.value)

    def _handle_logout(self, e):
        """Handle logout button."""
        if self.on_logout:
            self.on_logout()

    def update_sync_status(self, last_sync: str):
        """Update last sync time display."""
        # Would need to store reference to update
        pass

    def update_stats(self, patient_count: int, visit_count: int):
        """Update data statistics display."""
        # Would need to store reference to update
        pass
