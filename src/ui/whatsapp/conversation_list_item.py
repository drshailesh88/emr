"""Conversation list item for WhatsApp-style chat list"""
import flet as ft
from datetime import datetime
from typing import Optional, Callable


class ConversationListItem(ft.UserControl):
    """Individual conversation item in the chat list"""

    def __init__(
        self,
        conversation_id: str,
        patient_id: int,
        patient_name: str,
        patient_phone: str,
        last_message: str,
        last_message_time: datetime,
        unread_count: int = 0,
        is_pinned: bool = False,
        is_online: bool = False,
        is_typing: bool = False,
        last_seen: Optional[datetime] = None,
        avatar_url: Optional[str] = None,
        on_click: Optional[Callable] = None,
        is_selected: bool = False,
        is_dark: bool = False,
    ):
        super().__init__()
        self.conversation_id = conversation_id
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.patient_phone = patient_phone
        self.last_message = last_message
        self.last_message_time = last_message_time
        self.unread_count = unread_count
        self.is_pinned = is_pinned
        self.is_online = is_online
        self.is_typing = is_typing
        self.last_seen = last_seen
        self.avatar_url = avatar_url
        self.on_click = on_click
        self.is_selected = is_selected
        self.is_dark = is_dark

    def _format_time(self) -> str:
        """Format timestamp to relative time"""
        now = datetime.now()
        diff = now - self.last_message_time

        if diff.days == 0:
            # Today - show time
            return self.last_message_time.strftime("%I:%M %p")
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return self.last_message_time.strftime("%A")
        else:
            return self.last_message_time.strftime("%d/%m/%y")

    def _get_avatar(self) -> ft.Control:
        """Get patient avatar (initials or photo)"""
        if self.avatar_url:
            return ft.CircleAvatar(
                foreground_image_url=self.avatar_url,
                radius=25,
            )
        else:
            # Get initials
            initials = "".join([word[0].upper() for word in self.patient_name.split()[:2]])

            # Generate color based on name
            name_hash = sum(ord(c) for c in self.patient_name)
            colors = [
                ft.Colors.BLUE_400,
                ft.Colors.GREEN_400,
                ft.Colors.ORANGE_400,
                ft.Colors.PURPLE_400,
                ft.Colors.TEAL_400,
                ft.Colors.PINK_400,
            ]
            color = colors[name_hash % len(colors)]

            return ft.CircleAvatar(
                content=ft.Text(
                    initials,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                bgcolor=color,
                radius=25,
            )

    def _get_status_indicator(self) -> Optional[ft.Container]:
        """Get online status indicator"""
        if not self.is_online:
            return None

        return ft.Container(
            width=12,
            height=12,
            border_radius=ft.border_radius.all(6),
            bgcolor=ft.Colors.GREEN_400,
            border=ft.border.all(2, ft.Colors.WHITE if not self.is_dark else "#1E1E1E"),
            offset=ft.transform.Offset(0.7, 0.7),
        )

    def _handle_click(self, e):
        """Handle item click"""
        if self.on_click:
            self.on_click(self.conversation_id, self.patient_id)

    def build(self):
        # Background color based on selection
        if self.is_selected:
            bg_color = ft.Colors.BLUE_50 if not self.is_dark else "#1A3A52"
        else:
            bg_color = ft.Colors.WHITE if not self.is_dark else "#1E1E1E"

        # Text colors
        primary_text_color = ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE
        secondary_text_color = ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400
        unread_text_color = ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE

        # Last message display
        if self.is_typing:
            last_msg_display = ft.Row(
                controls=[
                    ft.Icon(
                        name=ft.Icons.MORE_HORIZ_ROUNDED,
                        size=14,
                        color=ft.Colors.BLUE_400,
                    ),
                    ft.Text(
                        "typing...",
                        size=13,
                        color=ft.Colors.BLUE_400,
                        italic=True,
                    ),
                ],
                spacing=4,
            )
        else:
            # Truncate long messages
            truncated_msg = self.last_message[:40] + ("..." if len(self.last_message) > 40 else "")
            last_msg_display = ft.Text(
                truncated_msg,
                size=13,
                color=secondary_text_color if self.unread_count == 0 else unread_text_color,
                weight=ft.FontWeight.NORMAL if self.unread_count == 0 else ft.FontWeight.W_500,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )

        # Build conversation item
        return ft.Container(
            content=ft.Row(
                controls=[
                    # Avatar with online indicator
                    ft.Stack(
                        controls=[
                            self._get_avatar(),
                            self._get_status_indicator() if self.is_online else ft.Container(),
                        ],
                        width=50,
                        height=50,
                    ),
                    # Content (name, message, time)
                    ft.Column(
                        controls=[
                            # Name and time row
                            ft.Row(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                self.patient_name,
                                                size=15,
                                                weight=ft.FontWeight.BOLD if self.unread_count > 0 else ft.FontWeight.W_500,
                                                color=primary_text_color,
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                            ft.Icon(
                                                name=ft.Icons.PUSH_PIN_ROUNDED,
                                                size=14,
                                                color=ft.Colors.GREY_500,
                                            ) if self.is_pinned else ft.Container(),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                    ft.Text(
                                        self._format_time(),
                                        size=12,
                                        color=ft.Colors.BLUE_400 if self.unread_count > 0 else secondary_text_color,
                                        weight=ft.FontWeight.BOLD if self.unread_count > 0 else ft.FontWeight.NORMAL,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            # Message and badge row
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=last_msg_display,
                                        expand=True,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            str(self.unread_count),
                                            size=11,
                                            color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        bgcolor=ft.Colors.GREEN_500,
                                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                        border_radius=ft.border_radius.all(10),
                                        visible=self.unread_count > 0,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=bg_color,
            on_click=self._handle_click,
            on_hover=lambda e: self._handle_hover(e),
            border=ft.border.only(
                bottom=ft.BorderSide(1, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
            ),
        )

    def _handle_hover(self, e):
        """Handle hover effect"""
        if e.data == "true" and not self.is_selected:
            e.control.bgcolor = ft.Colors.GREY_100 if not self.is_dark else "#2A2A2A"
        elif not self.is_selected:
            e.control.bgcolor = ft.Colors.WHITE if not self.is_dark else "#1E1E1E"
        e.control.update()
