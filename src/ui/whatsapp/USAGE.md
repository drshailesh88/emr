# WhatsApp Conversation UI - Usage Guide

## Overview

This module provides a complete WhatsApp-style conversation interface for patient messaging in the DocAssist EMR application.

## Components

### 1. WhatsAppConversationPanel (Main Component)

The main panel that integrates all conversation features.

```python
from src.ui.whatsapp import WhatsAppConversationPanel
from src.services.database import DatabaseService
from src.services.whatsapp.client import WhatsAppClient
from src.services.whatsapp.conversation_handler import ConversationHandler

# Initialize services
db_service = DatabaseService()
whatsapp_client = WhatsAppClient()
conversation_handler = ConversationHandler(llm_service, db_service, whatsapp_client)

# Create conversation panel
conversation_panel = WhatsAppConversationPanel(
    db_service=db_service,
    whatsapp_client=whatsapp_client,
    conversation_handler=conversation_handler,
    on_patient_selected=lambda patient_id: print(f"Selected patient: {patient_id}"),
    is_dark=False  # Use dark mode
)

# Add to your Flet page
page.add(conversation_panel)
```

### 2. Individual Components

You can also use individual components separately:

#### Message Bubble

```python
from src.ui.whatsapp import MessageBubble
from datetime import datetime

message = MessageBubble(
    message_id="msg_001",
    content="Hello doctor, I need help",
    timestamp=datetime.now(),
    is_outgoing=False,  # Incoming message
    status="read",
    message_type="text",
    on_reply=lambda msg_id, content: print(f"Reply to: {content}"),
    on_copy=lambda content: print(f"Copied: {content}"),
    on_star=lambda msg_id, starred: print(f"Star: {starred}"),
    is_dark=False
)
```

#### Conversation List Item

```python
from src.ui.whatsapp import ConversationListItem
from datetime import datetime

conversation = ConversationListItem(
    conversation_id="conv_001",
    patient_id=1,
    patient_name="Rajesh Kumar",
    patient_phone="9876543210",
    last_message="Thank you doctor",
    last_message_time=datetime.now(),
    unread_count=3,
    is_pinned=True,
    is_online=True,
    on_click=lambda conv_id, patient_id: print(f"Selected: {conv_id}"),
    is_dark=False
)
```

#### Quick Replies

```python
from src.ui.whatsapp import QuickReplies

quick_replies = QuickReplies(
    on_reply_selected=lambda text: print(f"Selected: {text}"),
    language="en",  # or "hi" for Hindi
    is_dark=False
)
```

#### AI Suggestions

```python
from src.ui.whatsapp import AISuggestions, AISuggestion

ai_panel = AISuggestions(
    on_suggestion_selected=lambda text: print(f"Using: {text}"),
    on_escalate=lambda: print("Escalating to doctor"),
    is_dark=False
)

# Set suggestions from AI
suggestions = [
    AISuggestion(
        suggestion_id="sugg_001",
        text="Your appointment is confirmed for tomorrow at 10 AM",
        confidence=0.95,
        reason="Patient requested appointment confirmation",
        category="appointment",
        requires_escalation=False
    ),
    AISuggestion(
        suggestion_id="sugg_002",
        text="Please visit the clinic for examination",
        confidence=0.75,
        reason="Symptoms require physical checkup",
        category="urgent",
        requires_escalation=True
    ),
]

ai_panel.set_suggestions(suggestions)
```

#### Escalation Banner

```python
from src.ui.whatsapp import EscalationBanner
from datetime import datetime

banner = EscalationBanner(
    message_id="msg_urgent",
    patient_name="Priya Sharma",
    patient_id=2,
    urgency="emergency",  # emergency, high, medium, low
    reason="Chest pain detected",
    message_content="Doctor, I have severe chest pain!",
    detected_symptoms=["chest pain", "difficulty breathing"],
    timestamp=datetime.now(),
    on_call=lambda pid, name: print(f"Calling: {name}"),
    on_view_history=lambda pid: print(f"Viewing history: {pid}"),
    on_respond=lambda mid, pid: print(f"Responding to: {mid}"),
    on_dismiss=lambda mid: print(f"Dismissed: {mid}"),
    is_dark=False
)
```

#### Attachment Picker

```python
from src.ui.whatsapp import AttachmentPicker

picker = AttachmentPicker(
    patient_id=1,
    patient_name="Rajesh Kumar",
    on_send_prescription=lambda rx_id: print(f"Sending prescription: {rx_id}"),
    on_send_lab_report=lambda rep_id: print(f"Sending lab report: {rep_id}"),
    on_send_document=lambda path: print(f"Sending document: {path}"),
    on_send_appointment=lambda apt: print(f"Sending appointment: {apt}"),
    on_send_location=lambda: print("Sending clinic location"),
    get_recent_prescriptions=lambda pid: [],  # Return list of prescriptions
    get_recent_lab_reports=lambda pid: [],    # Return list of lab reports
    is_dark=False
)

# Show picker
picker.show()
```

