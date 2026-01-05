#!/usr/bin/env python3
"""
Test Mobile UI - Verify all screens render correctly

This script tests the mobile app UI without requiring a full build.
It cycles through all screens to check for rendering errors.

Usage:
    python test_mobile_ui.py
"""

import flet as ft
import sys
import os
from datetime import datetime, date

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.screens.home_screen import HomeScreen, AppointmentData
from src.ui.screens.patient_list import PatientListScreen, PatientData
from src.ui.screens.patient_detail import PatientDetailScreen, PatientInfo, VisitData, LabData
from src.ui.screens.settings_screen import SettingsScreen
from src.ui.screens.add_patient_screen import AddPatientScreen
from src.ui.screens.login_screen import LoginScreen
from src.ui.screens.onboarding_screen import OnboardingScreen
from src.ui.haptics import HapticFeedback


class ScreenTester:
    """Test harness for mobile screens."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_screen = "menu"
        self.haptics = HapticFeedback(page)

        # Configure page
        self.page.title = "DocAssist Mobile - UI Test"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Test data
        self.test_patient_data = [
            PatientData(
                id=1,
                name="Ram Lal",
                age=65,
                gender="M",
                phone="9876543210",
                last_visit="2 days ago",
            ),
            PatientData(
                id=2,
                name="Priya Sharma",
                age=32,
                gender="F",
                phone="9876543211",
                last_visit="1 week ago",
            ),
            PatientData(
                id=3,
                name="Amit Kumar",
                age=45,
                gender="M",
                phone="9876543212",
                last_visit="Yesterday",
            ),
        ]

        self.test_appointments = [
            AppointmentData(
                id=1,
                patient_id=1,
                patient_name="Ram Lal",
                time="10:30 AM",
                reason="Follow-up checkup",
            ),
            AppointmentData(
                id=2,
                patient_id=2,
                patient_name="Priya Sharma",
                time="11:00 AM",
                reason="Blood pressure check",
            ),
        ]

        self.test_patient_info = PatientInfo(
            id=1,
            name="Ram Lal",
            uhid="EMR-2024-0001",
            age=65,
            gender="M",
            phone="9876543210",
            address="123 Main Street, Delhi",
        )

        self.test_visits = [
            VisitData(
                id=1,
                date="Jan 3, 2026",
                chief_complaint="Chest pain",
                diagnosis="Angina pectoris",
                prescription='{"medications": [{"drug_name": "Aspirin", "strength": "75mg"}]}',
            ),
        ]

        self.test_labs = [
            LabData(
                id=1,
                test_name="Creatinine",
                result="1.4",
                unit="mg/dL",
                reference_range="0.7-1.3",
                date="Jan 2, 2026",
                is_abnormal=True,
            ),
        ]

    def build(self):
        """Build test menu."""
        self.show_menu()

    def show_menu(self):
        """Show test menu with all screens."""
        self.current_screen = "menu"
        self.page.controls.clear()

        menu = ft.Column(
            [
                ft.AppBar(
                    title=ft.Text("Mobile UI Test Suite"),
                    bgcolor=ft.colors.BLUE_700,
                ),
                ft.Container(height=20),
                ft.Text("Test Screens", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "1. Login Screen",
                    on_click=lambda _: self.test_login(),
                    width=300,
                ),
                ft.ElevatedButton(
                    "2. Onboarding Screen",
                    on_click=lambda _: self.test_onboarding(),
                    width=300,
                ),
                ft.ElevatedButton(
                    "3. Home Screen",
                    on_click=lambda _: self.test_home(),
                    width=300,
                ),
                ft.ElevatedButton(
                    "4. Patient List Screen",
                    on_click=lambda _: self.test_patient_list(),
                    width=300,
                ),
                ft.ElevatedButton(
                    "5. Patient Detail Screen",
                    on_click=lambda _: self.test_patient_detail(),
                    width=300,
                ),
                ft.ElevatedButton(
                    "6. Settings Screen",
                    on_click=lambda _: self.test_settings(),
                    width=300,
                ),
                ft.ElevatedButton(
                    "7. Add Patient Screen",
                    on_click=lambda _: self.test_add_patient(),
                    width=300,
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Test All Screens",
                    on_click=lambda _: self.test_all(),
                    icon=ft.icons.PLAY_ARROW,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.GREEN_700,
                        color=ft.colors.WHITE,
                    ),
                    width=300,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

        self.page.add(menu)
        self.page.update()

    def add_back_button(self):
        """Add back button to return to menu."""
        return ft.FloatingActionButton(
            icon=ft.icons.ARROW_BACK,
            on_click=lambda _: self.show_menu(),
            bgcolor=ft.colors.BLUE_700,
        )

    def test_login(self):
        """Test login screen."""
        print("Testing Login Screen...")
        self.page.controls.clear()

        screen = LoginScreen(
            on_login=lambda email, password: print(f"Login: {email}"),
        )

        self.page.add(
            ft.Stack(
                [
                    screen,
                    ft.Container(
                        content=self.add_back_button(),
                        top=10,
                        left=10,
                    ),
                ],
                expand=True,
            )
        )
        self.page.update()
        print("✓ Login Screen rendered successfully")

    def test_onboarding(self):
        """Test onboarding screen."""
        print("Testing Onboarding Screen...")
        self.page.controls.clear()

        screen = OnboardingScreen(
            on_complete=lambda: print("Onboarding complete"),
            haptics=self.haptics,
        )

        self.page.add(
            ft.Stack(
                [
                    screen,
                    ft.Container(
                        content=self.add_back_button(),
                        top=10,
                        left=10,
                    ),
                ],
                expand=True,
            )
        )
        self.page.update()
        print("✓ Onboarding Screen rendered successfully")

    def test_home(self):
        """Test home screen."""
        print("Testing Home Screen...")
        self.page.controls.clear()

        screen = HomeScreen(
            on_appointment_click=lambda id: print(f"Appointment clicked: {id}"),
            on_patient_click=lambda id: print(f"Patient clicked: {id}"),
            on_refresh=lambda: print("Refresh triggered"),
            sync_status="synced",
            last_sync="2 mins ago",
        )

        # Set appointments
        screen.set_appointments(self.test_appointments)

        self.page.add(
            ft.Stack(
                [
                    screen,
                    ft.Container(
                        content=self.add_back_button(),
                        top=10,
                        left=10,
                    ),
                ],
                expand=True,
            )
        )
        self.page.update()
        print("✓ Home Screen rendered successfully")

    def test_patient_list(self):
        """Test patient list screen."""
        print("Testing Patient List Screen...")
        self.page.controls.clear()

        screen = PatientListScreen(
            on_patient_click=lambda id: print(f"Patient clicked: {id}"),
            on_search=lambda query: print(f"Search: {query}"),
        )

        # Set patients
        screen.set_patients(self.test_patient_data)

        self.page.add(
            ft.Stack(
                [
                    screen,
                    ft.Container(
                        content=self.add_back_button(),
                        top=10,
                        left=10,
                    ),
                ],
                expand=True,
            )
        )
        self.page.update()
        print("✓ Patient List Screen rendered successfully")

    def test_patient_detail(self):
        """Test patient detail screen."""
        print("Testing Patient Detail Screen...")
        self.page.controls.clear()

        screen = PatientDetailScreen(
            patient=self.test_patient_info,
            on_back=lambda: print("Back pressed"),
            on_call=lambda phone: print(f"Call: {phone}"),
            on_share=lambda id: print(f"Share prescription: {id}"),
        )

        # Load data
        screen.set_visits(self.test_visits)
        screen.set_labs(self.test_labs)
        screen.set_procedures([])

        self.page.add(screen)
        self.page.update()
        print("✓ Patient Detail Screen rendered successfully")

    def test_settings(self):
        """Test settings screen."""
        print("Testing Settings Screen...")
        self.page.controls.clear()

        screen = SettingsScreen(
            user_name="Dr. Kumar",
            user_email="kumar@example.com",
            patient_count=150,
            visit_count=1250,
            last_sync="Just now",
            is_dark_mode=False,
            app_version="1.0.0",
            on_sync=lambda: print("Sync triggered"),
            on_toggle_dark_mode=lambda v: print(f"Dark mode: {v}"),
            on_logout=lambda: print("Logout"),
        )

        self.page.add(
            ft.Stack(
                [
                    screen,
                    ft.Container(
                        content=self.add_back_button(),
                        top=10,
                        left=10,
                    ),
                ],
                expand=True,
            )
        )
        self.page.update()
        print("✓ Settings Screen rendered successfully")

    def test_add_patient(self):
        """Test add patient screen."""
        print("Testing Add Patient Screen...")
        self.page.controls.clear()

        screen = AddPatientScreen(
            on_back=lambda: print("Back pressed"),
            on_save=lambda data, open_after: print(f"Save patient: {data}"),
            haptic_feedback=self.haptics,
        )

        self.page.add(screen)
        self.page.update()
        print("✓ Add Patient Screen rendered successfully")

    def test_all(self):
        """Test all screens in sequence."""
        print("\n" + "="*50)
        print("TESTING ALL SCREENS")
        print("="*50 + "\n")

        screens = [
            ("Login", self.test_login),
            ("Onboarding", self.test_onboarding),
            ("Home", self.test_home),
            ("Patient List", self.test_patient_list),
            ("Patient Detail", self.test_patient_detail),
            ("Settings", self.test_settings),
            ("Add Patient", self.test_add_patient),
        ]

        for name, test_func in screens:
            print(f"\n→ Testing {name} Screen...")
            try:
                test_func()
                import time
                time.sleep(1)  # Brief pause to see each screen
            except Exception as e:
                print(f"✗ {name} Screen FAILED: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "="*50)
        print("TEST COMPLETE")
        print("="*50 + "\n")

        # Return to menu
        self.show_menu()


def main(page: ft.Page):
    """Main test entry point."""
    tester = ScreenTester(page)
    tester.build()


if __name__ == "__main__":
    print("DocAssist Mobile - UI Test Suite")
    print("="*50)
    print("Testing UI components without full build...")
    print("")

    # Run in desktop mode for testing
    ft.app(target=main)
