"""Attachment picker for sending files via WhatsApp"""
import flet as ft
from typing import Callable, Optional, List, Dict
from datetime import datetime, date


class AttachmentPicker(ft.UserControl):
    """Bottom sheet for selecting attachments to send"""

    def __init__(
        self,
        patient_id: int,
        patient_name: str,
        on_send_prescription: Callable[[int], None],
        on_send_lab_report: Callable[[int], None],
        on_send_document: Callable[[str], None],
        on_send_appointment: Callable[[Dict], None],
        on_send_location: Callable[[], None],
        get_recent_prescriptions: Callable[[int], List[Dict]],
        get_recent_lab_reports: Callable[[int], List[Dict]],
        is_dark: bool = False,
    ):
        super().__init__()
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.on_send_prescription = on_send_prescription
        self.on_send_lab_report = on_send_lab_report
        self.on_send_document = on_send_document
        self.on_send_appointment = on_send_appointment
        self.on_send_location = on_send_location
        self.get_recent_prescriptions = get_recent_prescriptions
        self.get_recent_lab_reports = get_recent_lab_reports
        self.is_dark = is_dark

        self.bottom_sheet = None
        self.content_view = None

    def show(self):
        """Show the attachment picker"""
        if self.bottom_sheet:
            self.bottom_sheet.open = True
            self.bottom_sheet.update()

    def hide(self):
        """Hide the attachment picker"""
        if self.bottom_sheet:
            self.bottom_sheet.open = False
            self.bottom_sheet.update()

    def _show_prescription_picker(self, e):
        """Show prescription selection view"""
        prescriptions = self.get_recent_prescriptions(self.patient_id)

        if not prescriptions:
            self._show_empty_state("No prescriptions found for this patient")
            return

        prescription_items = []
        for rx in prescriptions:
            prescription_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        f"Visit: {rx.get('visit_date', 'Unknown')}",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        rx.get('diagnosis', 'No diagnosis'),
                                        size=12,
                                        color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SEND_ROUNDED,
                                icon_color=ft.Colors.BLUE_600,
                                tooltip="Send",
                                on_click=lambda e, rx_id=rx.get('id'): self._send_prescription(rx_id),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.all(12),
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                    ),
                    on_click=lambda e, rx_id=rx.get('id'): self._send_prescription(rx_id),
                )
            )

        self.content_view.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_ROUNDED,
                            on_click=self._show_main_menu,
                        ),
                        ft.Text(
                            "Select Prescription",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.padding.all(16),
                border=ft.border.only(
                    bottom=ft.BorderSide(2, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                ),
            ),
            ft.Column(
                controls=prescription_items,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
        ]
        self.content_view.update()

    def _show_lab_report_picker(self, e):
        """Show lab report selection view"""
        reports = self.get_recent_lab_reports(self.patient_id)

        if not reports:
            self._show_empty_state("No lab reports found for this patient")
            return

        report_items = []
        for report in reports:
            report_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        report.get('test_name', 'Unknown Test'),
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                f"Date: {report.get('test_date', 'Unknown')}",
                                                size=12,
                                                color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                                            ),
                                            ft.Container(
                                                content=ft.Text(
                                                    "ABNORMAL" if report.get('is_abnormal') else "NORMAL",
                                                    size=10,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ft.Colors.WHITE,
                                                ),
                                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                                border_radius=ft.border_radius.all(8),
                                                bgcolor=ft.Colors.RED_500 if report.get('is_abnormal') else ft.Colors.GREEN_500,
                                            ),
                                        ],
                                        spacing=8,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SEND_ROUNDED,
                                icon_color=ft.Colors.BLUE_600,
                                tooltip="Send",
                                on_click=lambda e, report_id=report.get('id'): self._send_lab_report(report_id),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.all(12),
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                    ),
                    on_click=lambda e, report_id=report.get('id'): self._send_lab_report(report_id),
                )
            )

        self.content_view.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_ROUNDED,
                            on_click=self._show_main_menu,
                        ),
                        ft.Text(
                            "Select Lab Report",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.padding.all(16),
                border=ft.border.only(
                    bottom=ft.BorderSide(2, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                ),
            ),
            ft.Column(
                controls=report_items,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
        ]
        self.content_view.update()

    def _show_document_picker(self, e):
        """Show file picker for documents"""
        # This would integrate with Flet's file picker
        file_picker = ft.FilePicker(
            on_result=self._handle_file_picked
        )
        if self.page:
            self.page.overlay.append(file_picker)
            self.page.update()
            file_picker.pick_files(
                allowed_extensions=["pdf", "doc", "docx", "jpg", "png"],
                allow_multiple=False,
            )

    def _handle_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if e.files:
            file_path = e.files[0].path
            if self.on_send_document:
                self.on_send_document(file_path)
            self.hide()

    def _show_appointment_details(self, e):
        """Show appointment details to send"""
        # Mock appointment data - would come from database
        appointment = {
            "date": date.today().strftime("%A, %d %B %Y"),
            "time": "10:00 AM",
            "doctor": "Dr. Sharma",
            "clinic": "DocAssist Clinic",
            "address": "123 Main Street, City - 123456",
        }

        if self.on_send_appointment:
            self.on_send_appointment(appointment)
        self.hide()

    def _show_location(self, e):
        """Send clinic location"""
        if self.on_send_location:
            self.on_send_location()
        self.hide()

    def _send_prescription(self, prescription_id: int):
        """Send prescription"""
        if self.on_send_prescription:
            self.on_send_prescription(prescription_id)
        self.hide()

    def _send_lab_report(self, report_id: int):
        """Send lab report"""
        if self.on_send_lab_report:
            self.on_send_lab_report(report_id)
        self.hide()

    def _show_main_menu(self, e=None):
        """Show main attachment menu"""
        menu_items = [
            {
                "icon": ft.Icons.DESCRIPTION_ROUNDED,
                "title": "Send Prescription",
                "subtitle": "Recent prescriptions for this patient",
                "color": ft.Colors.PURPLE_400,
                "on_click": self._show_prescription_picker,
            },
            {
                "icon": ft.Icons.SCIENCE_ROUNDED,
                "title": "Send Lab Report",
                "subtitle": "Recent test results",
                "color": ft.Colors.BLUE_400,
                "on_click": self._show_lab_report_picker,
            },
            {
                "icon": ft.Icons.INSERT_DRIVE_FILE_ROUNDED,
                "title": "Send Document",
                "subtitle": "Pick a file from your device",
                "color": ft.Colors.GREEN_400,
                "on_click": self._show_document_picker,
            },
            {
                "icon": ft.Icons.CALENDAR_TODAY_ROUNDED,
                "title": "Send Appointment Details",
                "subtitle": "Share upcoming appointment",
                "color": ft.Colors.ORANGE_400,
                "on_click": self._show_appointment_details,
            },
            {
                "icon": ft.Icons.LOCATION_ON_ROUNDED,
                "title": "Send Clinic Location",
                "subtitle": "Share clinic address and map",
                "color": ft.Colors.RED_400,
                "on_click": self._show_location,
            },
        ]

        menu_controls = []
        for item in menu_items:
            menu_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    item["icon"],
                                    size=24,
                                    color=ft.Colors.WHITE,
                                ),
                                width=48,
                                height=48,
                                border_radius=ft.border_radius.all(24),
                                bgcolor=item["color"],
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        item["title"],
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        item["subtitle"],
                                        size=12,
                                        color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(
                                ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                size=16,
                                color=ft.Colors.GREY_400,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.all(16),
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                    ),
                    on_click=item["on_click"],
                    on_hover=self._handle_item_hover,
                )
            )

        self.content_view.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            "Send Attachment",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED,
                            on_click=lambda e: self.hide(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.all(16),
                border=ft.border.only(
                    bottom=ft.BorderSide(2, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                ),
            ),
            ft.Column(
                controls=menu_controls,
                spacing=0,
            ),
        ]
        self.content_view.update()

    def _show_empty_state(self, message: str):
        """Show empty state message"""
        self.content_view.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_ROUNDED,
                            on_click=self._show_main_menu,
                        ),
                    ],
                ),
                padding=ft.padding.all(16),
                border=ft.border.only(
                    bottom=ft.BorderSide(2, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                ),
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.FOLDER_OFF_ROUNDED,
                            size=64,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Text(
                            message,
                            size=14,
                            color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=16,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.all(40),
                alignment=ft.alignment.center,
            ),
        ]
        self.content_view.update()

    def _handle_item_hover(self, e):
        """Handle hover effect"""
        if e.data == "true":
            e.control.bgcolor = ft.Colors.GREY_100 if not self.is_dark else "#2A2A2A"
        else:
            e.control.bgcolor = None
        e.control.update()

    def build(self):
        # Content view (will be dynamically updated)
        self.content_view = ft.Column(
            controls=[],
            spacing=0,
        )

        # Initialize with main menu
        self._show_main_menu()

        # Bottom sheet
        self.bottom_sheet = ft.BottomSheet(
            content=ft.Container(
                content=self.content_view,
                bgcolor=ft.Colors.WHITE if not self.is_dark else "#1E1E1E",
                border_radius=ft.border_radius.only(top_left=16, top_right=16),
            ),
            open=False,
        )

        return self.bottom_sheet
