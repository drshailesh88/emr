"""
DocAssist Mobile - Main Application

Premium mobile companion app for DocAssist EMR.
Provides view-only access to patient records with sync from desktop.
"""

import flet as ft
import threading
import os
from typing import Optional
from enum import Enum
from datetime import datetime

from .tokens import Colors, MobileSpacing, MobileTypography, Radius
from .screens.login_screen import LoginScreen
from .screens.home_screen import HomeScreen, AppointmentData
from .screens.patient_list import PatientListScreen, PatientData
from .screens.patient_detail import PatientDetailScreen, PatientInfo, VisitData, LabData, ProcedureData
from .screens.settings_screen import SettingsScreen
from .screens.add_patient_screen import AddPatientScreen
from .screens.onboarding_screen import OnboardingScreen
from .screens.welcome_back_screen import WelcomeBackScreen

from .components.floating_action_button import FloatingActionButton, FABAction
from .haptics import HapticFeedback

from ..services.auth_service import AuthService
from ..services.sync_client import SyncClient, SyncStatus
from ..services.local_db import LocalDatabase
from ..services.preferences_service import PreferencesService, get_preferences


class Screen(Enum):
    """Available screens in the app."""
    ONBOARDING = "onboarding"
    WELCOME_BACK = "welcome_back"
    LOGIN = "login"
    HOME = "home"
    PATIENTS = "patients"
    PATIENT_DETAIL = "patient_detail"
    SETTINGS = "settings"
    ADD_PATIENT = "add_patient"


