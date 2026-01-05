# WhatsApp Conversation UI Module

Complete WhatsApp-style conversation interface for DocAssist EMR patient messaging.

## 📁 Module Structure

```
src/ui/whatsapp/
├── __init__.py                    # Module exports
├── conversation_panel.py          # Main conversation panel (WhatsApp-like interface)
├── message_bubble.py              # Individual message bubbles
├── conversation_list_item.py      # Conversation list items
├── quick_replies.py               # Quick reply picker (EN/HI support)
├── ai_suggestions.py              # AI-powered response suggestions
├── escalation_banner.py           # Urgent message escalation banner
├── attachment_picker.py           # File/document attachment picker
├── USAGE.md                       # Detailed usage guide
├── example_integration.py         # Integration example
└── README.md                      # This file
```

## 🎨 Components Overview

### 1. **WhatsAppConversationPanel** (Main Component)
The primary panel that integrates all features:
- **Left Panel**: Conversation list with search and filters
- **Right Panel**: Active chat view with messages
- **Input Area**: Message composition with attachments
- **Real-time**: Updates for typing, online status, message status

**Key Features:**
- Search conversations
- Filter by All/Unread/Starred
- Message status (sent/delivered/read checkmarks)
- Typing indicators
- Online/offline status
- Quick replies and AI suggestions
- Attachment sending (prescriptions, lab reports, documents)

### 2. **MessageBubble**
WhatsApp-style message bubble with:
- Incoming (left) and outgoing (right) alignment
- Timestamp and status indicators
- Reply-to preview
- Attachment support (images, documents)
- Long-press context menu (Reply, Copy, Star)
- Star/unstar messages
- Different styles for light/dark mode

### 3. **ConversationListItem**
Individual conversation in the list:
- Patient avatar (initials with color)
- Patient name and last message preview
- Relative timestamps ("2m ago", "Yesterday")
- Unread count badge
- Pinned indicator
- Online status dot
- Typing indicator animation
- Hover effects

### 4. **QuickReplies**
Predefined response picker:
- 10 default quick replies in English and Hindi
- Searchable and filterable by category
- Language toggle (English ↔ Hindi)
- Categories: Appointments, Medication, Follow-up, Reports, etc.
- Custom quick replies support
- One-click send or edit before sending

**Default Quick Replies:**
- Appointment confirmed
- Take medicines regularly
- Come for follow-up
- Reports are normal
- Visit clinic for examination
- Prescription sent
- Emergency - call clinic
- Stay hydrated and rest
- Get tests done
- Follow diet plan

### 5. **AISuggestions**
AI-powered response suggestions:
- Analyzes incoming patient messages
- Suggests appropriate responses with confidence scores
- Categories: General, Urgent, Prescription, Appointment
- Visual confidence indicators (progress bars)
- One-click use or edit suggestions
- Escalation recommendations for urgent cases

### 6. **EscalationBanner**
Alert banner for urgent messages:
- 4 urgency levels: Emergency, High, Medium, Low
- Color-coded based on urgency
- Detected symptoms chips
- Quick actions: Call, View History, Respond, Dismiss
- Time since message received
- Auto-detection of emergency keywords

### 7. **AttachmentPicker**
Bottom sheet for sending attachments:
- Send prescription (recent prescriptions list)
- Send lab report (recent test results)
- Send document (file picker)
- Send appointment details
- Send clinic location
- Empty states for "no data" scenarios

## 🚀 Quick Start

### Basic Integration

```python
import flet as ft
from src.ui.whatsapp import WhatsAppConversationPanel

def main(page: ft.Page):
    # Initialize services
    db_service = DatabaseService()
    whatsapp_client = WhatsAppClient()
    conversation_handler = ConversationHandler(llm, db_service, whatsapp_client)

    # Create panel
    whatsapp_panel = WhatsAppConversationPanel(
        db_service=db_service,
        whatsapp_client=whatsapp_client,
        conversation_handler=conversation_handler,
        is_dark=False
    )

    page.add(whatsapp_panel)

ft.app(target=main)
```

### Standalone Components

```python
from src.ui.whatsapp import MessageBubble, QuickReplies, EscalationBanner

# Use components individually in your UI
message = MessageBubble(...)
quick_replies = QuickReplies(...)
escalation = EscalationBanner(...)
```

