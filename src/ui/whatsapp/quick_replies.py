"""Quick replies dropdown for common responses"""
import flet as ft
from typing import Callable, Optional, List, Dict


class QuickReplies(ft.UserControl):
    """Quick reply picker with predefined responses"""

    # Predefined quick replies in English and Hindi
    DEFAULT_REPLIES = [
        {
            "id": "appointment_confirmed",
            "text_en": "Your appointment is confirmed. See you soon!",
            "text_hi": "आपकी अपॉइंटमेंट कन्फर्म हो गई है। जल्द मिलेंगे!",
            "category": "Appointments",
        },
        {
            "id": "take_medicines",
            "text_en": "Please take your medicines regularly as prescribed.",
            "text_hi": "कृपया अपनी दवाएं नियमित रूप से लें।",
            "category": "Medication",
        },
        {
            "id": "follow_up",
            "text_en": "Please come for follow-up as scheduled.",
            "text_hi": "कृपया समय पर फॉलो-अप के लिए आएं।",
            "category": "Follow-up",
        },
        {
            "id": "reports_normal",
            "text_en": "Your reports are normal. Continue with your current medications.",
            "text_hi": "आपकी रिपोर्ट सामान्य है। अपनी दवाएं जारी रखें।",
            "category": "Reports",
        },
        {
            "id": "visit_clinic",
            "text_en": "Please visit the clinic for a physical examination.",
            "text_hi": "कृपया जांच के लिए क्लिनिक आएं।",
            "category": "Consultation",
        },
        {
            "id": "prescription_sent",
            "text_en": "I have sent your prescription. Please check the attachment.",
            "text_hi": "मैंने आपका प्रिस्क्रिप्शन भेज दिया है। कृपया अटैचमेंट देखें।",
            "category": "Medication",
        },
        {
            "id": "emergency_call",
            "text_en": "This seems urgent. Please call the clinic immediately.",
            "text_hi": "यह जरूरी लगता है। कृपया तुरंत क्लिनिक पर कॉल करें।",
            "category": "Emergency",
        },
        {
            "id": "stay_hydrated",
            "text_en": "Drink plenty of water and rest. Contact if symptoms worsen.",
            "text_hi": "खूब पानी पिएं और आराम करें। लक्षण बढ़ने पर संपर्क करें।",
            "category": "Advice",
        },
        {
            "id": "test_required",
            "text_en": "Please get the recommended tests done and share the reports.",
            "text_hi": "कृपया सुझाई गई जांचें करवाएं और रिपोर्ट शेयर करें।",
            "category": "Investigation",
        },
        {
            "id": "diet_control",
            "text_en": "Follow the diet plan and avoid oily/spicy foods.",
            "text_hi": "डाइट प्लान फॉलो करें और तैलीय/मसालेदार खाना avoid करें।",
            "category": "Advice",
        },
    ]

    def __init__(
        self,
        on_reply_selected: Callable[[str], None],
        custom_replies: Optional[List[Dict]] = None,
        language: str = "en",  # en or hi
        is_dark: bool = False,
    ):
        super().__init__()
        self.on_reply_selected = on_reply_selected
        self.custom_replies = custom_replies or []
        self.language = language
        self.is_dark = is_dark

        self.search_field = None
        self.replies_list = None
        self.category_filter = None

    def _get_reply_text(self, reply: Dict) -> str:
        """Get reply text in selected language"""
        if self.language == "hi" and "text_hi" in reply:
            return reply["text_hi"]
        return reply.get("text_en", "")

    def _filter_replies(self, search_text: str = "", category: str = "All") -> List[Dict]:
        """Filter replies based on search and category"""
        all_replies = self.DEFAULT_REPLIES + self.custom_replies

        filtered = all_replies

        # Filter by category
        if category != "All":
            filtered = [r for r in filtered if r.get("category") == category]

        # Filter by search text
        if search_text:
            search_lower = search_text.lower()
            filtered = [
                r for r in filtered
                if search_lower in self._get_reply_text(r).lower()
                or search_lower in r.get("category", "").lower()
            ]

        return filtered

    def _handle_search(self, e):
        """Handle search input"""
        self._update_replies_list()

    def _handle_category_change(self, e):
        """Handle category filter change"""
        self._update_replies_list()

    def _update_replies_list(self):
        """Update the replies list based on filters"""
        if not self.replies_list or not self.search_field or not self.category_filter:
            return

        search_text = self.search_field.value or ""
        category = self.category_filter.value or "All"

        filtered_replies = self._filter_replies(search_text, category)

        # Build reply items
        reply_items = []
        for reply in filtered_replies:
            reply_text = self._get_reply_text(reply)

            reply_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        reply_text,
                                        size=14,
                                        color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        reply.get("category", "General"),
                                        size=11,
                                        color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SEND_ROUNDED,
                                icon_size=18,
                                tooltip="Send",
                                on_click=lambda e, text=reply_text: self._send_reply(text),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.all(12),
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                    ),
                    on_click=lambda e, text=reply_text: self._send_reply(text),
                    on_hover=self._handle_item_hover,
                )
            )

        if not reply_items:
            reply_items.append(
                ft.Container(
                    content=ft.Text(
                        "No quick replies found",
                        size=14,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=ft.padding.all(20),
                    alignment=ft.alignment.center,
                )
            )

        self.replies_list.controls = reply_items
        self.replies_list.update()

    def _send_reply(self, text: str):
        """Send the selected quick reply"""
        if self.on_reply_selected:
            self.on_reply_selected(text)

    def _handle_item_hover(self, e):
        """Handle hover effect on reply items"""
        if e.data == "true":
            e.control.bgcolor = ft.Colors.GREY_100 if not self.is_dark else "#2A2A2A"
        else:
            e.control.bgcolor = None
        e.control.update()

    def _get_categories(self) -> List[str]:
        """Get all unique categories"""
        all_replies = self.DEFAULT_REPLIES + self.custom_replies
        categories = set(reply.get("category", "General") for reply in all_replies)
        return ["All"] + sorted(list(categories))

    def build(self):
        # Search field
        self.search_field = ft.TextField(
            hint_text="Search quick replies...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border_color=ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700,
            focused_border_color=ft.Colors.BLUE_400,
            dense=True,
            on_change=self._handle_search,
        )

        # Category filter
        categories = self._get_categories()
        self.category_filter = ft.Dropdown(
            options=[ft.dropdown.Option(cat) for cat in categories],
            value="All",
            width=150,
            dense=True,
            on_change=self._handle_category_change,
        )

        # Language toggle
        language_toggle = ft.Row(
            controls=[
                ft.Text("Language:", size=12, color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400),
                ft.SegmentedButton(
                    selected={"en"} if self.language == "en" else {"hi"},
                    allow_empty_selection=False,
                    segments=[
                        ft.Segment(
                            value="en",
                            label=ft.Text("English", size=12),
                        ),
                        ft.Segment(
                            value="hi",
                            label=ft.Text("हिन्दी", size=12),
                        ),
                    ],
                    on_change=self._handle_language_change,
                ),
            ],
            spacing=8,
        )

        # Replies list (initially empty, will be populated)
        self.replies_list = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Initial population
        self._update_replies_list()

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.QUICK_REPLY_ROUNDED, size=20),
                                ft.Text(
                                    "Quick Replies",
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
                    # Filters
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self.search_field,
                                ft.Row(
                                    controls=[
                                        ft.Text("Category:", size=12),
                                        self.category_filter,
                                        language_toggle,
                                    ],
                                    spacing=12,
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=ft.padding.all(16),
                        border=ft.border.only(
                            bottom=ft.BorderSide(1, ft.Colors.GREY_200 if not self.is_dark else ft.Colors.GREY_800)
                        ),
                    ),
                    # Replies list
                    ft.Container(
                        content=self.replies_list,
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            bgcolor=ft.Colors.WHITE if not self.is_dark else "#1E1E1E",
            border_radius=ft.border_radius.all(8),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            width=400,
            height=500,
        )

    def _handle_language_change(self, e):
        """Handle language toggle"""
        selected = list(e.control.selected)[0]
        self.language = selected
        self._update_replies_list()