class DocAssistMobile:
    """Main mobile application class."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_screen: Screen = Screen.LOGIN
        self.selected_patient_id: Optional[int] = None

        # Services
        self.auth_service = AuthService()
        self.sync_client = SyncClient(data_dir="data")
        self.local_db = None  # Initialized after first sync
        self.preferences = get_preferences(data_dir="data")

        # Screen instances
        self.onboarding_screen_widget: Optional[OnboardingScreen] = None
        self.welcome_back_screen_widget: Optional[WelcomeBackScreen] = None
        self.login_screen_widget: Optional[LoginScreen] = None
        self.home_screen_widget: Optional[HomeScreen] = None
        self.patient_list_screen_widget: Optional[PatientListScreen] = None
        self.patient_detail_screen_widget: Optional[PatientDetailScreen] = None
        self.settings_screen_widget: Optional[SettingsScreen] = None
        self.add_patient_screen_widget: Optional[AddPatientScreen] = None

        # UI state
        self.is_dark_mode: bool = False
        self.content_area: Optional[ft.Container] = None
        self.bottom_nav: Optional[ft.NavigationBar] = None
        self.fab: Optional[FloatingActionButton] = None
        self.haptics: Optional[HapticFeedback] = None

        # Configure page
        self._configure_page()

        # Setup sync callback
        self.sync_client.set_status_callback(self._on_sync_status_change)

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
        # Initialize haptics early
        self.haptics = HapticFeedback(self.page)

        # Check if user has completed onboarding
        if not self.preferences.has_seen_onboarding():
            # First-time user: show onboarding
            self._show_onboarding()
        elif self.auth_service.is_authenticated():
            # Returning user: show welcome back screen
            self._show_welcome_back()
        else:
            # User has seen onboarding but not logged in: show login
            self._show_login()

    def _on_sync_status_change(self, sync_state):
        """Handle sync status changes."""
        # Update UI when sync status changes
        if self.home_screen_widget:
            status_text = "synced" if sync_state.status == SyncStatus.SUCCESS else "syncing"
            self.home_screen_widget.update_sync_status(
                status_text,
                self.sync_client.get_last_sync_text()
            )

    def _initialize_database(self):
        """Initialize local database connection."""
        try:
            db_path = os.path.join(self.sync_client.data_dir, "clinic.db")
            self.local_db = LocalDatabase(db_path)
        except Exception as e:
            print(f"Database initialization error: {e}")
            # Database doesn't exist yet, will be created after first sync

    def _show_onboarding(self):
        """Show onboarding screen for first-time users."""
        self.page.controls.clear()
        self.current_screen = Screen.ONBOARDING

        self.onboarding_screen_widget = OnboardingScreen(
            on_complete=self._handle_onboarding_complete,
            haptics=self.haptics,
        )

        self.page.add(self.onboarding_screen_widget)
        self.page.update()

    def _handle_onboarding_complete(self):
        """Handle onboarding completion."""
        # Mark onboarding as complete
        self.preferences.set_onboarding_complete()

        # Show login screen
        self._show_login()

    def _show_welcome_back(self):
        """Show welcome back screen for returning users."""
        self.page.controls.clear()
        self.current_screen = Screen.WELCOME_BACK

        # Get user info
        user_name, user_email = self.auth_service.get_user_info()

        # Initialize database for stats
        self._initialize_database()

        # Get today's appointment count
        appointments_today = 0
        if self.local_db:
            try:
                appointments = self.local_db.get_todays_appointments()
                appointments_today = len(appointments)
            except:
                pass

        # Check if biometrics enabled
        biometrics_enabled = self.preferences.get_biometrics_enabled()

        self.welcome_back_screen_widget = WelcomeBackScreen(
            user_name=user_name or "Doctor",
            last_sync=self.sync_client.get_last_sync_text(),
            appointments_today=appointments_today,
            on_continue=self._handle_welcome_continue,
            biometrics_enabled=biometrics_enabled,
            haptics=self.haptics,
        )

        self.page.add(self.welcome_back_screen_widget)
        self.page.update()

    def _handle_welcome_continue(self):
        """Handle continue from welcome back screen."""
        # Show main app
        self._show_main_app()

    def _show_login(self):
        """Show login screen."""
        self.page.controls.clear()
        self.current_screen = Screen.LOGIN

        self.login_screen_widget = LoginScreen(
            on_login=self._handle_login,
        )

        self.page.add(self.login_screen_widget)
        self.page.update()

    def _handle_login(self, email: str, password: str):
        """Handle login attempt."""
        def do_login():
            # Attempt authentication
            success = self.auth_service.login(email, password)

            if success:
                # Set credentials for sync
                token = self.auth_service.get_token()
                key = self.auth_service.get_encryption_key()
                self.sync_client.set_credentials(token, key)

                # Store user name for welcome screen
                user_name, _ = self.auth_service.get_user_info()
                if user_name:
                    self.preferences.set_user_name(user_name)

                # Record last login
                from datetime import datetime
                self.preferences.set_last_login(datetime.now().isoformat())

                # Initialize database
                self._initialize_database()

                # Trigger initial sync in background
                self.sync_client.sync(background=True)

                # Show main app
                self.page.run_task(lambda: self._show_main_app())
            else:
                # Show error
                self.page.run_task(
                    lambda: self.login_screen_widget.show_login_error(
                        "Invalid email or password"
                    )
                )

        # Run login in thread to avoid blocking UI
        threading.Thread(target=do_login, daemon=True).start()

    def _show_main_app(self):
        """Show main app with bottom navigation."""
        self.page.controls.clear()

        # Initialize haptics
        self.haptics = HapticFeedback(self.page)

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

        # Create FAB with quick actions
        self.fab = FloatingActionButton(
            actions=[
                FABAction(
                    icon=ft.Icons.PERSON_ADD,
                    label="Add Patient",
                    on_click=self._show_add_patient_screen,
                ),
                FABAction(
                    icon=ft.Icons.NOTE_ADD,
                    label="New Visit",
                    on_click=self._handle_new_visit,
                ),
                FABAction(
                    icon=ft.Icons.SCIENCE,
                    label="Add Lab Result",
                    on_click=self._handle_add_lab,
                ),
                FABAction(
                    icon=ft.Icons.CALENDAR_TODAY,
                    label="Schedule Appointment",
                    on_click=self._handle_schedule_appointment,
                ),
            ],
            page=self.page,
            haptic_feedback=self.haptics,
        )

        # Position FAB at bottom-right, above navigation bar
        fab_container = ft.Container(
            content=self.fab,
            right=16,
            bottom=MobileSpacing.NAV_HEIGHT + 16,  # Above nav bar
        )

        # Use Stack to layer FAB over content
        content_with_fab = ft.Stack(
            [
                # Main content
                ft.Column(
                    [
                        self.content_area,
                        self.bottom_nav,
                    ],
                    spacing=0,
                    expand=True,
                ),
                # FAB overlay
                fab_container,
            ],
            expand=True,
        )

        self.page.add(content_with_fab)

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

        # Update FAB visibility
        self._update_fab_visibility()
        self.page.update()

    def _show_home_screen(self):
        """Show home screen with today's appointments."""
        self.current_screen = Screen.HOME

        # Create home screen
        self.home_screen_widget = HomeScreen(
            on_appointment_click=self._show_patient_detail,
            on_patient_click=self._show_patient_detail,
            on_refresh=self._handle_manual_sync,
            sync_status="synced" if self.sync_client.state.status == SyncStatus.SUCCESS else "syncing",
            last_sync=self.sync_client.get_last_sync_text(),
        )

        # Load appointments
        self._load_appointments()

        self.content_area.content = self.home_screen_widget
        self.content_area.update()

    def _load_appointments(self):
        """Load today's appointments from database."""
        def load():
            if not self.local_db:
                return

            try:
                appointments = self.local_db.get_todays_appointments()
                appt_data = []
                for appt in appointments:
                    # Format time from datetime
                    time_str = appt.appointment_time.strftime("%I:%M %p")
                    appt_data.append(AppointmentData(
                        id=appt.id,
                        patient_id=appt.patient_id,
                        patient_name=appt.patient_name,
                        time=time_str,
                        reason=appt.reason,
                    ))

                # Update UI on main thread
                self.page.run_task(lambda: self.home_screen_widget.set_appointments(appt_data))
            except Exception as e:
                print(f"Error loading appointments: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _show_patients_screen(self):
        """Show patient list screen."""
        self.current_screen = Screen.PATIENTS

        # Create patient list screen
        self.patient_list_screen_widget = PatientListScreen(
            on_patient_click=self._show_patient_detail,
            on_search=self._handle_patient_search,
        )

        # Load patients
        self._load_patients()

        self.content_area.content = self.patient_list_screen_widget
        self.content_area.update()

    def _load_patients(self, query: str = ""):
        """Load patients from database."""
        def load():
            if not self.local_db:
                self.page.run_task(lambda: self.patient_list_screen_widget.show_no_data())
                return

            try:
                # Show loading
                self.page.run_task(lambda: self.patient_list_screen_widget.show_loading())

                # Search or get all
                if query:
                    patients = self.local_db.search_patients(query)
                else:
                    patients = self.local_db.get_all_patients(limit=100)

                # Convert to display data
                patient_data = []
                for p in patients:
                    last_visit = None
                    if p.last_visit_date:
                        # Calculate time ago
                        from datetime import date
                        delta = date.today() - p.last_visit_date
                        if delta.days == 0:
                            last_visit = "Today"
                        elif delta.days == 1:
                            last_visit = "Yesterday"
                        elif delta.days < 7:
                            last_visit = f"{delta.days} days ago"
                        elif delta.days < 30:
                            weeks = delta.days // 7
                            last_visit = f"{weeks} week{'s' if weeks > 1 else ''} ago"
                        else:
                            last_visit = p.last_visit_date.strftime("%b %d, %Y")

                    patient_data.append(PatientData(
                        id=p.id,
                        name=p.name,
                        age=p.age,
                        gender=p.gender,
                        phone=p.phone,
                        last_visit=last_visit,
                    ))

                # Update UI
                self.page.run_task(lambda: self.patient_list_screen_widget.set_patients(patient_data))
            except Exception as e:
                print(f"Error loading patients: {e}")
                self.page.run_task(lambda: self.patient_list_screen_widget.show_no_data())

        threading.Thread(target=load, daemon=True).start()

    def _handle_patient_search(self, query: str):
        """Handle patient search."""
        self._load_patients(query)

    def _show_patient_detail(self, patient_id: int):
        """Show patient detail screen."""
        self.selected_patient_id = patient_id
        self.current_screen = Screen.PATIENT_DETAIL

        # Create placeholder screen while loading
        if not self.local_db:
            return

        def load():
            try:
                # Get patient info
                patient = self.local_db.get_patient(patient_id)
                if not patient:
                    print(f"Patient {patient_id} not found")
                    return

                # Create patient info
                patient_info = PatientInfo(
                    id=patient.id,
                    name=patient.name,
                    uhid=patient.uhid,
                    age=patient.age,
                    gender=patient.gender,
                    phone=patient.phone,
                    address=patient.address,
                )

                # Create detail screen
                def create_screen():
                    self.patient_detail_screen_widget = PatientDetailScreen(
                        patient=patient_info,
                        on_back=self._go_back,
                        on_call=self._handle_call,
                        on_share=self._handle_share_rx,
                        on_add_appointment=self._handle_add_appointment,
                    )

                    # Load related data
                    self._load_patient_visits(patient_id)
                    self._load_patient_labs(patient_id)
                    self._load_patient_procedures(patient_id)

                    self.content_area.content = self.patient_detail_screen_widget
                    self.content_area.update()

                self.page.run_task(create_screen)

            except Exception as e:
                print(f"Error loading patient detail: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _load_patient_visits(self, patient_id: int):
        """Load patient visits."""
        def load():
            try:
                visits = self.local_db.get_patient_visits(patient_id, limit=20)
                visit_data = []
                for v in visits:
                    visit_data.append(VisitData(
                        id=v.id,
                        date=v.visit_date.strftime("%b %d, %Y"),
                        chief_complaint=v.chief_complaint,
                        diagnosis=v.diagnosis,
                        prescription=v.prescription_json,
                    ))

                self.page.run_task(lambda: self.patient_detail_screen_widget.set_visits(visit_data))
            except Exception as e:
                print(f"Error loading visits: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _load_patient_labs(self, patient_id: int):
        """Load patient lab results."""
        def load():
            try:
                labs = self.local_db.get_patient_investigations(patient_id, limit=50)
                lab_data = []
                for lab in labs:
                    lab_data.append(LabData(
                        id=lab.id,
                        test_name=lab.test_name,
                        result=lab.result or "",
                        unit=lab.unit,
                        reference_range=lab.reference_range,
                        date=lab.test_date.strftime("%b %d, %Y") if lab.test_date else None,
                        is_abnormal=lab.is_abnormal,
                    ))

                self.page.run_task(lambda: self.patient_detail_screen_widget.set_labs(lab_data))
            except Exception as e:
                print(f"Error loading labs: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _load_patient_procedures(self, patient_id: int):
        """Load patient procedures."""
        def load():
            try:
                procedures = self.local_db.get_patient_procedures(patient_id, limit=20)
                proc_data = []
                for proc in procedures:
                    proc_data.append(ProcedureData(
                        id=proc.id,
                        name=proc.procedure_name,
                        date=proc.procedure_date.strftime("%b %d, %Y"),
                        details=proc.details,
                    ))

                self.page.run_task(lambda: self.patient_detail_screen_widget.set_procedures(proc_data))
            except Exception as e:
                print(f"Error loading procedures: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _handle_call(self, phone: str):
        """Handle call button - open phone dialer."""
        import webbrowser
        webbrowser.open(f"tel:{phone}")

    def _handle_share_rx(self, patient_id: int):
        """Handle share prescription."""
        # TODO: Implement prescription sharing
        print(f"Share prescription for patient {patient_id}")

    def _handle_add_appointment(self, patient_id: int):
        """Handle add appointment."""
        # TODO: Implement appointment creation
        print(f"Add appointment for patient {patient_id}")

    def _show_settings_screen(self):
        """Show settings screen."""
        self.current_screen = Screen.SETTINGS

        # Get user info
        user_name, user_email = self.auth_service.get_user_info()

        # Get stats
        patient_count = 0
        visit_count = 0
        if self.local_db:
            try:
                stats = self.local_db.get_stats()
                patient_count = stats.get('patient_count', 0)
                visit_count = stats.get('visit_count', 0)
            except:
                pass

        # Create settings screen
        self.settings_screen_widget = SettingsScreen(
            user_name=user_name or "Guest",
            user_email=user_email or "",
            patient_count=patient_count,
            visit_count=visit_count,
            last_sync=self.sync_client.get_last_sync_text(),
            is_dark_mode=self.is_dark_mode,
            app_version="1.0.0",
            on_sync=self._handle_manual_sync,
            on_toggle_dark_mode=self._toggle_dark_mode,
            on_logout=self._handle_logout,
        )

        self.content_area.content = self.settings_screen_widget
        self.content_area.update()

    def _handle_manual_sync(self):
        """Handle manual sync trigger."""
        if self.sync_client and self.auth_service.is_authenticated():
            self.sync_client.sync(background=True)

    def _toggle_dark_mode(self, value: bool):
        """Toggle dark mode."""
        self.is_dark_mode = value
        self.page.theme_mode = ft.ThemeMode.DARK if self.is_dark_mode else ft.ThemeMode.LIGHT
        self.page.update()

    def _handle_logout(self):
        """Handle logout with confirmation."""
        def confirm_logout(e):
            # Close dialog
            dialog.open = False
            self.page.update()

            # Logout
            self.auth_service.logout()

            # Clear database
            if self.local_db:
                self.local_db.close()
                self.local_db = None

            # Clear sync client
            self.sync_client = SyncClient(data_dir="data")

            # Show login
            self._show_login()

        def cancel_logout(e):
            dialog.open = False
            self.page.update()

        # Show confirmation dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Logout"),
            content=ft.Text("Are you sure you want to logout? This will clear local data."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_logout),
                ft.TextButton(
                    "Logout",
                    on_click=confirm_logout,
                    style=ft.ButtonStyle(color=Colors.ERROR_MAIN),
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _go_back(self):
        """Navigate back."""
        if self.current_screen == Screen.PATIENT_DETAIL:
            # Return to previous screen (either home or patients)
            if self.bottom_nav.selected_index == 0:
                self._show_home_screen()
            else:
                self._show_patients_screen()
        elif self.current_screen == Screen.ADD_PATIENT:
            # Return to patients screen
            self._show_patients_screen()

        # Update FAB visibility
        self._update_fab_visibility()
        self.page.update()

    def _update_fab_visibility(self):
        """Update FAB visibility based on current screen."""
        if not self.fab:
            return

        # Show FAB only on Home and Patients screens
        show_fab = self.current_screen in [Screen.HOME, Screen.PATIENTS]

        # Get the fab_container from the Stack
        if self.page.controls:
            stack = self.page.controls[0]
            if isinstance(stack, ft.Stack) and len(stack.controls) > 1:
                fab_container = stack.controls[1]
                fab_container.visible = show_fab
                fab_container.update()

    def _show_add_patient_screen(self):
        """Show add patient screen."""
        self.current_screen = Screen.ADD_PATIENT

        # Create add patient screen
        self.add_patient_screen_widget = AddPatientScreen(
            on_back=self._go_back,
            on_save=self._handle_save_patient,
            haptic_feedback=self.haptics,
        )

        self.content_area.content = self.add_patient_screen_widget
        self.content_area.update()

        # Hide FAB on add patient screen
        self._update_fab_visibility()

    def _handle_save_patient(self, patient_data: dict, open_after: bool):
        """Handle save patient from add patient screen."""
        if not self.local_db:
            print("Database not initialized")
            return

        def save():
            try:
                # Save to database
                patient_id = self.local_db.add_patient(
                    name=patient_data["name"],
                    phone=patient_data.get("phone"),
                    age=patient_data.get("age"),
                    gender=patient_data["gender"],
                )

                # Update UI on main thread
                def on_saved():
                    if open_after:
                        # Open patient detail
                        self._show_patient_detail(patient_id)
                    else:
                        # Show success message and stay on add screen
                        if self.add_patient_screen_widget:
                            snackbar = self.add_patient_screen_widget.show_success_message(
                                f"Patient {patient_data['name']} added successfully"
                            )
                            if snackbar:
                                self.page.overlay.append(snackbar)
                                snackbar.open = True
                                self.page.update()

                self.page.run_task(on_saved)

            except Exception as e:
                print(f"Error saving patient: {e}")

                def show_error():
                    # Show error snackbar
                    snackbar = ft.SnackBar(
                        content=ft.Text(f"Error saving patient: {e}"),
                        bgcolor=Colors.ERROR_MAIN,
                    )
                    self.page.overlay.append(snackbar)
                    snackbar.open = True
                    self.page.update()

                self.page.run_task(show_error)

        threading.Thread(target=save, daemon=True).start()

    def _handle_new_visit(self):
        """Handle new visit action from FAB."""
        # TODO: Implement new visit screen
        print("New Visit - Not yet implemented")

        # Show snackbar
        snackbar = ft.SnackBar(
            content=ft.Text("New Visit feature coming soon"),
            duration=2000,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def _handle_add_lab(self):
        """Handle add lab result action from FAB."""
        # TODO: Implement add lab screen
        print("Add Lab Result - Not yet implemented")

        # Show snackbar
        snackbar = ft.SnackBar(
            content=ft.Text("Add Lab Result feature coming soon"),
            duration=2000,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def _handle_schedule_appointment(self):
        """Handle schedule appointment action from FAB."""
        # TODO: Implement schedule appointment screen
        print("Schedule Appointment - Not yet implemented")

        # Show snackbar
        snackbar = ft.SnackBar(
            content=ft.Text("Schedule Appointment feature coming soon"),
            duration=2000,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
