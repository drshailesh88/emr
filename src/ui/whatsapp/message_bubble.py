"""WhatsApp-style message bubble component"""
import flet as ft
from datetime import datetime
from typing import Optional, Callable


class MessageBubble(ft.UserControl):
    """Individual message bubble with WhatsApp-style design"""

    def __init__(
        self,
        message_id: str,
        content: str,
        timestamp: datetime,
        is_outgoing: bool,
        status: str = "sent",  # sent, delivered, read, failed
        message_type: str = "text",  # text, image, document, reply
        reply_to: Optional[dict] = None,
        attachment_url: Optional[str] = None,
        attachment_name: Optional[str] = None,
        is_starred: bool = False,
        on_reply: Optional[Callable] = None,
        on_copy: Optional[Callable] = None,
        on_star: Optional[Callable] = None,
        is_dark: bool = False
    ):
        super().__init__()
        self.message_id = message_id
        self.content = content
        self.timestamp = timestamp
        self.is_outgoing = is_outgoing
        self.status = status
        self.message_type = message_type
        self.reply_to = reply_to
        self.attachment_url = attachment_url
        self.attachment_name = attachment_name
        self.is_starred = is_starred
        self.on_reply = on_reply
        self.on_copy = on_copy
        self.on_star = on_star
        self.is_dark = is_dark

        self.menu_anchor = None
        self.bubble_container = None

    def _format_time(self) -> str:
        """Format timestamp for display"""
        return self.timestamp.strftime("%I:%M %p")

    def _get_status_icon(self) -> Optional[ft.Icon]:
        """Get status icon (checkmarks) for outgoing messages"""
        if not self.is_outgoing:
            return None

        if self.status == "read":
            return ft.Icon(
                name=ft.Icons.DONE_ALL_ROUNDED,
                size=16,
                color=ft.Colors.BLUE_400
            )
        elif self.status == "delivered":
            return ft.Icon(
                name=ft.Icons.DONE_ALL_ROUNDED,
                size=16,
                color=ft.Colors.GREY_500
            )
        elif self.status == "sent":
            return ft.Icon(
                name=ft.Icons.DONE_ROUNDED,
                size=16,
                color=ft.Colors.GREY_500
            )
        elif self.status == "failed":
            return ft.Icon(
                name=ft.Icons.ERROR_OUTLINE_ROUNDED,
                size=16,
                color=ft.Colors.RED_400
            )
        return None

    def _handle_long_press(self, e):
        """Show context menu on long press"""
        if self.menu_anchor:
            self.menu_anchor.open = True
            self.menu_anchor.update()

    def _handle_reply(self, e):
        """Handle reply action"""
        if self.menu_anchor:
            self.menu_anchor.close()
        if self.on_reply:
            self.on_reply(self.message_id, self.content)

    def _handle_copy(self, e):
        """Handle copy action"""
        if self.menu_anchor:
            self.menu_anchor.close()
        if self.on_copy:
            self.on_copy(self.content)
        # Also copy to clipboard
        if self.page:
            self.page.set_clipboard(self.content)
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Message copied"))
            )

    def _handle_star(self, e):
        """Handle star/unstar action"""
        if self.menu_anchor:
            self.menu_anchor.close()
        self.is_starred = not self.is_starred
        if self.on_star:
            self.on_star(self.message_id, self.is_starred)
        self.update()

    def _build_reply_preview(self) -> Optional[ft.Container]:
        """Build reply-to preview"""
        if not self.reply_to:
            return None

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        self.reply_to.get("sender", "Unknown"),
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_400 if not self.is_dark else ft.Colors.BLUE_300,
                    ),
                    ft.Text(
                        self.reply_to.get("content", "")[:50] + ("..." if len(self.reply_to.get("content", "")) > 50 else ""),
                        size=12,
                        color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=2,
            ),
            padding=ft.padding.all(8),
            margin=ft.margin.only(bottom=4),
            border_radius=ft.border_radius.all(4),
            bgcolor=ft.Colors.BLACK12 if not self.is_dark else ft.Colors.WHITE12,
            border=ft.border.only(
                left=ft.BorderSide(3, ft.Colors.BLUE_400 if not self.is_dark else ft.Colors.BLUE_300)
            )
        )

    def _build_attachment(self) -> Optional[ft.Container]:
        """Build attachment preview"""
        if self.message_type == "text" or not self.attachment_url:
            return None

        if self.message_type == "image":
            return ft.Container(
                content=ft.Image(
                    src=self.attachment_url,
                    width=250,
                    height=200,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(8),
                ),
                margin=ft.margin.only(bottom=4)
            )
        elif self.message_type == "document":
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            name=ft.Icons.INSERT_DRIVE_FILE_ROUNDED,
                            size=40,
                            color=ft.Colors.BLUE_400
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    self.attachment_name or "Document",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    "PDF Document",
                                    size=12,
                                    color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DOWNLOAD_ROUNDED,
                            icon_size=20,
                            tooltip="Download"
                        )
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.START,
                ),
                padding=ft.padding.all(10),
                margin=ft.margin.only(bottom=4),
                border_radius=ft.border_radius.all(8),
                bgcolor=ft.Colors.BLACK12 if not self.is_dark else ft.Colors.WHITE12,
            )

        return None

    def build(self):
        # Bubble colors
        if self.is_outgoing:
            bubble_color = "#DCF8C6" if not self.is_dark else "#056162"
            text_color = ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE
        else:
            bubble_color = ft.Colors.WHITE if not self.is_dark else "#1E2428"
            text_color = ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE

        # Build message content
        content_controls = []

        # Add reply preview if exists
        reply_preview = self._build_reply_preview()
        if reply_preview:
            content_controls.append(reply_preview)

        # Add attachment if exists
        attachment = self._build_attachment()
        if attachment:
            content_controls.append(attachment)

        # Add message text
        if self.content:
            content_controls.append(
                ft.Text(
                    self.content,
                    size=14,
                    color=text_color,
                    selectable=True,
                )
            )

        # Add timestamp and status row
        status_row_controls = []

        if self.is_starred:
            status_row_controls.append(
                ft.Icon(
                    name=ft.Icons.STAR,
                    size=12,
                    color=ft.Colors.YELLOW_700
                )
            )

        status_row_controls.append(
            ft.Text(
                self._format_time(),
                size=11,
                color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
            )
        )

        status_icon = self._get_status_icon()
        if status_icon:
            status_row_controls.append(status_icon)

        content_controls.append(
            ft.Row(
                controls=status_row_controls,
                spacing=4,
                alignment=ft.MainAxisAlignment.END,
            )
        )

        # Create bubble container
        self.bubble_container = ft.Container(
            content=ft.Column(
                controls=content_controls,
                spacing=4,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=ft.border_radius.all(8),
            bgcolor=bubble_color,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=2,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 1),
            ),
        )

        # Create context menu
        self.menu_anchor = ft.MenuBar(
            controls=[
                ft.SubmenuButton(
                    content=self.bubble_container,
                    on_long_press=self._handle_long_press,
                    on_hover=None,
                    menu_style=ft.MenuStyle(
                        bgcolor=ft.Colors.WHITE if not self.is_dark else "#2D2D2D",
                        elevation=8,
                    ),
                    controls=[
                        ft.MenuItemButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.REPLY_ROUNDED, size=18),
                                ft.Text("Reply", size=14),
                            ], spacing=10),
                            on_click=self._handle_reply,
                            style=ft.ButtonStyle(
                                padding=ft.padding.all(12),
                            )
                        ),
                        ft.MenuItemButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.COPY_ROUNDED, size=18),
                                ft.Text("Copy", size=14),
                            ], spacing=10),
                            on_click=self._handle_copy,
                            style=ft.ButtonStyle(
                                padding=ft.padding.all(12),
                            )
                        ),
                        ft.MenuItemButton(
                            content=ft.Row([
                                ft.Icon(
                                    ft.Icons.STAR if not self.is_starred else ft.Icons.STAR_BORDER,
                                    size=18
                                ),
                                ft.Text("Unstar" if self.is_starred else "Star", size=14),
                            ], spacing=10),
                            on_click=self._handle_star,
                            style=ft.ButtonStyle(
                                padding=ft.padding.all(12),
                            )
                        ),
                    ]
                )
            ]
        )

        # Wrap in alignment container
        return ft.Container(
            content=ft.Row(
                controls=[self.menu_anchor],
                alignment=ft.MainAxisAlignment.END if self.is_outgoing else ft.MainAxisAlignment.START,
            ),
            margin=ft.margin.symmetric(vertical=2, horizontal=8),
        )