## 📊 Database Schema

Required tables for full functionality:

```sql
-- Messages table
CREATE TABLE whatsapp_messages (
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
    is_starred BOOLEAN DEFAULT 0,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Conversations table
CREATE TABLE whatsapp_conversations (
    id TEXT PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    last_message_time TIMESTAMP,
    unread_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT 0,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Escalations table
CREATE TABLE whatsapp_escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    patient_id INTEGER NOT NULL,
    urgency TEXT DEFAULT 'medium',
    reason TEXT,
    detected_symptoms TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎨 Design System

### Colors

**Light Mode:**
- Background: White (#FFFFFF)
- Incoming bubble: White
- Outgoing bubble: Light green (#DCF8C6)
- Text: Black
- Secondary text: Grey-600
- Borders: Grey-300

**Dark Mode:**
- Background: Dark (#1E1E1E)
- Incoming bubble: Dark grey (#1E2428)
- Outgoing bubble: Dark teal (#056162)
- Text: White
- Secondary text: Grey-400
- Borders: Grey-800

### Typography

- Message text: 14px
- Patient name: 15px bold
- Timestamps: 11px/12px
- Quick replies: 14px
- Headers: 16px-20px bold

### Spacing

- Message padding: 12px horizontal, 8px vertical
- Message margin: 8px horizontal, 2px vertical
- Container padding: 16px
- Avatar radius: 25px (50px diameter)

## ✨ Premium UX Features

1. **Smooth Animations**
   - 300ms transitions
   - Ease-out curves
   - Typing indicator animation
   - Message entry/exit animations

2. **Haptic Feedback**
   - Long-press on messages
   - Button clicks
   - Send message action

3. **Accessibility**
   - Keyboard navigation
   - Screen reader support
   - High contrast support
   - Touch-friendly (48px minimum touch targets)

4. **Performance**
   - Virtual scrolling for long chats
   - Lazy loading conversations
   - Debounced search (300ms)
   - Optimized re-renders

5. **Mobile-Ready**
   - Responsive layout
   - Touch gestures
   - Works on tablets
   - Low RAM tolerance

## 🔒 Security & Privacy

- **E2E Encryption**: All messages encrypted in database
- **Audit Trail**: All message access logged
- **HIPAA Compliant**: Follows medical data guidelines
- **No Screenshots**: Sensitive screens marked secure
- **Auto-lock**: Session timeout

## 🌐 Internationalization

Currently supported languages:
- **English** (en)
- **Hindi** (hi) - हिन्दी

Quick replies available in both languages with one-click toggle.

## 🧪 Testing

Run the example:
```bash
python -m src.ui.whatsapp.example_integration
```

Unit tests:
```bash
pytest tests/ui/test_whatsapp_components.py
```

## 📝 Configuration

Environment variables needed:
```env
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
```

## 🐛 Known Issues

1. **Voice messages**: Not yet implemented (planned)
2. **Message reactions**: Not yet implemented (planned)
3. **Real-time sync**: Currently polling-based (websocket planned)

## 🚧 Roadmap

- [ ] Voice message support
- [ ] Video message support
- [ ] Message reactions (emoji)
- [ ] Scheduled messages
- [ ] Broadcast lists
- [ ] Message templates manager
- [ ] Chat export to PDF
- [ ] Multi-device sync
- [ ] WebSocket for real-time updates
- [ ] Message search within conversation
- [ ] Media gallery view
- [ ] Contact sharing

## 📚 Documentation

- **USAGE.md**: Detailed usage guide with examples
- **example_integration.py**: Working integration example
- **Component docstrings**: Each class has detailed documentation

## 🤝 Contributing

When contributing to this module:
1. Follow the existing design patterns
2. Maintain both light and dark mode support
3. Test on different screen sizes
4. Add docstrings to all public methods
5. Update USAGE.md for new features

## 📄 License

Part of DocAssist EMR - Internal use only.

## 👥 Support

For issues or questions:
- Check USAGE.md first
- Review example_integration.py
- Contact the DocAssist development team

---

**Built with ❤️ using Flet for DocAssist EMR**
