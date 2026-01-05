"""WhatsApp-style conversation panel for patient messaging"""
import flet as ft
from datetime import datetime, date
from typing import Optional, Callable, List, Dict
import asyncio

from .conversation_list_item import ConversationListItem
from .message_bubble import MessageBubble
from .quick_replies import QuickReplies
from .ai_suggestions import AISuggestions, AISuggestion
from .escalation_banner import EscalationBanner
from .attachment_picker import AttachmentPicker


class WhatsAppConversationPanel(ft.UserControl):
    """Main WhatsApp-style conversation interface"""

    def __init__(
        self,
        db_service,
        whatsapp_client,
        conversation_handler,
        on_patient_selected: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        super().__init__()
        self.db_service = db_service
        self.whatsapp_client = whatsapp_client
        self.conversation_handler = conversation_handler
        self.on_patient_selected = on_patient_selected
        self.is_dark = is_dark

        # State
        self.conversations: List[Dict] = []
        self.current_conversation_id: Optional[str] = None
        self.current_patient_id: Optional[int] = None
        self.current_patient: Optional[Dict] = None
        self.messages: List[Dict] = []
        self.filter_mode = "all"  # all, unread, starred

        # UI Components
        self.conversation_list = None
        self.chat_view = None
        self.message_input = None
        self.search_field = None
        self.filter_tabs = None
        self.send_button = None
        self.attach_button = None
        self.quick_reply_button = None
        self.ai_suggestions_panel = None
        self.escalation_banner_container = None
        self.messages_column = None
        self.chat_header = None
        self.quick_replies_panel = None
        self.attachment_picker = None

    def load_conversations(self):
        """Load all conversations from database"""
        # Mock data - would load from database
        self.conversations = [
            {
                "id": "conv_001",
                "patient_id": 1,
                "patient_name": "Rajesh Kumar",
                "patient_phone": "9876543210",
                "last_message": "Thank you doctor, I'm feeling much better now",
                "last_message_time": datetime.now(),
                "unread_count": 0,
                "is_pinned": False,
                "is_online": False,
                "is_typing": False,
            },
            {
                "id": "conv_002",
                "patient_id": 2,
                "patient_name": "Priya Sharma",
                "patient_phone": "9876543211",
                "last_message": "Doctor, I have severe chest pain. Please help!",
                "last_message_time": datetime.now(),
                "unread_count": 3,
                "is_pinned": True,
                "is_online": True,
                "is_typing": False,
            },
            {
                "id": "conv_003",
                "patient_id": 3,
                "patient_name": "Amit Patel",
                "patient_phone": "9876543212",
                "last_message": "Can I get my prescription?",
                "last_message_time": datetime.now(),
                "unread_count": 1,
                "is_pinned": False,
                "is_online": False,
                "is_typing": True,
            },
        ]
        self._update_conversation_list()

    def _update_conversation_list(self):
        """Update the conversation list view"""
        if not self.conversation_list:
            return

        # Filter conversations
        filtered = self.conversations

        if self.filter_mode == "unread":
            filtered = [c for c in filtered if c["unread_count"] > 0]
        elif self.filter_mode == "starred":
            filtered = [c for c in filtered if c["is_pinned"]]

        # Sort: pinned first, then by time
        filtered.sort(key=lambda c: (not c["is_pinned"], c["last_message_time"]), reverse=True)

        # Build conversation items
        conversation_items = []
        for conv in filtered:
            conversation_items.append(
                ConversationListItem(
                    conversation_id=conv["id"],
                    patient_id=conv["patient_id"],
                    patient_name=conv["patient_name"],
                    patient_phone=conv["patient_phone"],
                    last_message=conv["last_message"],
                    last_message_time=conv["last_message_time"],
                    unread_count=conv["unread_count"],
                    is_pinned=conv["is_pinned"],
                    is_online=conv["is_online"],
                    is_typing=conv["is_typing"],
                    on_click=self._handle_conversation_click,
                    is_selected=conv["id"] == self.current_conversation_id,
                    is_dark=self.is_dark,
                )
            )

        if not conversation_items:
            conversation_items.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
                                size=64,
                                color=ft.Colors.GREY_400,
                            ),
                            ft.Text(
                                "No conversations",
                                size=14,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        spacing=16,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.all(40),
                    alignment=ft.alignment.center,
                )
            )

        self.conversation_list.controls = conversation_items
        self.conversation_list.update()

    def _handle_conversation_click(self, conversation_id: str, patient_id: int):
        """Handle conversation selection"""
        self.current_conversation_id = conversation_id
        self.current_patient_id = patient_id

        # Get patient details
        # Mock - would load from database
        self.current_patient = {
            "id": patient_id,
            "name": next((c["patient_name"] for c in self.conversations if c["id"] == conversation_id), "Unknown"),
            "phone": next((c["patient_phone"] for c in self.conversations if c["id"] == conversation_id), ""),
            "is_online": next((c["is_online"] for c in self.conversations if c["id"] == conversation_id), False),
            "last_seen": datetime.now(),
        }

        # Load messages for this conversation
        self._load_messages()

        # Mark conversation as read
        self._mark_conversation_read(conversation_id)

        # Update UI
        self._update_conversation_list()
        self._update_chat_header()
        self._update_messages_view()

        # Notify parent
        if self.on_patient_selected:
            self.on_patient_selected(patient_id)

    def _load_messages(self):
        """Load messages for current conversation"""
        # Mock data - would load from database
        self.messages = [
            {
                "id": "msg_001",
                "content": "Hello doctor, I need to book an appointment",
                "timestamp": datetime.now(),
                "is_outgoing": False,
                "status": "read",
                "type": "text",
            },
            {
                "id": "msg_002",
                "content": "Sure! Let me check available slots for you.",
                "timestamp": datetime.now(),
                "is_outgoing": True,
                "status": "read",
                "type": "text",
            },
            {
                "id": "msg_003",
                "content": "I'm available tomorrow at 10 AM",
                "timestamp": datetime.now(),
                "is_outgoing": False,
                "status": "read",
                "type": "text",
            },
            {
                "id": "msg_004",
                "content": "Perfect! I've booked your appointment for tomorrow at 10 AM.",
                "timestamp": datetime.now(),
                "is_outgoing": True,
                "status": "delivered",
                "type": "text",
            },
        ]

    def _mark_conversation_read(self, conversation_id: str):
        """Mark conversation as read"""
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                conv["unread_count"] = 0
                break

    def _update_chat_header(self):
        """Update the chat header"""
        if not self.chat_header or not self.current_patient:
            return

        # Status text
        if self.current_patient.get("is_online"):
            status_text = "online"
            status_color = ft.Colors.GREEN_500
        else:
            last_seen = self.current_patient.get("last_seen")
            if last_seen:
                status_text = f"last seen {self._format_last_seen(last_seen)}"
            else:
                status_text = "offline"
            status_color = ft.Colors.GREY_500

        self.chat_header.content = ft.Row(
            controls=[
                # Patient info
                ft.Row(
                    controls=[
                        # Avatar
                        ft.CircleAvatar(
                            content=ft.Text(
                                "".join([word[0].upper() for word in self.current_patient["name"].split()[:2]]),
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            bgcolor=ft.Colors.BLUE_400,
                            radius=20,
                        ),
                        # Name and status
                        ft.Column(
                            controls=[
                                ft.Text(
                                    self.current_patient["name"],
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    status_text,
                                    size=12,
                                    color=status_color,
                                ),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=12,
                    expand=True,
                ),
                # Actions
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CALL_ROUNDED,
                            tooltip="Call patient",
                            on_click=self._handle_call_patient,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.VIDEOCAM_ROUNDED,
                            tooltip="Video call",
                            on_click=self._handle_video_call,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.MORE_VERT_ROUNDED,
                            tooltip="More options",
                            on_click=self._show_chat_options,
                        ),
                    ],
                    spacing=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.chat_header.update()

    def _format_last_seen(self, last_seen: datetime) -> str:
        """Format last seen timestamp"""
        diff = datetime.now() - last_seen
        if diff.seconds < 60:
            return "just now"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}m ago"
        elif diff.seconds < 86400:
            return f"{diff.seconds // 3600}h ago"
        else:
            return last_seen.strftime("%d %b at %I:%M %p")

    def _update_messages_view(self):
        """Update the messages view"""
        if not self.messages_column:
            return

        message_bubbles = []

        # Group messages by date
        current_date = None
        for msg in self.messages:
            msg_date = msg["timestamp"].date()

            # Add date separator if date changed
            if current_date != msg_date:
                current_date = msg_date
                message_bubbles.append(
                    ft.Container(
                        content=ft.Text(
                            self._format_date_separator(msg_date),
                            size=12,
                            color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                            weight=ft.FontWeight.BOLD,
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=ft.Colors.GREY_200 if not self.is_dark else "#2A2A2A",
                        border_radius=ft.border_radius.all(12),
                        alignment=ft.alignment.center,
                        margin=ft.margin.symmetric(vertical=8, horizontal=80),
                    )
                )

            # Add message bubble
            message_bubbles.append(
                MessageBubble(
                    message_id=msg["id"],
                    content=msg["content"],
                    timestamp=msg["timestamp"],
                    is_outgoing=msg["is_outgoing"],
                    status=msg.get("status", "sent"),
                    message_type=msg.get("type", "text"),
                    on_reply=self._handle_reply_to_message,
                    on_copy=self._handle_copy_message,
                    on_star=self._handle_star_message,
                    is_dark=self.is_dark,
                )
            )

        self.messages_column.controls = message_bubbles
        self.messages_column.update()

        # Scroll to bottom
        if self.chat_view:
            self.chat_view.scroll_to(offset=-1, duration=300)

    def _format_date_separator(self, msg_date: date) -> str:
        """Format date for separator"""
        today = date.today()
        if msg_date == today:
            return "TODAY"
        elif msg_date == today.replace(day=today.day - 1):
            return "YESTERDAY"
        else:
            return msg_date.strftime("%d %B %Y").upper()

    def _handle_send_message(self, e):
        """Handle sending a message"""
        message_text = self.message_input.value.strip()
        if not message_text:
            return

        # Add message to view
        new_message = {
            "id": f"msg_{len(self.messages) + 1:03d}",
            "content": message_text,
            "timestamp": datetime.now(),
            "is_outgoing": True,
            "status": "sent",
            "type": "text",
        }
        self.messages.append(new_message)

        # Clear input
        self.message_input.value = ""
        self.message_input.update()

        # Update view
        self._update_messages_view()

        # Send via WhatsApp API (async)
        asyncio.create_task(self._send_to_whatsapp(message_text))

    async def _send_to_whatsapp(self, message: str):
        """Send message via WhatsApp API"""
        if not self.current_patient:
            return

        try:
            result = await self.whatsapp_client.send_text(
                to=self.current_patient["phone"],
                message=message
            )
            # Update message status based on result
            if self.messages:
                self.messages[-1]["status"] = result.status.value
                self._update_messages_view()
        except Exception as e:
            print(f"Error sending message: {e}")
            if self.messages:
                self.messages[-1]["status"] = "failed"
                self._update_messages_view()

    def _handle_search(self, e):
        """Handle conversation search"""
        search_text = e.control.value.lower()
        if not search_text:
            self._update_conversation_list()
            return

        # Filter conversations by search text
        filtered = [
            c for c in self.conversations
            if search_text in c["patient_name"].lower()
            or search_text in c["last_message"].lower()
            or search_text in c["patient_phone"]
        ]

        # Update list with filtered results
        # (simplified - would update conversation_list directly)
        pass

    def _handle_filter_change(self, e):
        """Handle filter tab change"""
        selected_index = e.control.selected_index
        filters = ["all", "unread", "starred"]
        self.filter_mode = filters[selected_index]
        self._update_conversation_list()

    def _handle_attach_click(self, e):
        """Handle attach button click"""
        if self.attachment_picker:
            self.attachment_picker.show()

    def _handle_quick_reply_click(self, e):
        """Handle quick reply button click"""
        # Show quick replies panel
        if not self.quick_replies_panel:
            self.quick_replies_panel = QuickReplies(
                on_reply_selected=self._insert_quick_reply,
                is_dark=self.is_dark,
            )

        # Show in dialog
        dialog = ft.AlertDialog(
            content=self.quick_replies_panel,
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(e)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _close_dialog(self, e):
        """Close current dialog"""
        if self.page and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def _insert_quick_reply(self, text: str):
        """Insert quick reply into message input"""
        if self.message_input:
            self.message_input.value = text
            self.message_input.update()
            self.message_input.focus()

        # Close dialog
        if self.page and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def _handle_reply_to_message(self, message_id: str, content: str):
        """Handle replying to a specific message"""
        # Implementation would show reply UI
        pass

    def _handle_copy_message(self, content: str):
        """Handle copying message"""
        pass

    def _handle_star_message(self, message_id: str, is_starred: bool):
        """Handle starring/unstarring message"""
        pass

    def _handle_call_patient(self, e):
        """Handle calling patient"""
        pass

    def _handle_video_call(self, e):
        """Handle video call"""
        pass

    def _show_chat_options(self, e):
        """Show chat options menu"""
        pass

    def build(self):
        # Conversation list (left side)
        self.search_field = ft.TextField(
            hint_text="Search conversations...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border_color=ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700,
            dense=True,
            on_change=self._handle_search,
        )

        self.filter_tabs = ft.Tabs(
            selected_index=0,
            on_change=self._handle_filter_change,
            tabs=[
                ft.Tab(text="All", icon=ft.Icons.CHAT_ROUNDED),
                ft.Tab(text="Unread", icon=ft.Icons.MARK_CHAT_UNREAD_ROUNDED),
                ft.Tab(text="Starred", icon=ft.Icons.STAR_ROUNDED),
            ],
        )

        self.conversation_list = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        conversations_panel = ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Text(
                            "Messages",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        padding=ft.padding.all(16),
                    ),
                    # Search
                    ft.Container(
                        content=self.search_field,
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    ),
                    # Filter tabs
                    ft.Container(
                        content=self.filter_tabs,
                        padding=ft.padding.symmetric(horizontal=16),
                    ),
                    # Conversations list
                    ft.Container(
                        content=self.conversation_list,
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            width=350,
            bgcolor=ft.Colors.WHITE if not self.is_dark else "#1E1E1E",
            border=ft.border.only(
                right=ft.BorderSide(1, ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_800)
            ),
        )

        # Chat view (right side)
        self.chat_header = ft.Container(
            padding=ft.padding.all(16),
            border=ft.border.only(
                bottom=ft.BorderSide(1, ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_800)
            ),
            bgcolor=ft.Colors.WHITE if not self.is_dark else "#1E1E1E",
        )

        self.messages_column = ft.Column(
            controls=[],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.chat_view = ft.Container(
            content=self.messages_column,
            expand=True,
            padding=ft.padding.symmetric(vertical=16),
            bgcolor=ft.Colors.GREY_50 if not self.is_dark else "#0D1418",
        )

        # Escalation banner container
        self.escalation_banner_container = ft.Container(
            visible=False,
            padding=ft.padding.all(12),
        )

        # AI suggestions panel
        self.ai_suggestions_panel = AISuggestions(
            on_suggestion_selected=self._insert_quick_reply,
            is_dark=self.is_dark,
        )

        # Message input area
        self.message_input = ft.TextField(
            hint_text="Type a message...",
            multiline=True,
            min_lines=1,
            max_lines=4,
            shift_enter=True,
            border_color=ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700,
            on_submit=self._handle_send_message,
            expand=True,
        )

        self.attach_button = ft.IconButton(
            icon=ft.Icons.ATTACH_FILE_ROUNDED,
            tooltip="Attach file",
            on_click=self._handle_attach_click,
        )

        self.quick_reply_button = ft.IconButton(
            icon=ft.Icons.QUICK_REPLY_ROUNDED,
            tooltip="Quick replies",
            on_click=self._handle_quick_reply_click,
        )

        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            tooltip="Send message",
            icon_color=ft.Colors.BLUE_600,
            on_click=self._handle_send_message,
        )

        input_area = ft.Container(
            content=ft.Row(
                controls=[
                    self.attach_button,
                    self.message_input,
                    self.quick_reply_button,
                    self.send_button,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            padding=ft.padding.all(16),
            border=ft.border.only(
                top=ft.BorderSide(1, ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_800)
            ),
            bgcolor=ft.Colors.WHITE if not self.is_dark else "#1E1E1E",
        )

        chat_panel = ft.Container(
            content=ft.Column(
                controls=[
                    self.chat_header,
                    self.escalation_banner_container,
                    self.chat_view,
                    input_area,
                ],
                spacing=0,
            ),
            expand=True,
        )

        # Attachment picker (hidden by default)
        if self.current_patient_id:
            self.attachment_picker = AttachmentPicker(
                patient_id=self.current_patient_id,
                patient_name=self.current_patient["name"] if self.current_patient else "",
                on_send_prescription=lambda rx_id: print(f"Send prescription {rx_id}"),
                on_send_lab_report=lambda rep_id: print(f"Send lab report {rep_id}"),
                on_send_document=lambda path: print(f"Send document {path}"),
                on_send_appointment=lambda apt: print(f"Send appointment {apt}"),
                on_send_location=lambda: print("Send location"),
                get_recent_prescriptions=lambda pid: [],
                get_recent_lab_reports=lambda pid: [],
                is_dark=self.is_dark,
            )

        # Load initial data
        self.load_conversations()

        return ft.Row(
            controls=[
                conversations_panel,
                chat_panel,
            ],
            spacing=0,
            expand=True,
        )
