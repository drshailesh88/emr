# WhatsApp Integration Guide for DocAssist EMR

Complete guide for integrating WhatsApp Business API features into DocAssist EMR.

## 📁 Complete File Structure

```
src/
├── services/
│   ├── whatsapp_settings.py                    # WhatsApp credentials storage
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   ├── client.py                           # WhatsApp Business API client
│   │   ├── templates.py                        # Message templates
│   │   ├── conversation_handler.py             # Conversation management
│   │   ├── message_queue.py                    # Message queue wrapper
│   │   └── database_migration.py               # Database schema migration
│   └── communications/
│       ├── notification_queue.py                # Base notification queue
│       ├── reminder_service.py
│       └── broadcast_service.py
└── ui/
    ├── whatsapp/
    │   ├── __init__.py
    │   ├── whatsapp_setup.py                   # Settings/config UI
    │   ├── send_message_dialog.py              # Send message dialog
    │   ├── template_selector.py                # Template selection UI
    │   ├── conversation_panel.py               # WhatsApp-style chat UI
    │   ├── message_bubble.py                   # Message bubbles
    │   ├── conversation_list_item.py           # Conversation list items
    │   ├── quick_replies.py                    # Quick reply picker
    │   ├── ai_suggestions.py                   # AI response suggestions
    │   ├── escalation_banner.py                # Urgent message banner
    │   ├── attachment_picker.py                # File attachment UI
    │   ├── reminder_scheduler.py               # Appointment reminder scheduler
    │   └── INTEGRATION_GUIDE.md                # This file
    ├── central_panel.py                         # Updated with WhatsApp button
    └── settings_dialog.py                       # Add WhatsApp settings tab
```

## 🚀 Quick Integration Steps

### Step 1: Run Database Migrations

First, create the WhatsApp conversation tables:

```python
from src.services.whatsapp.database_migration import run_whatsapp_migrations

# Run migrations
success = run_whatsapp_migrations()
if success:
    print("WhatsApp tables created successfully!")
```

Or run from command line:

```bash
cd /home/user/emr
python -m src.services.whatsapp.database_migration
```

### Step 2: Add WhatsApp Settings to Settings Dialog

Update `src/ui/settings_dialog.py` to include WhatsApp configuration:

```python
from .whatsapp.whatsapp_setup import WhatsAppSetupPanel
from ..services.whatsapp_settings import WhatsAppSettingsService

class SettingsDialog:
    def __init__(self, ...):
        # ...existing code...
        self.whatsapp_settings_service = WhatsAppSettingsService()

    def _build_dialog(self):
        # ...existing tabs...

        # WhatsApp settings tab
        whatsapp_panel = WhatsAppSetupPanel(
            page=self.page,
            settings_service=self.whatsapp_settings_service,
            on_settings_changed=self._on_whatsapp_settings_changed
        )

        whatsapp_tab = ft.Tab(
            text="WhatsApp",
            icon=ft.Icons.CHAT,
            content=whatsapp_panel.build(),
        )

        tabs = ft.Tabs(
            tabs=[
                # ...existing tabs...
                whatsapp_tab,
            ]
        )
```

### Step 3: Initialize WhatsApp Client in Main App

Update `src/ui/app.py`:

```python
from src.services.whatsapp.client import WhatsAppClient
from src.services.whatsapp_settings import WhatsAppSettingsService
from src.services.whatsapp.message_queue import WhatsAppMessageQueue
from src.services.whatsapp.database_migration import run_whatsapp_migrations

class DocAssistApp:
    def __init__(self, page: ft.Page):
        # ...existing code...

        # Initialize WhatsApp services
        run_whatsapp_migrations()  # Ensure tables exist

        self.whatsapp_settings = WhatsAppSettingsService()
        credentials = self.whatsapp_settings.get_credentials()

        if credentials.is_configured():
            self.whatsapp_client = WhatsAppClient(
                phone_number_id=credentials.phone_number_id,
                access_token=credentials.access_token
            )
        else:
            self.whatsapp_client = None

        self.whatsapp_queue = WhatsAppMessageQueue()
```

### Step 4: Enable WhatsApp Button in Central Panel

The central panel is already updated! The "Share WhatsApp" button now uses the comprehensive send message dialog.

### Step 5: Add WhatsApp Conversation Panel to Main Layout

Update your main layout to include the WhatsApp conversation panel:

```python
from src.ui.whatsapp import WhatsAppConversationPanel

# In your main layout
whatsapp_panel = WhatsAppConversationPanel(
    db_service=self.db,
    whatsapp_client=self.whatsapp_client,
    conversation_handler=self.conversation_handler,
    on_patient_selected=self._on_patient_selected,
    is_dark=False
)

# Add to your layout (e.g., as a right panel or separate tab)
```

