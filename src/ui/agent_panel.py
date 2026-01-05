"""Right panel - AI Agent for RAG queries with premium styling."""

import flet as ft
from typing import Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from ..models.schemas import Patient
from ..services.llm import LLMService
from ..services.rag import RAGService
from .components.language_indicator import LanguageIndicator
from .tokens import Colors, Typography, Spacing, Radius, Motion

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AgentPanel:
    """Premium AI Assistant panel for RAG queries."""

    def __init__(
        self,
        on_query: Callable[[str, Callable], None],
        llm: LLMService,
        rag: RAGService,
        is_dark: bool = False
    ):
        self.on_query = on_query
        self.llm = llm
        self.rag = rag
        self.is_dark = is_dark

        self.current_patient: Optional[Patient] = None
        self.messages: List[ChatMessage] = []

        # UI components
        self.chat_list: Optional[ft.ListView] = None
        self.query_field: Optional[ft.TextField] = None
        self.send_btn: Optional[ft.IconButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        self.patient_context: Optional[ft.Text] = None
        self.doc_count: Optional[ft.Text] = None
        self.query_language_indicator: Optional[LanguageIndicator] = None
        self.typing_indicator: Optional[ft.Container] = None

    def build(self) -> ft.Control:
        """Build the premium agent panel UI."""

        # Patient context text
        self.patient_context = ft.Text(
            "No patient selected",
            size=Typography.BODY_SMALL.size,
            color=Colors.NEUTRAL_500 if not self.is_dark else Colors.NEUTRAL_400,
            italic=True,
        )

        self.doc_count = ft.Text(
            "",
            size=Typography.CAPTION.size,
            color=Colors.NEUTRAL_400 if not self.is_dark else Colors.NEUTRAL_500,
        )

        # Clear chat button
        clear_btn = ft.IconButton(
            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
            icon_size=18,
            tooltip="Clear chat (Ctrl+L)",
            icon_color=Colors.NEUTRAL_500 if not self.is_dark else Colors.NEUTRAL_400,
            on_click=lambda e: self.clear_chat(),
            style=ft.ButtonStyle(
                overlay_color=Colors.HOVER_OVERLAY if not self.is_dark else Colors.HOVER_OVERLAY_DARK,
            ),
        )

        # Premium header
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.AUTO_AWESOME,
                                color=Colors.PRIMARY_500 if not self.is_dark else Colors.PRIMARY_300,
                                size=18
                            ),
                            width=32,
                            height=32,
                            bgcolor=Colors.PRIMARY_50 if not self.is_dark else Colors.PRIMARY_900,
                            border_radius=Radius.MD,
                            alignment=ft.alignment.center,
                        ),
                        ft.Text(
                            "AI Assistant",
                            size=Typography.TITLE_SMALL.size,
                            weight=ft.FontWeight.W_600,
                            color=Colors.NEUTRAL_900 if not self.is_dark else Colors.NEUTRAL_100,
                        ),
                    ], spacing=Spacing.XS),
                    clear_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=ft.Column([
                        self.patient_context,
                        self.doc_count,
                    ], spacing=2),
                    padding=ft.padding.only(left=40),  # Align with title
                ),
            ], spacing=Spacing.XS),
            padding=Spacing.MD,
            bgcolor=Colors.PANEL_AGENT_BG if not self.is_dark else Colors.PANEL_AGENT_BG_DARK,
            border=ft.border.only(
                bottom=ft.BorderSide(1, Colors.NEUTRAL_200 if not self.is_dark else Colors.NEUTRAL_700)
            ),
        )

        # Chat history
        self.chat_list = ft.ListView(
            spacing=Spacing.SM,
            padding=Spacing.MD,
            expand=True,
            auto_scroll=True,
        )

        # Typing indicator (hidden by default)
        self.typing_indicator = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.ProgressRing(
                        width=12, height=12, stroke_width=2,
                        color=Colors.PRIMARY_400
                    ),
                ),
                ft.Text(
                    "AI is thinking...",
                    size=Typography.CAPTION.size,
                    color=Colors.NEUTRAL_500,
                    italic=True,
                ),
            ], spacing=Spacing.XS),
            visible=False,
            padding=ft.padding.only(left=Spacing.MD, bottom=Spacing.XS),
        )

        # Welcome message
        self._add_assistant_message(
            "Hello! I can help you query this patient's medical records. "
            "Try asking questions like:\n\n"
            "• What was his last creatinine?\n"
            "• When was his last echo done?\n"
            "• What medications is he on?\n"
            "• Summarize his cardiac history"
        )

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(
            visible=False, width=18, height=18, stroke_width=2,
            color=Colors.PRIMARY_500
        )

        # Premium chat input
        self.query_field = ft.TextField(
            hint_text="Ask about this patient...",
            hint_style=ft.TextStyle(
                size=Typography.BODY_MEDIUM.size,
                color=Colors.NEUTRAL_400,
            ),
            text_size=Typography.BODY_MEDIUM.size,
            border_radius=Radius.XXL,
            border_color=Colors.NEUTRAL_200 if not self.is_dark else Colors.NEUTRAL_600,
            focused_border_color=Colors.PRIMARY_400,
            focused_border_width=2,
            bgcolor=Colors.NEUTRAL_0 if not self.is_dark else Colors.NEUTRAL_800,
            cursor_color=Colors.PRIMARY_500,
            content_padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=3,
            shift_enter=True,
            on_submit=self._on_send_click,
            on_change=self._on_query_change,
        )

        # Language indicator for query
        self.query_language_indicator = LanguageIndicator(visible=True)

        self.send_btn = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color=Colors.NEUTRAL_0,
            bgcolor=Colors.PRIMARY_500,
            tooltip="Send message (Enter)",
            on_click=self._on_send_click,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                animation_duration=Motion.FAST,
            ),
        )

        # Query input with language indicator
        query_with_indicator = ft.Stack([
            self.query_field,
            ft.Container(
                content=self.query_language_indicator,
                right=50,  # Position before send button
                top=8,
            ),
        ])

        # Input container
        input_row = ft.Container(
            content=ft.Row([
                query_with_indicator,
                self.loading_indicator,
                self.send_btn,
            ], spacing=Spacing.XS, vertical_alignment=ft.CrossAxisAlignment.END),
            padding=Spacing.SM,
            bgcolor=Colors.NEUTRAL_0 if not self.is_dark else Colors.NEUTRAL_900,
            border=ft.border.only(
                top=ft.BorderSide(1, Colors.NEUTRAL_200 if not self.is_dark else Colors.NEUTRAL_700)
            ),
        )

        # Quick action chips
        quick_actions = ft.Container(
            content=ft.Row([
                self._quick_chip("Last labs", "What are the most recent lab results?"),
                self._quick_chip("Medications", "List all current medications"),
                self._quick_chip("Summary", "Give me a brief summary of this patient"),
            ], spacing=Spacing.XS, wrap=True),
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XS),
            bgcolor=Colors.NEUTRAL_50 if not self.is_dark else Colors.NEUTRAL_800,
        )

        return ft.Column([
            header,
            ft.Container(
                content=ft.Column([
                    self.chat_list,
                    self.typing_indicator,
                ], spacing=0, expand=True),
                expand=True,
                bgcolor=Colors.NEUTRAL_0 if not self.is_dark else Colors.NEUTRAL_900,
            ),
            quick_actions,
            input_row,
        ], spacing=0, expand=True)

    def _quick_chip(self, label: str, query: str) -> ft.Container:
        """Create a quick action chip."""
        return ft.Container(
            content=ft.Text(
                label,
                size=Typography.LABEL_SMALL.size,
                color=Colors.PRIMARY_600 if not self.is_dark else Colors.PRIMARY_300,
            ),
            bgcolor=Colors.PRIMARY_50 if not self.is_dark else Colors.PRIMARY_900,
            border_radius=Radius.CHIP,
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=Spacing.XXS),
            on_click=lambda e, q=query: self._quick_query(q),
            ink=True,
        )

    def set_patient(self, patient: Patient):
        """Set the current patient context."""
        logger.debug(f"Setting patient context in agent panel: {patient.name} (ID: {patient.id})")
        self.current_patient = patient

        # Update context display
        self.patient_context.value = f"Viewing: {patient.name}"
        self.patient_context.italic = False
        self.patient_context.color = Colors.PRIMARY_600 if not self.is_dark else Colors.PRIMARY_300

        # Get document count
        try:
            doc_count = self.rag.get_patient_document_count(patient.id)
            self.doc_count.value = f"{doc_count} records indexed"
            logger.info(f"Patient {patient.id} has {doc_count} records indexed for RAG")
        except Exception as e:
            logger.error(f"Error getting document count for patient {patient.id}: {e}", exc_info=True)
            doc_count = 0
            self.doc_count.value = "Error loading records"

        # Clear chat history
        self.messages = []
        self.chat_list.controls.clear()
        self._add_assistant_message(
            f"Now viewing records for **{patient.name}**. "
            f"I have access to {doc_count} records. What would you like to know?"
        )

        if self.patient_context.page:
            self.patient_context.page.update()

    def _add_user_message(self, content: str):
        """Add a user message to the chat."""
        msg = ChatMessage(role="user", content=content)
        self.messages.append(msg)
        self._render_message(msg)

    def _add_assistant_message(self, content: str):
        """Add an assistant message to the chat."""
        msg = ChatMessage(role="assistant", content=content)
        self.messages.append(msg)
        self._render_message(msg)

    def _render_message(self, msg: ChatMessage):
        """Render a premium chat bubble."""
        is_user = msg.role == "user"

        # Premium bubble styling
        if is_user:
            bubble = ft.Container(
                content=ft.Text(
                    msg.content,
                    size=Typography.BODY_MEDIUM.size,
                    color=Colors.NEUTRAL_0,
                    selectable=True,
                ),
                bgcolor=Colors.PRIMARY_500,
                padding=ft.padding.all(Spacing.SM),
                border_radius=ft.border_radius.only(
                    top_left=Radius.LG,
                    top_right=Radius.LG,
                    bottom_left=Radius.LG,
                    bottom_right=Radius.XS,
                ),
                shadow=ft.BoxShadow(
                    blur_radius=4,
                    spread_radius=0,
                    offset=ft.Offset(0, 2),
                    color="rgba(26, 115, 232, 0.2)"
                ),
            )
        else:
            bubble = ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.AUTO_AWESOME,
                        size=14,
                        color=Colors.PRIMARY_400,
                    ),
                    ft.Text(
                        msg.content,
                        size=Typography.BODY_MEDIUM.size,
                        color=Colors.NEUTRAL_800 if not self.is_dark else Colors.NEUTRAL_200,
                        selectable=True,
                    ),
                ], spacing=Spacing.XS),
                bgcolor=Colors.NEUTRAL_100 if not self.is_dark else Colors.NEUTRAL_800,
                padding=ft.padding.all(Spacing.SM),
                border_radius=ft.border_radius.only(
                    top_left=Radius.XS,
                    top_right=Radius.LG,
                    bottom_left=Radius.LG,
                    bottom_right=Radius.LG,
                ),
                border=ft.border.all(1, Colors.NEUTRAL_200 if not self.is_dark else Colors.NEUTRAL_700),
            )

        # Timestamp (subtle)
        time_text = ft.Text(
            msg.timestamp.strftime("%H:%M"),
            size=Typography.CAPTION.size - 1,
            color=Colors.NEUTRAL_400,
        )

        row = ft.Column([
            ft.Row(
                [bubble],
                alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            ),
            ft.Row(
                [time_text],
                alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            ),
        ], spacing=2)

        self.chat_list.controls.append(
            ft.Container(
                content=row,
                padding=ft.padding.only(
                    left=Spacing.XL if is_user else 0,
                    right=0 if is_user else Spacing.XL,
                ),
            )
        )

        if self.chat_list.page:
            self.chat_list.update()

    def _on_query_change(self, e):
        """Handle query field change - update language indicator."""
        query_text = e.control.value if hasattr(e.control, 'value') else ""

        # Update language indicator
        if self.query_language_indicator:
            self.query_language_indicator.update_text(query_text)

    def _quick_query(self, query: str):
        """Handle quick action button click."""
        logger.debug(f"Quick query selected: {query}")
        self.query_field.value = query
        # Update language indicator
        if self.query_language_indicator:
            self.query_language_indicator.update_text(query)
        if self.query_field.page:
            self.query_field.page.update()
        self._send_query(query)

    def _on_send_click(self, e):
        """Handle send button click."""
        query = self.query_field.value.strip()
        if not query:
            return
        self._send_query(query)

    def _send_query(self, query: str):
        """Send a query to the RAG system."""
        if not self.current_patient:
            logger.warning("Query attempted without patient context")
            self._add_assistant_message("Please select a patient first.")
            return

        logger.info(f"Sending RAG query from agent panel: {query}")

        # Add user message
        self._add_user_message(query)

        # Clear input
        self.query_field.value = ""

        # Show loading state
        self.loading_indicator.visible = True
        self.send_btn.disabled = True
        self.typing_indicator.visible = True
        if self.loading_indicator.page:
            self.loading_indicator.page.update()

        def callback(success: bool, response: str):
            self.loading_indicator.visible = False
            self.send_btn.disabled = False
            self.typing_indicator.visible = False

            if success:
                logger.debug("RAG query successful, displaying response")
                self._add_assistant_message(response)
            else:
                logger.warning(f"RAG query failed: {response[:100]}")
                self._add_assistant_message(f"Sorry, I encountered an error: {response}")

            if self.loading_indicator.page:
                self.loading_indicator.page.update()

        self.on_query(query, callback)

    def clear_chat(self):
        """Clear the chat history."""
        if self.current_patient:
            self.messages = []
            self.chat_list.controls.clear()

            doc_count = self.rag.get_patient_document_count(self.current_patient.id)

            self._add_assistant_message(
                f"Chat cleared. Still viewing records for **{self.current_patient.name}**. "
                f"I have access to {doc_count} records. What would you like to know?"
            )
        else:
            self.messages = []
            self.chat_list.controls.clear()
            self._add_assistant_message(
                "Hello! I can help you query this patient's medical records. "
                "Try asking questions like:\n\n"
                "• What was his last creatinine?\n"
                "• When was his last echo done?\n"
                "• What medications is he on?\n"
                "• Summarize his cardiac history"
            )

        if self.chat_list.page:
            self.chat_list.page.update()