## Integration with Main App

### Adding to Central Panel

```python
# In src/ui/central_panel.py

from src.ui.whatsapp import WhatsAppConversationPanel

class CentralPanel(ft.UserControl):
    def __init__(self, ...):
        super().__init__()
        # ... existing code ...

        # Create WhatsApp tab
        self.whatsapp_panel = WhatsAppConversationPanel(
            db_service=self.db_service,
            whatsapp_client=self.whatsapp_client,
            conversation_handler=self.conversation_handler,
            is_dark=self.is_dark
        )

    def build(self):
        return ft.Tabs(
            tabs=[
                ft.Tab(text="Prescription", content=self.prescription_tab),
                ft.Tab(text="History", content=self.history_tab),
                ft.Tab(text="Messages", content=self.whatsapp_panel),  # Add here
                # ... other tabs
            ]
        )
```

### Database Schema for Messages

Add this to your database initialization:

```python
# In src/services/database.py

cursor.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT UNIQUE,
        conversation_id TEXT NOT NULL,
        patient_id INTEGER NOT NULL,
        content TEXT,
        message_type TEXT DEFAULT 'text',
        is_outgoing BOOLEAN DEFAULT 0,
        status TEXT DEFAULT 'sent',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reply_to_id TEXT,
        attachment_url TEXT,
        attachment_name TEXT,
        is_starred BOOLEAN DEFAULT 0,
        metadata TEXT,  -- JSON for additional data
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_conversations (
        id TEXT PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        last_message_time TIMESTAMP,
        unread_count INTEGER DEFAULT 0,
        is_pinned BOOLEAN DEFAULT 0,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_escalations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT NOT NULL,
        patient_id INTEGER NOT NULL,
        urgency TEXT DEFAULT 'medium',
        reason TEXT,
        detected_symptoms TEXT,  -- JSON array
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
""")
```

## Features

### 1. Real-time Updates

The conversation panel supports real-time updates for:
- New incoming messages
- Message status changes (sent → delivered → read)
- Typing indicators
- Online/offline status

### 2. Message Types

Supported message types:
- Text messages
- Images
- Documents (PDF, etc.)
- Replies (quoting another message)
- Interactive buttons (from WhatsApp Business API)

### 3. AI-Powered Features

- **Auto-triage**: AI analyzes incoming messages and suggests responses
- **Smart suggestions**: Context-aware response suggestions
- **Escalation detection**: Automatically flags urgent messages
- **Symptom detection**: Identifies medical symptoms in patient messages

### 4. Accessibility

- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Touch-friendly on tablets

### 5. Dark Mode

All components support dark mode via the `is_dark` parameter.

## Theming

The components use colors from `src/ui/themes.py`. To customize:

```python
from src.ui.themes import get_panel_colors

colors = get_panel_colors(is_dark=False)
# colors['patient_panel_bg']
# colors['card_bg']
# etc.
```

## Performance Considerations

1. **Message Pagination**: Load messages in batches (e.g., 50 at a time)
2. **Lazy Loading**: Load conversation list items as needed
3. **Virtual Scrolling**: For very long chat histories
4. **Debounce Search**: Delay search queries by 300ms
5. **Image Optimization**: Compress images before display

## Security & Privacy

1. **E2E Encryption**: All messages stored encrypted in database
2. **No Screenshots**: Mark sensitive screens as secure
3. **Auto-lock**: Clear sensitive data after timeout
4. **Audit Trail**: Log all message accesses
5. **HIPAA Compliance**: Follow medical data handling guidelines

## Testing

```python
# Example test
def test_message_bubble():
    bubble = MessageBubble(
        message_id="test_001",
        content="Test message",
        timestamp=datetime.now(),
        is_outgoing=True,
        status="sent",
    )

    # Test rendering
    widget = bubble.build()
    assert widget is not None

    # Test status icon
    assert bubble._get_status_icon() is not None
```

## Troubleshooting

### Messages not sending
- Check WhatsApp API credentials in `.env`
- Verify phone number format (E.164)
- Check internet connection

### UI not updating
- Ensure `.update()` is called after state changes
- Check if component is mounted to page
- Verify event handlers are properly connected

### Dark mode issues
- Pass `is_dark` parameter to all components
- Use theme-aware colors from `themes.py`
- Test both light and dark modes

## Future Enhancements

- [ ] Voice messages
- [ ] Video messages
- [ ] Message reactions (emoji reactions)
- [ ] Scheduled messages
- [ ] Broadcast lists
- [ ] Message templates
- [ ] Chat export to PDF
- [ ] Multi-device sync
- [ ] Message encryption indicators
- [ ] Message forwarding

## Support

For issues or questions:
- Check the main DocAssist documentation
- Review WhatsApp Business API docs
- Contact the development team