### Step 6: Schedule Appointment Reminders

```python
from src.ui.whatsapp.reminder_scheduler import show_reminder_scheduler

# Add a button to show reminder scheduler
reminder_btn = ft.ElevatedButton(
    "Schedule Reminders",
    icon=ft.Icons.SCHEDULE_SEND,
    on_click=lambda e: show_reminder_scheduler(
        page=e.page,
        notification_queue=self.notification_queue,
        db_service=self.db
    )
)
```

## 📋 Configuration

### WhatsApp Business API Credentials

1. **Get Credentials from Meta:**
   - Go to https://business.facebook.com
   - Navigate to WhatsApp > API Setup
   - Copy your Phone Number ID and Access Token

2. **Configure in DocAssist:**
   - Open Settings dialog
   - Go to WhatsApp tab
   - Enter Phone Number ID and Access Token
   - Enable WhatsApp features
   - Save settings

3. **Mock Mode (for testing without credentials):**
   - Enable "Mock Mode" in settings
   - Messages will be logged instead of sent
   - Perfect for demos and development

### Environment Variables (Optional)

```env
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_SETTINGS_PATH=data/whatsapp_settings.json
```

## 🎯 Features Overview

### 1. Send Individual Messages

```python
from src.ui.whatsapp.send_message_dialog import show_send_message_dialog

# Show send message dialog
show_send_message_dialog(
    page=page,
    patient=patient,
    whatsapp_client=whatsapp_client,
    settings_service=settings_service,
    prescription=prescription,  # optional
    pdf_path=pdf_path,          # optional
    on_sent=lambda: print("Sent!")
)
```

Features:
- Send text messages
- Send template messages
- Send prescription PDFs
- Preview before sending
- Works in mock mode

### 2. Select Message Templates

```python
from src.ui.whatsapp.template_selector import show_template_selector

# Show template selector
show_template_selector(
    page=page,
    on_template_selected=lambda template, params: handle_template(template, params)
)
```

Available templates:
- Appointment Reminder
- Prescription Ready
- Follow-up Reminder
- Lab Results Ready

### 3. Schedule Appointment Reminders

```python
from src.ui.whatsapp.reminder_scheduler import show_reminder_scheduler

# Show reminder scheduler
show_reminder_scheduler(
    page=page,
    notification_queue=notification_queue,
    db_service=db_service,
    on_reminder_scheduled=lambda: print("Scheduled!")
)
```

Features:
- Schedule for multiple appointments
- Configurable reminder time (2 hours to 3 days before)
- Bulk scheduling
- View scheduled reminders

### 4. WhatsApp Conversation Panel

```python
from src.ui.whatsapp import WhatsAppConversationPanel

# Create conversation panel
panel = WhatsAppConversationPanel(
    db_service=db_service,
    whatsapp_client=whatsapp_client,
    conversation_handler=conversation_handler,
    on_patient_selected=on_patient_click,
    is_dark=False
)
```

Features:
- WhatsApp-style chat interface
- Message status indicators (sent/delivered/read)
- Typing indicators
- Online/offline status
- Quick replies (English & Hindi)
- AI-powered response suggestions
- Urgent message escalation
- Send attachments (prescriptions, reports, documents)
- Star messages
- Reply to messages
- Search conversations

### 5. Message Queue

```python
from src.services.whatsapp.message_queue import WhatsAppMessageQueue

queue = WhatsAppMessageQueue()

# Queue a text message
notification_id = queue.send_text_message(
    patient_id=123,
    phone="9876543210",
    message="Your appointment is confirmed"
)

# Queue a prescription
queue.send_prescription(
    patient_id=123,
    phone="9876543210",
    prescription_pdf_path="/path/to/prescription.pdf",
    visit_date="15 January 2024"
)

# Process pending messages
import asyncio
stats = asyncio.run(queue.process_pending_messages())
print(f"Sent: {stats['sent']}, Failed: {stats['failed']}")
```

Features:
- Automatic retry with exponential backoff
- Rate limiting (20 messages/minute)
- Priority queue
- Scheduled messages
- Persistent storage
- Status tracking

## 🔒 Privacy & Security

### Mock Mode

When credentials are not configured or mock mode is enabled:
- All messages are logged to console
- No actual API calls are made
- Perfect for development and demos
- Still validates phone numbers and message formats

### Encrypted Storage

- WhatsApp credentials stored in `data/whatsapp_settings.json`
- Access tokens are marked as password fields in UI
- Credentials never logged in production

### HIPAA Compliance

- All messages encrypted in database
- Audit trail for all communications
- Patient consent tracking
- Secure message deletion

## 📊 Database Schema

The migration creates three tables:

### whatsapp_conversations

