"""First-run setup wizard for DocAssist EMR.

Multi-step wizard to collect doctor profile, clinic info, and preferences.
"""

import flet as ft
from typing import Callable, Optional
import logging

from ..services.settings import SettingsService, DoctorSettings

logger = logging.getLogger(__name__)


class SetupWizard:
    """First-run setup wizard with multi-step flow."""

    def __init__(
        self,
        page: ft.Page,
        settings_service: SettingsService,
        on_complete: Callable[[], None]
    ):
        """Initialize setup wizard.

        Args:
            page: Flet page instance
            settings_service: Settings service for saving configuration
            on_complete: Callback when wizard is completed
        """
        self.page = page
        self.settings = settings_service
        self.on_complete = on_complete
        self.current_step = 0

        # Form data storage
        self.doctor_name = ""
        self.qualifications = ""
        self.registration_number = ""
        self.specialization = ""
        self.clinic_name = ""
        self.clinic_address = ""
        self.phone = ""
        self.email = ""
        self.theme = "light"
        self.language = "en"
        self.backup_frequency = 4

        # UI components
        self.stepper: Optional[ft.Control] = None
        self.container: Optional[ft.Container] = None

    def build(self) -> ft.Container:
        """Build the wizard UI."""
        # Create the main container
        self.container = ft.Container(
            content=self._build_content(),
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )
        return self.container

    def _build_content(self) -> ft.Control:
        """Build the current step content."""
        if self.current_step == 0:
            return self._build_welcome_step()
        elif self.current_step == 1:
            return self._build_doctor_profile_step()
        elif self.current_step == 2:
            return self._build_clinic_info_step()
        elif self.current_step == 3:
            return self._build_preferences_step()
        elif self.current_step == 4:
            return self._build_confirmation_step()
        return ft.Text("Unknown step")

    def _build_welcome_step(self) -> ft.Control:
        """Step 0: Welcome screen."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=80),
                    # Logo/Icon
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.MEDICAL_SERVICES_ROUNDED,
                            size=80,
                            color=ft.Colors.BLUE_700
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=20),
                    # Title
                    ft.Text(
                        "Welcome to DocAssist EMR",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=10),
                    # Subtitle
                    ft.Text(
                        "India's First Local-First AI-Powered EMR",
                        size=18,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=40),
                    # Features
                    ft.Container(
                        content=ft.Column(
                            [
                                self._build_feature_item(
                                    ft.Icons.LOCK_ROUNDED,
                                    "100% Offline & Private",
                                    "Your data never leaves your computer"
                                ),
                                ft.Container(height=15),
                                self._build_feature_item(
                                    ft.Icons.PSYCHOLOGY_ROUNDED,
                                    "AI-Powered Intelligence",
                                    "Natural language search & prescription generation"
                                ),
                                ft.Container(height=15),
                                self._build_feature_item(
                                    ft.Icons.SPEED_ROUNDED,
                                    "Lightning Fast",
                                    "Search thousands of records instantly"
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        width=500,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=40),
                    # Description
                    ft.Container(
                        content=ft.Text(
                            "Let's set up your practice in just a few steps.\n"
                            "This will take less than 2 minutes.",
                            size=14,
                            color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=400,
                    ),
                    ft.Container(height=40),
                    # Buttons
                    ft.Row(
                        [
                            ft.TextButton(
                                "Skip for now",
                                on_click=self._on_skip,
                            ),
                            ft.ElevatedButton(
                                "Get Started",
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                on_click=lambda e: self._next_step(),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_700,
                                    color=ft.Colors.WHITE,
                                    padding=ft.padding.symmetric(horizontal=30, vertical=15),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )

    def _build_feature_item(self, icon: str, title: str, description: str) -> ft.Control:
        """Build a feature item row."""
        return ft.Row(
            [
                ft.Icon(icon, size=32, color=ft.Colors.BLUE_700),
                ft.Column(
                    [
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(description, size=12, color=ft.Colors.GREY_600),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=15,
        )

    def _build_doctor_profile_step(self) -> ft.Control:
        """Step 1: Doctor profile."""
        doctor_name_field = ft.TextField(
            label="Full Name *",
            hint_text="Dr. Rajesh Kumar",
            value=self.doctor_name,
            autofocus=True,
            on_change=lambda e: setattr(self, 'doctor_name', e.control.value),
            width=400,
        )

        qualifications_field = ft.TextField(
            label="Qualifications *",
            hint_text="MBBS, MD (Medicine), DM (Cardiology)",
            value=self.qualifications,
            on_change=lambda e: setattr(self, 'qualifications', e.control.value),
            width=400,
        )

        registration_field = ft.TextField(
            label="Medical Registration Number *",
            hint_text="MH-12345-2020",
            value=self.registration_number,
            on_change=lambda e: setattr(self, 'registration_number', e.control.value),
            width=400,
        )

        specialization_field = ft.TextField(
            label="Specialization (Optional)",
            hint_text="Cardiologist",
            value=self.specialization,
            on_change=lambda e: setattr(self, 'specialization', e.control.value),
            width=400,
        )

        error_text = ft.Text("", color=ft.Colors.RED_600, size=12, visible=False)

        def validate_and_next(e):
            if not self.doctor_name.strip():
                error_text.value = "Please enter your name"
                error_text.visible = True
                self.page.update()
                return
            if not self.qualifications.strip():
                error_text.value = "Please enter your qualifications"
                error_text.visible = True
                self.page.update()
                return
            if not self.registration_number.strip():
                error_text.value = "Please enter your registration number"
                error_text.visible = True
                self.page.update()
                return
            error_text.visible = False
            self._next_step()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=40),
                    # Progress indicator
                    self._build_progress_indicator(),
                    ft.Container(height=30),
                    # Title
                    ft.Text(
                        "Doctor Profile",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "This information will appear on prescriptions",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    # Form fields
                    ft.Container(
                        content=ft.Column(
                            [
                                doctor_name_field,
                                ft.Container(height=15),
                                qualifications_field,
                                ft.Container(height=15),
                                registration_field,
                                ft.Container(height=15),
                                specialization_field,
                                ft.Container(height=10),
                                error_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=30),
                    # Navigation buttons
                    ft.Row(
                        [
                            ft.TextButton(
                                "Back",
                                icon=ft.Icons.ARROW_BACK_ROUNDED,
                                on_click=lambda e: self._previous_step(),
                            ),
                            ft.ElevatedButton(
                                "Next",
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                on_click=validate_and_next,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_700,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=40,
        )

    def _build_clinic_info_step(self) -> ft.Control:
        """Step 2: Clinic information."""
        clinic_name_field = ft.TextField(
            label="Clinic/Hospital Name *",
            hint_text="Apollo Cardiac Care Center",
            value=self.clinic_name,
            autofocus=True,
            on_change=lambda e: setattr(self, 'clinic_name', e.control.value),
            width=400,
        )

        clinic_address_field = ft.TextField(
            label="Clinic Address *",
            hint_text="123, MG Road, Mumbai - 400001",
            value=self.clinic_address,
            multiline=True,
            min_lines=2,
            max_lines=3,
            on_change=lambda e: setattr(self, 'clinic_address', e.control.value),
            width=400,
        )

        phone_field = ft.TextField(
            label="Phone Number *",
            hint_text="+91 98765 43210",
            value=self.phone,
            on_change=lambda e: setattr(self, 'phone', e.control.value),
            width=400,
        )

        email_field = ft.TextField(
            label="Email (Optional)",
            hint_text="doctor@clinic.com",
            value=self.email,
            on_change=lambda e: setattr(self, 'email', e.control.value),
            width=400,
        )

        error_text = ft.Text("", color=ft.Colors.RED_600, size=12, visible=False)

        def validate_and_next(e):
            if not self.clinic_name.strip():
                error_text.value = "Please enter clinic name"
                error_text.visible = True
                self.page.update()
                return
            if not self.clinic_address.strip():
                error_text.value = "Please enter clinic address"
                error_text.visible = True
                self.page.update()
                return
            if not self.phone.strip():
                error_text.value = "Please enter phone number"
                error_text.visible = True
                self.page.update()
                return
            error_text.visible = False
            self._next_step()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=40),
                    # Progress indicator
                    self._build_progress_indicator(),
                    ft.Container(height=30),
                    # Title
                    ft.Text(
                        "Clinic Information",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "This will appear on prescriptions and documents",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    # Form fields
                    ft.Container(
                        content=ft.Column(
                            [
                                clinic_name_field,
                                ft.Container(height=15),
                                clinic_address_field,
                                ft.Container(height=15),
                                phone_field,
                                ft.Container(height=15),
                                email_field,
                                ft.Container(height=10),
                                error_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=30),
                    # Navigation buttons
                    ft.Row(
                        [
                            ft.TextButton(
                                "Back",
                                icon=ft.Icons.ARROW_BACK_ROUNDED,
                                on_click=lambda e: self._previous_step(),
                            ),
                            ft.ElevatedButton(
                                "Next",
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                on_click=validate_and_next,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_700,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=40,
        )

    def _build_preferences_step(self) -> ft.Control:
        """Step 3: Preferences."""
        theme_dropdown = ft.Dropdown(
            label="Theme",
            value=self.theme,
            options=[
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("dark", "Dark"),
            ],
            on_change=lambda e: setattr(self, 'theme', e.control.value),
            width=400,
        )

        language_dropdown = ft.Dropdown(
            label="Language",
            value=self.language,
            options=[
                ft.dropdown.Option("en", "English"),
                ft.dropdown.Option("hi", "Hindi (Coming Soon)", disabled=True),
            ],
            on_change=lambda e: setattr(self, 'language', e.control.value),
            width=400,
        )

        backup_dropdown = ft.Dropdown(
            label="Automatic Backup Frequency",
            value=str(self.backup_frequency),
            options=[
                ft.dropdown.Option("1", "Every hour"),
                ft.dropdown.Option("4", "Every 4 hours (Recommended)"),
                ft.dropdown.Option("12", "Every 12 hours"),
                ft.dropdown.Option("24", "Once daily"),
            ],
            on_change=lambda e: setattr(self, 'backup_frequency', int(e.control.value)),
            width=400,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=40),
                    # Progress indicator
                    self._build_progress_indicator(),
                    ft.Container(height=30),
                    # Title
                    ft.Text(
                        "Preferences",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Customize your experience (can be changed later)",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    # Form fields
                    ft.Container(
                        content=ft.Column(
                            [
                                theme_dropdown,
                                ft.Container(height=15),
                                language_dropdown,
                                ft.Container(height=15),
                                backup_dropdown,
                                ft.Container(height=20),
                                # Info box
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.INFO_OUTLINE_ROUNDED,
                                                size=20,
                                                color=ft.Colors.BLUE_700
                                            ),
                                            ft.Container(
                                                content=ft.Text(
                                                    "Automatic backups are encrypted and stored locally. "
                                                    "You can enable cloud sync later in settings.",
                                                    size=12,
                                                    color=ft.Colors.GREY_700,
                                                ),
                                                expand=True,
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                    bgcolor=ft.Colors.BLUE_50,
                                    border=ft.border.all(1, ft.Colors.BLUE_200),
                                    border_radius=8,
                                    padding=15,
                                    width=400,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=30),
                    # Navigation buttons
                    ft.Row(
                        [
                            ft.TextButton(
                                "Back",
                                icon=ft.Icons.ARROW_BACK_ROUNDED,
                                on_click=lambda e: self._previous_step(),
                            ),
                            ft.ElevatedButton(
                                "Next",
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                on_click=lambda e: self._next_step(),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_700,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=40,
        )

    def _build_confirmation_step(self) -> ft.Control:
        """Step 4: Confirmation."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=40),
                    # Progress indicator
                    self._build_progress_indicator(),
                    ft.Container(height=30),
                    # Title
                    ft.Text(
                        "All Set!",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Review your information",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    # Summary cards
                    ft.Container(
                        content=ft.Column(
                            [
                                # Doctor profile card
                                self._build_summary_card(
                                    "Doctor Profile",
                                    [
                                        ("Name", self.doctor_name),
                                        ("Qualifications", self.qualifications),
                                        ("Registration No.", self.registration_number),
                                    ] + ([("Specialization", self.specialization)] if self.specialization else [])
                                ),
                                ft.Container(height=15),
                                # Clinic info card
                                self._build_summary_card(
                                    "Clinic Information",
                                    [
                                        ("Clinic Name", self.clinic_name),
                                        ("Address", self.clinic_address),
                                        ("Phone", self.phone),
                                    ] + ([("Email", self.email)] if self.email else [])
                                ),
                                ft.Container(height=15),
                                # Preferences card
                                self._build_summary_card(
                                    "Preferences",
                                    [
                                        ("Theme", self.theme.capitalize()),
                                        ("Language", "English" if self.language == "en" else "Hindi"),
                                        ("Backup Frequency", f"Every {self.backup_frequency} hours"),
                                    ]
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        width=500,
                    ),
                    ft.Container(height=30),
                    # Navigation buttons
                    ft.Row(
                        [
                            ft.TextButton(
                                "Back",
                                icon=ft.Icons.ARROW_BACK_ROUNDED,
                                on_click=lambda e: self._previous_step(),
                            ),
                            ft.ElevatedButton(
                                "Complete Setup",
                                icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                                on_click=lambda e: self._complete_setup(),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_700,
                                    color=ft.Colors.WHITE,
                                    padding=ft.padding.symmetric(horizontal=30, vertical=15),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=40,
        )

    def _build_summary_card(self, title: str, items: list) -> ft.Control:
        """Build a summary card with key-value pairs."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700,
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=5),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{key}:",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        width=140,
                                    ),
                                    ft.Text(
                                        value,
                                        size=13,
                                        color=ft.Colors.GREY_700,
                                    ),
                                ],
                                spacing=10,
                            )
                            for key, value in items
                        ],
                        spacing=8,
                    ),
                ],
                spacing=10,
                tight=True,
            ),
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=20,
            width=500,
        )

    def _build_progress_indicator(self) -> ft.Control:
        """Build a step progress indicator."""
        steps = ["Welcome", "Doctor", "Clinic", "Preferences", "Review"]

        return ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Text(
                                    str(i + 1),
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE if i <= self.current_step else ft.Colors.GREY_500,
                                ),
                                width=30,
                                height=30,
                                bgcolor=ft.Colors.BLUE_700 if i <= self.current_step else ft.Colors.GREY_300,
                                border_radius=15,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                steps[i],
                                size=10,
                                color=ft.Colors.BLUE_700 if i <= self.current_step else ft.Colors.GREY_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                )
                for i in range(len(steps))
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

    def _next_step(self):
        """Navigate to next step."""
        if self.current_step < 4:
            self.current_step += 1
            self._refresh()

    def _previous_step(self):
        """Navigate to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._refresh()

    def _refresh(self):
        """Refresh the wizard UI."""
        self.container.content = self._build_content()
        self.page.update()

    def _on_skip(self, e):
        """Handle skip button click."""
        # Save minimal settings with empty doctor name (marks as skipped)
        doctor_settings = DoctorSettings(
            doctor_name="",
            clinic_name="",
            clinic_address="",
            phone="",
            email="",
            registration_number="",
            specialization="",
        )
        self.settings.update_doctor_settings(doctor_settings)

        logger.info("Setup wizard skipped")
        self.on_complete()

    def _complete_setup(self):
        """Save all settings and complete the wizard."""
        try:
            # Save doctor settings
            doctor_settings = DoctorSettings(
                doctor_name=self.doctor_name.strip(),
                qualifications=self.qualifications.strip(),
                registration_number=self.registration_number.strip(),
                specialization=self.specialization.strip(),
                clinic_name=self.clinic_name.strip(),
                clinic_address=self.clinic_address.strip(),
                phone=self.phone.strip(),
                email=self.email.strip(),
            )
            self.settings.update_doctor_settings(doctor_settings)

            # Save theme preference
            app_settings = self.settings.load()
            app_settings.theme = self.theme
            app_settings.language = self.language
            self.settings.save(app_settings)

            # Save backup frequency
            self.settings.set_backup_frequency(self.backup_frequency)

            logger.info("Setup wizard completed successfully")
            self.on_complete()

        except Exception as e:
            logger.error(f"Error saving setup wizard data: {e}", exc_info=True)
            # Show error dialog
            error_dialog = ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text(f"Failed to save settings: {str(e)}"),
                actions=[
                    ft.TextButton("OK", on_click=lambda e: self._close_error_dialog(error_dialog)),
                ],
            )
            self.page.overlay.append(error_dialog)
            error_dialog.open = True
            self.page.update()

    def _close_error_dialog(self, dialog):
        """Close error dialog."""
        dialog.open = False
        self.page.update()
