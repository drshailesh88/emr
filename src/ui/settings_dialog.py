"""Settings dialog UI component."""

import flet as ft
from typing import Callable, Optional
from datetime import datetime
from pathlib import Path
from ..services.settings import AppSettings, DoctorSettings, ClinicSettings, PreferenceSettings
from ..services.backup import BackupService
from ..services.export import ExportService


class SettingsDialog:
    """Settings dialog with tabs for Doctor, Clinic, and Preferences."""

    def __init__(
        self,
        page: ft.Page,
        current_settings: AppSettings,
        on_save: Callable[[AppSettings], None],
        backup_service: Optional[BackupService] = None,
        last_backup_time: Optional[datetime] = None,
        on_backup: Optional[Callable] = None,
        on_restore: Optional[Callable[[dict], None]] = None,
        export_service: Optional[ExportService] = None,
        current_patient_id: Optional[int] = None
    ):
        """Initialize settings dialog.

        Args:
            page: Flet page
            current_settings: Current application settings
            on_save: Callback when settings are saved
            backup_service: Backup service instance
            last_backup_time: Time of last backup
            on_backup: Callback to trigger manual backup
            on_restore: Callback to restore a backup
            export_service: Export service instance
            current_patient_id: Currently selected patient ID (if any)
        """
        self.page = page
        self.current_settings = current_settings
        self.on_save = on_save
        self.backup_service = backup_service
        self.last_backup_time = last_backup_time
        self.on_backup = on_backup
        self.on_restore = on_restore
        self.export_service = export_service
        self.current_patient_id = current_patient_id

        # Create working copy of settings
        self.working_settings = AppSettings(**current_settings.model_dump())

        # Create dialog
        self.dialog = self._build_dialog()

    def _build_dialog(self) -> ft.AlertDialog:
        """Build the settings dialog."""

        # Doctor tab controls
        self.doctor_name = ft.TextField(
            label="Doctor Name",
            value=self.working_settings.doctor.name,
            hint_text="Dr. Rajesh Kumar",
            autofocus=True,
            on_change=self._on_doctor_change
        )

        self.doctor_qualifications = ft.TextField(
            label="Qualifications",
            value=self.working_settings.doctor.qualifications,
            hint_text="MBBS, MD (Medicine)",
            on_change=self._on_doctor_change
        )

        self.doctor_registration = ft.TextField(
            label="Registration Number",
            value=self.working_settings.doctor.registration_number,
            hint_text="MCI-12345",
            on_change=self._on_doctor_change
        )

        doctor_tab = ft.Container(
            content=ft.Column([
                ft.Text("Doctor Profile", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.doctor_name,
                self.doctor_qualifications,
                self.doctor_registration,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

        # Clinic tab controls
        self.clinic_name = ft.TextField(
            label="Clinic Name",
            value=self.working_settings.clinic.name,
            hint_text="Kumar Clinic",
            on_change=self._on_clinic_change
        )

        self.clinic_address = ft.TextField(
            label="Address",
            value=self.working_settings.clinic.address,
            hint_text="123 Main Street\nMumbai 400001",
            multiline=True,
            min_lines=3,
            max_lines=5,
            on_change=self._on_clinic_change
        )

        self.clinic_phone = ft.TextField(
            label="Phone",
            value=self.working_settings.clinic.phone,
            hint_text="+91 98765 43210",
            on_change=self._on_clinic_change
        )

        self.clinic_email = ft.TextField(
            label="Email",
            value=self.working_settings.clinic.email,
            hint_text="dr.kumar@clinic.com",
            on_change=self._on_clinic_change
        )

        clinic_tab = ft.Container(
            content=ft.Column([
                ft.Text("Clinic Information", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.clinic_name,
                self.clinic_address,
                self.clinic_phone,
                self.clinic_email,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

        # Preferences tab controls
        self.backup_frequency = ft.TextField(
            label="Backup Frequency (hours)",
            value=str(self.working_settings.preferences.backup_frequency_hours),
            hint_text="4",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_preferences_change
        )

        self.backup_retention = ft.TextField(
            label="Backup Retention Count",
            value=str(self.working_settings.preferences.backup_retention_count),
            hint_text="10",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_preferences_change
        )

        self.model_override = ft.TextField(
            label="Model Override (optional)",
            value=self.working_settings.preferences.model_override or "",
            hint_text="qwen2.5:3b",
            on_change=self._on_preferences_change
        )

        self.theme = ft.Dropdown(
            label="Theme",
            value=self.working_settings.preferences.theme,
            options=[
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("dark", "Dark"),
                ft.dropdown.Option("system", "System"),
            ],
            on_change=self._on_preferences_change
        )

        preferences_tab = ft.Container(
            content=ft.Column([
                ft.Text("Preferences", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.backup_frequency,
                self.backup_retention,
                self.model_override,
                self.theme,
                ft.Divider(),
                ft.Text(
                    "Note: Model override will take effect after restart. Leave blank for auto-detection.",
                    size=11,
                    color=ft.Colors.GREY_600,
                    italic=True
                ),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

        # Backups tab
        backups_tab = self._build_backups_tab()

        # Export tab
        export_tab = self._build_export_tab()

        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Doctor",
                    icon=ft.Icons.PERSON,
                    content=doctor_tab,
                ),
                ft.Tab(
                    text="Clinic",
                    icon=ft.Icons.BUSINESS,
                    content=clinic_tab,
                ),
                ft.Tab(
                    text="Preferences",
                    icon=ft.Icons.SETTINGS,
                    content=preferences_tab,
                ),
                ft.Tab(
                    text="Backups",
                    icon=ft.Icons.BACKUP,
                    content=backups_tab,
                ),
                ft.Tab(
                    text="Export",
                    icon=ft.Icons.DOWNLOAD,
                    content=export_tab,
                ),
            ],
            expand=True,
        )

        # Create dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Container(
                content=tabs,
                width=600,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._on_cancel),
                ft.ElevatedButton("Save", on_click=self._on_save_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return dialog

    def _build_backups_tab(self) -> ft.Container:
        """Build the backups tab content."""
        # Get backup status
        backup_status_text = "No backups yet"
        if self.last_backup_time:
            delta = datetime.now() - self.last_backup_time
            minutes = int(delta.total_seconds() / 60)
            if minutes < 1:
                backup_status_text = "Last backup: just now"
            elif minutes < 60:
                backup_status_text = f"Last backup: {minutes}m ago"
            else:
                hours = minutes // 60
                backup_status_text = f"Last backup: {hours}h ago"

        # Get list of backups
        backup_list_items = []
        if self.backup_service:
            backups = self.backup_service.list_backups()
            for backup in backups[:10]:  # Show last 10
                created_at = backup.get("created_at", "Unknown")
                try:
                    dt = datetime.fromisoformat(created_at)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = created_at[:16] if len(created_at) > 16 else created_at

                size_mb = backup.get("size_bytes", 0) / (1024 * 1024)
                patient_count = backup.get("patient_count", "?")

                backup_list_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(date_str, size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{patient_count} patients | {size_mb:.1f} MB",
                                       size=11, color=ft.Colors.GREY_600),
                            ], spacing=2, tight=True),
                            ft.IconButton(
                                icon=ft.Icons.RESTORE,
                                tooltip="Restore this backup",
                                on_click=lambda e, b=backup: self._on_restore_click(b)
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=5,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=5,
                    )
                )

        backups_content = ft.Column([
            ft.Text("Backup Management", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(),

            ft.Text(backup_status_text, size=14),

            ft.ElevatedButton(
                "Backup Now",
                icon=ft.Icons.BACKUP,
                on_click=self._on_backup_click
            ),

            ft.Container(height=10),

            ft.Text("Recent Backups:", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(
                    backup_list_items if backup_list_items else [
                        ft.Text("No backups found", size=12, color=ft.Colors.GREY_600)
                    ],
                    spacing=5,
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=200,
            ),

            ft.Container(height=10),
            ft.Text(
                "Note: Backups are created automatically on startup, shutdown, and every N hours (configurable in Preferences).",
                size=11,
                color=ft.Colors.GREY_600,
                italic=True
            ),
        ], spacing=15, scroll=ft.ScrollMode.AUTO)

        return ft.Container(
            content=backups_content,
            padding=20,
        )

    def _on_backup_click(self, e):
        """Handle backup button click."""
        if self.on_backup:
            self.on_backup()

    def _on_restore_click(self, backup_info: dict):
        """Handle restore button click."""
        if self.on_restore:
            self.on_restore(backup_info)

    def _build_export_tab(self) -> ft.Container:
        """Build the export tab content."""
        if not self.export_service:
            return ft.Container(
                content=ft.Column([
                    ft.Text("Export service not available", size=14, color=ft.Colors.RED),
                ]),
                padding=20,
            )

        # Status text
        self.export_status_text = ft.Text("", size=12, color=ft.Colors.GREY_600)

        # Single Patient Export section
        patient_export_enabled = self.current_patient_id is not None

        patient_section = ft.Column([
            ft.Text("Single Patient Export", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Export currently selected patient's complete record"
                if patient_export_enabled
                else "No patient selected - select a patient first",
                size=11,
                color=ft.Colors.GREY_600,
            ),
            ft.Row([
                ft.ElevatedButton(
                    "Export as PDF",
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=self._on_export_patient_pdf,
                    disabled=not patient_export_enabled,
                ),
                ft.ElevatedButton(
                    "Export as JSON",
                    icon=ft.Icons.CODE,
                    on_click=self._on_export_patient_json,
                    disabled=not patient_export_enabled,
                ),
            ], spacing=10),
        ], spacing=10)

        # Bulk Export section
        bulk_section = ft.Column([
            ft.Text("Bulk Export", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Export all data for analysis or migration",
                size=11,
                color=ft.Colors.GREY_600,
            ),
            ft.Row([
                ft.ElevatedButton(
                    "Patients CSV",
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._on_export_patients_csv,
                ),
                ft.ElevatedButton(
                    "Visits CSV",
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._on_export_visits_csv,
                ),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton(
                    "Investigations CSV",
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._on_export_investigations_csv,
                ),
                ft.ElevatedButton(
                    "Procedures CSV",
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self._on_export_procedures_csv,
                ),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton(
                    "Full Database JSON",
                    icon=ft.Icons.STORAGE,
                    on_click=self._on_export_full_database,
                ),
            ], spacing=10),
        ], spacing=10)

        export_content = ft.Column([
            ft.Text("Data Export", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            patient_section,
            ft.Divider(),
            bulk_section,
            ft.Container(height=10),
            self.export_status_text,
            ft.Container(height=10),
            ft.Text(
                "Note: All exports are saved to data/exports/ folder with timestamp. "
                "CSV files are Excel-compatible (UTF-8 with BOM).",
                size=11,
                color=ft.Colors.GREY_600,
                italic=True,
            ),
        ], spacing=15, scroll=ft.ScrollMode.AUTO)

        return ft.Container(
            content=export_content,
            padding=20,
        )

    def _show_export_status(self, message: str, is_error: bool = False):
        """Show export status message."""
        self.export_status_text.value = message
        self.export_status_text.color = ft.Colors.RED if is_error else ft.Colors.GREEN
        self.page.update()

    def _on_export_patient_pdf(self, e):
        """Handle export patient as PDF."""
        if not self.export_service or not self.current_patient_id:
            return

        try:
            self._show_export_status("Exporting patient PDF...")
            output_path = self.export_service.export_patient_summary_pdf(
                self.current_patient_id
            )
            self._show_export_status(f"Success! PDF saved to: {output_path}")
        except Exception as ex:
            self._show_export_status(f"Error: {str(ex)}", is_error=True)

    def _on_export_patient_json(self, e):
        """Handle export patient as JSON."""
        if not self.export_service or not self.current_patient_id:
            return

        try:
            self._show_export_status("Exporting patient JSON...")
            output_path = self.export_service.export_patient_json(
                self.current_patient_id
            )
            self._show_export_status(f"Success! JSON saved to: {output_path}")
        except Exception as ex:
            self._show_export_status(f"Error: {str(ex)}", is_error=True)

    def _on_export_patients_csv(self, e):
        """Handle export all patients as CSV."""
        if not self.export_service:
            return

        try:
            self._show_export_status("Exporting patients CSV...")
            output_path = self.export_service.export_all_patients_csv()
            self._show_export_status(f"Success! CSV saved to: {output_path}")
        except Exception as ex:
            self._show_export_status(f"Error: {str(ex)}", is_error=True)

    def _on_export_visits_csv(self, e):
        """Handle export all visits as CSV."""
        if not self.export_service:
            return

        try:
            self._show_export_status("Exporting visits CSV...")
            output_path = self.export_service.export_all_visits_csv()
            self._show_export_status(f"Success! CSV saved to: {output_path}")
        except Exception as ex:
            self._show_export_status(f"Error: {str(ex)}", is_error=True)

    def _on_export_investigations_csv(self, e):
        """Handle export all investigations as CSV."""
        if not self.export_service:
            return

        try:
            self._show_export_status("Exporting investigations CSV...")
            output_path = self.export_service.export_all_investigations_csv()
            self._show_export_status(f"Success! CSV saved to: {output_path}")
        except Exception as ex:
            self._show_export_status(f"Error: {str(ex)}", is_error=True)

    def _on_export_procedures_csv(self, e):
        """Handle export all procedures as CSV."""
        if not self.export_service:
            return

        try:
            self._show_export_status("Exporting procedures CSV...")
            output_path = self.export_service.export_all_procedures_csv()
            self._show_export_status(f"Success! CSV saved to: {output_path}")
        except Exception as ex:
            self._show_export_status(f"Error: {str(ex)}", is_error=True)

    def _on_export_full_database(self, e):
        """Handle export full database as JSON."""
        if not self.export_service:
            return

        try:
            self._show_export_status("Exporting full database JSON...")
            output_path = self.export_service.export_full_database_json()
            self._show_export_status(f"Success! JSON saved to: {output_path}")
        except Exception as ex:
            self._show_export_status(f"Error: {str(ex)}", is_error=True)

    def _on_doctor_change(self, e):
        """Handle changes to doctor fields."""
        self.working_settings.doctor.name = self.doctor_name.value
        self.working_settings.doctor.qualifications = self.doctor_qualifications.value
        self.working_settings.doctor.registration_number = self.doctor_registration.value

    def _on_clinic_change(self, e):
        """Handle changes to clinic fields."""
        self.working_settings.clinic.name = self.clinic_name.value
        self.working_settings.clinic.address = self.clinic_address.value
        self.working_settings.clinic.phone = self.clinic_phone.value
        self.working_settings.clinic.email = self.clinic_email.value

    def _on_preferences_change(self, e):
        """Handle changes to preferences fields."""
        try:
            self.working_settings.preferences.backup_frequency_hours = int(self.backup_frequency.value or 4)
        except ValueError:
            self.working_settings.preferences.backup_frequency_hours = 4

        try:
            self.working_settings.preferences.backup_retention_count = int(self.backup_retention.value or 10)
        except ValueError:
            self.working_settings.preferences.backup_retention_count = 10

        model_val = self.model_override.value.strip()
        self.working_settings.preferences.model_override = model_val if model_val else None

        self.working_settings.preferences.theme = self.theme.value

    def _on_save_click(self, e):
        """Handle save button click."""
        # Update working settings one more time to ensure all fields are captured
        self._on_doctor_change(None)
        self._on_clinic_change(None)
        self._on_preferences_change(None)

        # Call save callback
        self.on_save(self.working_settings)

        # Close dialog
        self.dialog.open = False
        self.page.update()

    def _on_cancel(self, e):
        """Handle cancel button click."""
        self.dialog.open = False
        self.page.update()

    def show(self):
        """Show the dialog."""
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()
