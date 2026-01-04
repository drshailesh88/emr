"""
DocAssist Mobile - Main Application

Premium mobile companion app for DocAssist EMR.
Provides view-only access to patient records with sync from desktop.
"""

import flet as ft
from typing import Optional
from enum import Enum

from .tokens import Colors, MobileSpacing, MobileTypography, Radius


class Screen(Enum):
    """Available screens in the app."""
    LOGIN = "login"
    HOME = "home"
    PATIENTS = "patients"
    PATIENT_DETAIL = "patient_detail"
    SETTINGS = "settings"


class DocAssistMobile:
    """Main mobile application class."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_screen: Screen = Screen.LOGIN
        self.selected_patient_id: Optional[int] = None
        self.is_authenticated: bool = False
        self.is_dark_mode: bool = False

        # Services (initialized after auth)
        self.local_db = None
        self.sync_client = None

        # Configure page
        self._configure_page()

    def _configure_page(self):
        """Configure page settings for mobile."""
        self.page.title = "DocAssist"
        self.page.padding = 0
        self.page.spacing = 0

        # Mobile-optimized settings
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Premium theme
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=Colors.PRIMARY_500,
                on_primary=Colors.NEUTRAL_0,
                secondary=Colors.PRIMARY_600,
                background=Colors.NEUTRAL_0,
                surface=Colors.NEUTRAL_50,
                error=Colors.ERROR_MAIN,
            ),
            use_material3=True,
        )

        self.page.dark_theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=Colors.PRIMARY_200,
                on_primary=Colors.NEUTRAL_900,
                secondary=Colors.PRIMARY_300,
                background=Colors.NEUTRAL_950,
                surface="#1E1E1E",
                error="#F28B82",
            ),
            use_material3=True,
        )

    def build(self):
        """Build the main app UI."""
        # Start with login or home based on auth state
        if self.is_authenticated:
            self._show_main_app()
        else:
            self._show_login()

    def _show_login(self):
        """Show login screen."""
        self.page.controls.clear()

        login_view = ft.Container(
            content=ft.Column(
                [
                    # Logo and title
                    ft.Container(height=80),
                    ft.Icon(
                        ft.Icons.LOCAL_HOSPITAL,
                        size=64,
                        color=Colors.PRIMARY_500,
                    ),
                    ft.Text(
                        "DocAssist",
                        size=MobileTypography.DISPLAY_LARGE,
                        weight=ft.FontWeight.W_300,
                        color=Colors.NEUTRAL_900,
                    ),
                    ft.Text(
                        "Your clinic in your pocket",
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_600,
                    ),
                    ft.Container(height=48),

                    # Login form
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.TextField(
                                    label="Email",
                                    prefix_icon=ft.Icons.EMAIL_OUTLINED,
                                    border_radius=Radius.MD,
                                    height=56,
                                ),
                                ft.Container(height=MobileSpacing.MD),
                                ft.TextField(
                                    label="Password",
                                    prefix_icon=ft.Icons.LOCK_OUTLINED,
                                    password=True,
                                    can_reveal_password=True,
                                    border_radius=Radius.MD,
                                    height=56,
                                ),
                                ft.Container(height=MobileSpacing.LG),
                                ft.ElevatedButton(
                                    text="Login",
                                    width=float("inf"),
                                    height=MobileSpacing.TOUCH_TARGET,
                                    style=ft.ButtonStyle(
                                        bgcolor=Colors.PRIMARY_500,
                                        color=Colors.NEUTRAL_0,
                                        shape=ft.RoundedRectangleBorder(
                                            radius=Radius.BUTTON
                                        ),
                                    ),
                                    on_click=self._handle_login,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=MobileSpacing.SCREEN_PADDING,
                    ),

                    ft.Container(expand=True),

                    # Footer
                    ft.Text(
                        "Privacy-first. Your data stays yours.",
                        size=MobileTypography.CAPTION,
                        color=Colors.NEUTRAL_500,
                    ),
                    ft.Container(height=MobileSpacing.LG),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            bgcolor=Colors.NEUTRAL_0,
        )

        self.page.add(login_view)
        self.page.update()

    def _handle_login(self, e):
        """Handle login button click."""
        # TODO: Implement actual authentication
        # For now, simulate successful login
        self.is_authenticated = True
        self._show_main_app()

    def _show_main_app(self):
        """Show main app with bottom navigation."""
        self.page.controls.clear()

        # Content area (changes based on selected tab)
        self.content_area = ft.Container(
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )

        # Bottom navigation
        self.bottom_nav = ft.NavigationBar(
            selected_index=0,
            height=MobileSpacing.NAV_HEIGHT,
            bgcolor=Colors.NEUTRAL_0,
            indicator_color=Colors.PRIMARY_50,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PEOPLE_OUTLINED,
                    selected_icon=ft.Icons.PEOPLE,
                    label="Patients",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            on_change=self._on_nav_change,
        )

        # Main layout
        main_layout = ft.Column(
            [
                self.content_area,
                self.bottom_nav,
            ],
            spacing=0,
            expand=True,
        )

        self.page.add(main_layout)

        # Show home screen by default
        self._show_home_screen()
        self.page.update()

    def _on_nav_change(self, e):
        """Handle bottom navigation change."""
        index = e.control.selected_index
        if index == 0:
            self._show_home_screen()
        elif index == 1:
            self._show_patients_screen()
        elif index == 2:
            self._show_settings_screen()
        self.page.update()

    def _show_home_screen(self):
        """Show home screen with today's appointments."""
        self.current_screen = Screen.HOME

        # Sync indicator
        sync_status = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=Colors.SUCCESS_MAIN),
                    ft.Text(
                        "Synced 5 min ago",
                        size=MobileTypography.CAPTION,
                        color=Colors.NEUTRAL_600,
                    ),
                ],
                spacing=MobileSpacing.XXS,
            ),
            padding=ft.padding.symmetric(horizontal=MobileSpacing.MD, vertical=MobileSpacing.XS),
        )

        # Today's appointments section
        appointments_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Today's Appointments",
                        size=MobileTypography.TITLE_MEDIUM,
                        weight=ft.FontWeight.W_600,
                        color=Colors.NEUTRAL_900,
                    ),
                    ft.Text(
                        "3 patients",
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_600,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=MobileSpacing.SCREEN_PADDING,
        )

        # Sample appointment cards
        appointments = ft.ListView(
            controls=[
                self._create_appointment_card("9:00 AM", "Ram Kumar", "Follow-up"),
                self._create_appointment_card("10:30 AM", "Priya Sharma", "New consultation"),
                self._create_appointment_card("2:00 PM", "Amit Patel", "Lab review"),
            ],
            spacing=MobileSpacing.SM,
            padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
            expand=True,
        )

        # Recent patients section
        recent_header = ft.Container(
            content=ft.Text(
                "Recent Patients",
                size=MobileTypography.TITLE_MEDIUM,
                weight=ft.FontWeight.W_600,
                color=Colors.NEUTRAL_900,
            ),
            padding=MobileSpacing.SCREEN_PADDING,
        )

        home_content = ft.Column(
            [
                sync_status,
                appointments_header,
                appointments,
            ],
            spacing=0,
            expand=True,
        )

        self.content_area.content = home_content
        self.content_area.update()

    def _create_appointment_card(self, time: str, name: str, reason: str) -> ft.Container:
        """Create an appointment card."""
        return ft.Container(
            content=ft.Row(
                [
                    # Time
                    ft.Container(
                        content=ft.Text(
                            time,
                            size=MobileTypography.BODY_MEDIUM,
                            weight=ft.FontWeight.W_600,
                            color=Colors.PRIMARY_500,
                        ),
                        width=70,
                    ),
                    # Patient info
                    ft.Column(
                        [
                            ft.Text(
                                name,
                                size=MobileTypography.BODY_LARGE,
                                weight=ft.FontWeight.W_500,
                                color=Colors.NEUTRAL_900,
                            ),
                            ft.Text(
                                reason,
                                size=MobileTypography.BODY_SMALL,
                                color=Colors.NEUTRAL_600,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    # Arrow
                    ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        color=Colors.NEUTRAL_400,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            ink=True,
            on_click=lambda e: self._show_patient_detail(1),  # TODO: pass real ID
        )

    def _show_patients_screen(self):
        """Show patient list screen."""
        self.current_screen = Screen.PATIENTS

        # Search bar
        search_bar = ft.Container(
            content=ft.TextField(
                hint_text="Search patients...",
                prefix_icon=ft.Icons.SEARCH,
                border_radius=Radius.FULL,
                height=48,
                bgcolor=Colors.NEUTRAL_0,
                border_color=Colors.NEUTRAL_200,
                focused_border_color=Colors.PRIMARY_500,
            ),
            padding=MobileSpacing.SCREEN_PADDING,
        )

        # Patient list
        patients = ft.ListView(
            controls=[
                self._create_patient_card("Ram Kumar", "M, 65", "Last visit: 2 days ago"),
                self._create_patient_card("Priya Sharma", "F, 42", "Last visit: 1 week ago"),
                self._create_patient_card("Amit Patel", "M, 55", "Last visit: 3 days ago"),
                self._create_patient_card("Sunita Devi", "F, 38", "Last visit: 2 weeks ago"),
                self._create_patient_card("Rajesh Singh", "M, 50", "Last visit: 5 days ago"),
            ],
            spacing=MobileSpacing.XS,
            padding=ft.padding.symmetric(horizontal=MobileSpacing.SCREEN_PADDING),
            expand=True,
        )

        patients_content = ft.Column(
            [
                search_bar,
                patients,
            ],
            spacing=0,
            expand=True,
        )

        self.content_area.content = patients_content
        self.content_area.update()

    def _create_patient_card(self, name: str, demographics: str, last_visit: str) -> ft.Container:
        """Create a patient list card."""
        # Generate initials from name
        initials = "".join([n[0] for n in name.split()[:2]]).upper()

        return ft.Container(
            content=ft.Row(
                [
                    # Avatar
                    ft.Container(
                        content=ft.Text(
                            initials,
                            size=MobileTypography.BODY_MEDIUM,
                            weight=ft.FontWeight.W_600,
                            color=Colors.PRIMARY_500,
                        ),
                        width=48,
                        height=48,
                        border_radius=Radius.FULL,
                        bgcolor=Colors.PRIMARY_50,
                        alignment=ft.alignment.center,
                    ),
                    # Patient info
                    ft.Column(
                        [
                            ft.Text(
                                name,
                                size=MobileTypography.BODY_LARGE,
                                weight=ft.FontWeight.W_500,
                                color=Colors.NEUTRAL_900,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        demographics,
                                        size=MobileTypography.BODY_SMALL,
                                        color=Colors.NEUTRAL_600,
                                    ),
                                    ft.Text(
                                        "•",
                                        size=MobileTypography.BODY_SMALL,
                                        color=Colors.NEUTRAL_400,
                                    ),
                                    ft.Text(
                                        last_visit,
                                        size=MobileTypography.BODY_SMALL,
                                        color=Colors.NEUTRAL_500,
                                    ),
                                ],
                                spacing=MobileSpacing.XS,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    # Arrow
                    ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        color=Colors.NEUTRAL_400,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=MobileSpacing.MD,
            ),
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            ink=True,
            on_click=lambda e: self._show_patient_detail(1),  # TODO: pass real ID
        )

    def _show_patient_detail(self, patient_id: int):
        """Show patient detail screen."""
        self.selected_patient_id = patient_id
        self.current_screen = Screen.PATIENT_DETAIL

        # Header with back button
        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=Colors.NEUTRAL_900,
                        on_click=lambda e: self._go_back(),
                    ),
                    ft.Text(
                        "Patient Details",
                        size=MobileTypography.TITLE_LARGE,
                        weight=ft.FontWeight.W_500,
                        color=Colors.NEUTRAL_900,
                    ),
                ],
            ),
            bgcolor=Colors.NEUTRAL_0,
            padding=ft.padding.only(left=MobileSpacing.XS, right=MobileSpacing.MD, top=MobileSpacing.SM, bottom=MobileSpacing.SM),
        )

        # Patient info card
        patient_header = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    "RK",
                                    size=MobileTypography.HEADLINE_MEDIUM,
                                    weight=ft.FontWeight.W_600,
                                    color=Colors.PRIMARY_500,
                                ),
                                width=64,
                                height=64,
                                border_radius=Radius.FULL,
                                bgcolor=Colors.PRIMARY_50,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Ram Kumar",
                                        size=MobileTypography.HEADLINE_MEDIUM,
                                        weight=ft.FontWeight.W_600,
                                        color=Colors.NEUTRAL_900,
                                    ),
                                    ft.Text(
                                        "UHID: EMR-2024-0001",
                                        size=MobileTypography.BODY_SMALL,
                                        color=Colors.NEUTRAL_600,
                                    ),
                                    ft.Text(
                                        "Male, 65 years • +91 98765 43210",
                                        size=MobileTypography.BODY_SMALL,
                                        color=Colors.NEUTRAL_500,
                                    ),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=MobileSpacing.MD,
                    ),
                    ft.Container(height=MobileSpacing.MD),
                    # Quick actions
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.PHONE, size=18),
                                        ft.Text("Call"),
                                    ],
                                    spacing=MobileSpacing.XS,
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=Colors.PRIMARY_500,
                                    color=Colors.NEUTRAL_0,
                                    shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                                ),
                                height=40,
                            ),
                            ft.OutlinedButton(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.SHARE, size=18),
                                        ft.Text("Share Rx"),
                                    ],
                                    spacing=MobileSpacing.XS,
                                ),
                                style=ft.ButtonStyle(
                                    color=Colors.PRIMARY_500,
                                    shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                                ),
                                height=40,
                            ),
                        ],
                        spacing=MobileSpacing.SM,
                    ),
                ],
            ),
            bgcolor=Colors.NEUTRAL_0,
            padding=MobileSpacing.SCREEN_PADDING,
        )

        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Visits"),
                ft.Tab(text="Labs"),
                ft.Tab(text="Procedures"),
            ],
            expand=True,
        )

        detail_content = ft.Column(
            [
                header,
                patient_header,
                ft.Divider(height=1, color=Colors.NEUTRAL_200),
                tabs,
            ],
            spacing=0,
            expand=True,
        )

        self.content_area.content = detail_content
        self.content_area.update()
        self.page.update()

    def _show_settings_screen(self):
        """Show settings screen."""
        self.current_screen = Screen.SETTINGS

        settings_content = ft.Column(
            [
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
                self._create_settings_section("Account", [
                    self._create_settings_item(
                        ft.Icons.PERSON_OUTLINED,
                        "Dr. Shailesh",
                        "drshailesh@example.com",
                    ),
                ]),

                # Sync section
                self._create_settings_section("Sync", [
                    self._create_settings_item(
                        ft.Icons.SYNC,
                        "Last synced",
                        "5 minutes ago",
                        action=ft.TextButton("Sync now"),
                    ),
                    self._create_settings_item(
                        ft.Icons.STORAGE,
                        "Local data",
                        "127 patients • 856 visits",
                    ),
                ]),

                # Appearance section
                self._create_settings_section("Appearance", [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.DARK_MODE_OUTLINED, color=Colors.NEUTRAL_600),
                                ft.Text(
                                    "Dark mode",
                                    size=MobileTypography.BODY_LARGE,
                                    color=Colors.NEUTRAL_900,
                                    expand=True,
                                ),
                                ft.Switch(
                                    value=self.is_dark_mode,
                                    on_change=self._toggle_dark_mode,
                                ),
                            ],
                            spacing=MobileSpacing.MD,
                        ),
                        bgcolor=Colors.NEUTRAL_0,
                        padding=MobileSpacing.CARD_PADDING,
                    ),
                ]),

                # About section
                self._create_settings_section("About", [
                    self._create_settings_item(
                        ft.Icons.INFO_OUTLINED,
                        "Version",
                        "1.0.0 (Mobile Lite)",
                    ),
                    self._create_settings_item(
                        ft.Icons.HELP_OUTLINED,
                        "Help & Support",
                        "Get help with DocAssist",
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
                            side=ft.BorderSide(1, Colors.ERROR_MAIN),
                            shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                        ),
                        width=float("inf"),
                        height=MobileSpacing.TOUCH_TARGET,
                        on_click=self._handle_logout,
                    ),
                    padding=MobileSpacing.SCREEN_PADDING,
                ),
                ft.Container(height=MobileSpacing.LG),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.content_area.content = settings_content
        self.content_area.update()

    def _create_settings_section(self, title: str, items: list) -> ft.Container:
        """Create a settings section."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            title,
                            size=MobileTypography.LABEL_LARGE,
                            weight=ft.FontWeight.W_600,
                            color=Colors.NEUTRAL_600,
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
                    ),
                ],
                spacing=0,
            ),
        )

    def _create_settings_item(
        self,
        icon: str,
        title: str,
        subtitle: str,
        action: Optional[ft.Control] = None,
    ) -> ft.Container:
        """Create a settings item."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=Colors.NEUTRAL_600, size=24),
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
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    action if action else ft.Container(),
                ],
                spacing=MobileSpacing.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=MobileSpacing.CARD_PADDING,
        )

    def _toggle_dark_mode(self, e):
        """Toggle dark mode."""
        self.is_dark_mode = e.control.value
        self.page.theme_mode = ft.ThemeMode.DARK if self.is_dark_mode else ft.ThemeMode.LIGHT
        self.page.update()

    def _handle_logout(self, e):
        """Handle logout."""
        self.is_authenticated = False
        self._show_login()

    def _go_back(self):
        """Navigate back."""
        if self.current_screen == Screen.PATIENT_DETAIL:
            self._show_patients_screen()
        self.page.update()