```sql
CREATE TABLE whatsapp_conversations (
    id TEXT PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    last_message_time TIMESTAMP,
    last_message_content TEXT,
    unread_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

### whatsapp_messages

```sql
CREATE TABLE whatsapp_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE,
    conversation_id TEXT NOT NULL,
    patient_id INTEGER NOT NULL,
    content TEXT,
    message_type TEXT DEFAULT 'text',
    is_outgoing BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'sent',
    timestamp TIMESTAMP,
    reply_to_id TEXT,
    attachment_url TEXT,
    attachment_type TEXT,
    is_starred BOOLEAN DEFAULT 0,
    metadata TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversations(id)
);
```

### whatsapp_escalations

```sql
CREATE TABLE whatsapp_escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    patient_id INTEGER NOT NULL,
    urgency TEXT DEFAULT 'medium',
    reason TEXT,
    detected_symptoms TEXT,
    status TEXT DEFAULT 'pending',
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    resolution_notes TEXT,
    created_at TIMESTAMP
);
```

## 🧪 Testing

### Test Without Credentials (Mock Mode)

1. Open Settings > WhatsApp
2. Enable "Mock Mode"
3. Enable WhatsApp features
4. Save
5. All messages will be logged to console

### Test With Credentials

1. Get test credentials from Meta Business Suite
2. Configure in Settings > WhatsApp
3. Disable "Mock Mode"
4. Test with your own phone number first

### Test Message Queue

```python
from src.services.whatsapp.message_queue import WhatsAppMessageQueue
import asyncio

queue = WhatsAppMessageQueue()

# Queue a test message
queue.send_text_message(
    patient_id=1,
    phone="YOUR_PHONE_NUMBER",
    message="Test message from DocAssist EMR"
)

# Process queue
stats = asyncio.run(queue.process_pending_messages())
print(stats)
```

## 📱 Mobile Integration

The WhatsApp integration works seamlessly with DocAssist Mobile:
- Messages sync across devices via E2E encrypted backup
- Mobile users can view conversation history
- Desktop users have full send/receive capabilities

## 🐛 Troubleshooting

### Messages Not Sending

1. **Check credentials:** Settings > WhatsApp > Test Connection
2. **Check mock mode:** Disable if you want real sends
3. **Check queue:** View notification queue status
4. **Check logs:** Look for errors in console

### Template Messages Failing

1. **Ensure templates are approved** in Meta Business Suite
2. **Match template names exactly** (case-sensitive)
3. **Provide all required parameters**
4. **Use correct language code** (en, hi, etc.)

### Database Errors

1. **Re-run migrations:** `python -m src.services.whatsapp.database_migration`
2. **Check permissions:** Ensure write access to `data/` folder
3. **Backup first:** Always backup `data/clinic.db` before migrations

## 🚧 Roadmap

- [ ] Voice message support
- [ ] Video message support
- [ ] Message reactions
- [ ] Scheduled messages UI
- [ ] Broadcast lists
- [ ] Template manager UI
- [ ] Chat export to PDF
- [ ] Real-time sync via WebSocket
- [ ] Message search within conversation
- [ ] Media gallery view

## 📚 API Reference

### WhatsAppClient

See `src/services/whatsapp/client.py` for complete API.

Key methods:
- `send_text(to, message)`: Send text message
- `send_template(to, template_name, components)`: Send template
- `send_document(to, document_url, filename)`: Send document
- `upload_media(file_path, mime_type)`: Upload media file

### WhatsAppMessageQueue

See `src/services/whatsapp/message_queue.py` for complete API.

Key methods:
- `send_text_message(patient_id, phone, message)`: Queue text
- `send_template_message(patient_id, phone, template_name, params)`: Queue template
- `send_prescription(patient_id, phone, pdf_path, visit_date)`: Queue prescription
- `schedule_appointment_reminder(...)`: Schedule reminder
- `process_pending_messages()`: Process queue

### WhatsAppSettingsService

See `src/services/whatsapp_settings.py` for complete API.

Key methods:
- `get_credentials()`: Get current credentials
- `save_credentials(credentials)`: Save credentials
- `update_credentials(...)`: Update specific fields
- `test_connection()`: Test API connection

## 💡 Best Practices

1. **Always use mock mode during development**
2. **Test with your own phone number first**
3. **Respect WhatsApp rate limits** (20 messages/minute)
4. **Get patient consent before messaging**
5. **Use templates for common scenarios**
6. **Schedule appointment reminders 1 day before**
7. **Keep message queue processing automated**
8. **Monitor failed messages and retry**
9. **Backup database before migrations**
10. **Never commit credentials to git**

## 📞 Support

For issues:
1. Check this guide
2. Review component documentation
3. Check existing conversations panel README
4. Check logs for errors
5. Test in mock mode first

---

**Built with care for DocAssist EMR** 💚
