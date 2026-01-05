"""Example integration of WhatsApp conversation panel into DocAssist EMR"""

import flet as ft
from datetime import datetime

# Mock services for demo
class MockDatabaseService:
    """Mock database service for demo"""
    def get_patients(self):
        return []

class MockWhatsAppClient:
    """Mock WhatsApp client for demo"""
    async def send_text(self, to, message):
        print(f"Sending to {to}: {message}")
        return type('obj', (object,), {
            'message_id': 'mock_123',
            'status': type('obj', (object,), {'value': 'sent'})()
        })

class MockConversationHandler:
    """Mock conversation handler for demo"""
    pass

def main(page: ft.Page):
    """Main application entry point"""

    page.title = "DocAssist EMR - WhatsApp Integration Demo"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1400
    page.window_height = 900

    # Import WhatsApp panel
    from .conversation_panel import WhatsAppConversationPanel

    # Initialize mock services
    db_service = MockDatabaseService()
    whatsapp_client = MockWhatsAppClient()
    conversation_handler = MockConversationHandler()

    # Dark mode toggle
    is_dark = False

    def toggle_theme(e):
        nonlocal is_dark
        is_dark = not is_dark
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        page.update()

    # Create WhatsApp conversation panel
    whatsapp_panel = WhatsAppConversationPanel(
        db_service=db_service,
        whatsapp_client=whatsapp_client,
        conversation_handler=conversation_handler,
        on_patient_selected=lambda patient_id: print(f"Selected patient: {patient_id}"),
        is_dark=is_dark
    )

    # Create app bar
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.Icons.LOCAL_HOSPITAL_ROUNDED),
        leading_width=40,
        title=ft.Text("DocAssist EMR - Patient Messages"),
        center_title=False,
        bgcolor=ft.Colors.BLUE_700,
        actions=[
            ft.IconButton(
                icon=ft.Icons.DARK_MODE_ROUNDED,
                tooltip="Toggle dark mode",
                on_click=toggle_theme
            ),
            ft.IconButton(
                icon=ft.Icons.SETTINGS_ROUNDED,
                tooltip="Settings"
            ),
        ],
    )

    # Add components to page
    page.appbar = app_bar
    page.add(whatsapp_panel)

if __name__ == "__main__":
    ft.app(target=main)
