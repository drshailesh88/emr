# WhatsApp UI Module - Architecture

## Component Hierarchy

```
WhatsAppConversationPanel (Main Container)
│
├── Conversation List (Left Panel - 350px)
│   ├── Header
│   │   └── "Messages" Title
│   ├── Search Field
│   │   └── Search icon + input
│   ├── Filter Tabs
│   │   ├── All
│   │   ├── Unread
│   │   └── Starred
│   └── Conversations List (Scrollable)
│       ├── ConversationListItem (Patient 1)
│       │   ├── Avatar (Circle with initials)
│       │   ├── Name + Last Message
│       │   ├── Timestamp
│       │   ├── Unread Badge
│       │   └── Online Status Indicator
│       ├── ConversationListItem (Patient 2)
│       └── ... more conversations
│
└── Chat Panel (Right Panel - Expandable)
    ├── Chat Header
    │   ├── Patient Avatar
    │   ├── Patient Name + Status
    │   └── Actions (Call, Video, More)
    │
    ├── Escalation Banner (Conditional)
    │   ├── Urgency Indicator
    │   ├── Patient Info
    │   ├── Message Preview
    │   ├── Detected Symptoms
    │   └── Quick Actions
    │
    ├── Messages View (Scrollable)
    │   ├── Date Separator (GROUP BY DATE)
    │   ├── MessageBubble (Incoming)
    │   │   ├── Reply Preview (if exists)
    │   │   ├── Attachment (if exists)
    │   │   ├── Message Text
    │   │   ├── Timestamp
    │   │   └── Context Menu (Long Press)
    │   ├── MessageBubble (Outgoing)
    │   │   ├── Message Text
    │   │   ├── Timestamp + Status Icon
    │   │   └── Context Menu
    │   └── ... more messages
    │
    └── Input Area
        ├── Attach Button → AttachmentPicker
        ├── Text Input (Multiline)
        ├── Quick Reply Button → QuickReplies
        └── Send Button
```

## Data Flow

### Incoming Message Flow

```
WhatsApp Webhook
       ↓
Conversation Handler (AI Triage)
       ↓
    ┌──────┴──────┐
    ↓             ↓
Database      UI Update
    ↓             ↓
Store       Update ConversationList
Message     Update MessageBubble
    ↓             ↓
Mark Read   Show Notification
```

### Outgoing Message Flow

```
User Types Message
       ↓
Click Send Button
       ↓
_handle_send_message()
       ↓
    ┌──────┴──────┐
    ↓             ↓
Save to DB   Send to WhatsApp API
    ↓             ↓
Update UI    Receive Message ID
    ↓             ↓
Show as      Update Status
"Sent"       (Sent → Delivered → Read)
```

### AI Suggestion Flow

```
Patient Message Received
         ↓
conversation_handler.process_message()
         ↓
LLM Analyzes Message
         ↓
Generate Triage Response
         ↓
    ┌────┴────┐
    ↓         ↓
Urgent?    Normal
    ↓         ↓
Escalation  AI Suggestions
Banner      Panel
    ↓         ↓
Doctor      Quick Response
Notified    Options
```

## State Management

### Panel State

```python
WhatsAppConversationPanel:
    - conversations: List[Dict]           # All conversations
    - current_conversation_id: str        # Selected conversation
    - current_patient_id: int            # Selected patient
    - messages: List[Dict]               # Current chat messages
    - filter_mode: str                   # "all" | "unread" | "starred"
```

### Message States

```
Message Status Flow:
  pending → sent → delivered → read
     ↓        ↓        ↓          ↓
  (Queue) (✓)      (✓✓)      (✓✓ Blue)
```

### Conversation States

```python
Conversation State:
    - IDLE: Normal conversation
    - AWAITING_SLOT_SELECTION: Booking appointment
    - AWAITING_CONFIRMATION: Confirming action
    - AWAITING_SYMPTOMS: Collecting symptom details
    - ESCALATED: Forwarded to doctor
```

## Integration Points

### With Database Service

```python
DatabaseService Methods Used:
    - get_conversations()
    - get_messages(conversation_id)
    - save_message(message)
    - mark_message_read(message_id)
    - get_patient_by_id(patient_id)
    - get_recent_prescriptions(patient_id)
    - get_recent_lab_reports(patient_id)
```

### With WhatsApp Client

```python
WhatsAppClient Methods Used:
    - send_text(to, message)
    - send_document(to, document_url, filename)
    - send_template(to, template_name, params)
    - mark_as_read(message_id)
    - upload_media(file_path)
```

### With Conversation Handler

```python
ConversationHandler Methods Used:
    - process_message(incoming_message)
    - get_ai_suggestions(message)
    - detect_urgency(message)
    - generate_response(context)
```

## Event Flow Diagram

### User Selects Conversation

```
User clicks ConversationListItem
         ↓
_handle_conversation_click()
         ↓
    ┌────┴────┬────────────┬────────────┐
    ↓         ↓            ↓            ↓
Set State  Load       Update       Notify
           Messages   UI           Parent
    ↓         ↓            ↓            ↓
conversation_id  _load_messages()  _update_chat_header()  on_patient_selected()
current_patient_id     ↓            _update_messages_view()
                  Database Query
                       ↓
                  messages = [...]
                       ↓
                  Render MessageBubbles
```

### User Sends Message

```
User types + clicks Send
         ↓
_handle_send_message()
         ↓
    ┌────┴────┐
    ↓         ↓
Create    Clear
Message   Input
    ↓         ↓
Append to  Update UI
messages[]     ↓
    ↓     Input.value = ""
_update_messages_view()
    ↓
_send_to_whatsapp() [async]
    ↓
WhatsAppClient.send_text()
    ↓
Update message status
```

### AI Suggestion Selected

```
AI generates suggestions
         ↓
AISuggestions.set_suggestions()
         ↓
User clicks "Use this"
         ↓
_handle_use_suggestion()
         ↓
on_suggestion_selected(text)
         ↓
_insert_quick_reply(text)
         ↓
message_input.value = text
         ↓
message_input.focus()
         ↓
User reviews and sends
```

## File Dependencies

```
conversation_panel.py
    ├── imports conversation_list_item.py
    ├── imports message_bubble.py
    ├── imports quick_replies.py
    ├── imports ai_suggestions.py
    ├── imports escalation_banner.py
    └── imports attachment_picker.py

__init__.py
    └── exports all components

USAGE.md
    ├── references all components
    └── provides examples

example_integration.py
    └── demonstrates conversation_panel usage
```

## Performance Considerations

### Optimization Strategies

1. **Virtual Scrolling**
   ```
   messages_column → Only render visible messages
   conversation_list → Only render visible conversations
   ```

2. **Debouncing**
   ```
   search_field.on_change → 300ms delay before search
   typing_indicator → 1000ms timeout
   ```

3. **Lazy Loading**
   ```
   Load 50 messages initially
   Load more on scroll to top
   Paginate conversation list
   ```

4. **Caching**
   ```
   Cache patient avatars
   Cache conversation metadata
   Cache quick replies list
   ```

## Error Handling

### Network Errors

```
Try: Send message via WhatsApp API
Catch: HTTPError
    ↓
Update message status to "failed"
    ↓
Show error icon on message bubble
    ↓
Allow retry (tap on failed message)
```

### Database Errors

```
Try: Load messages from database
Catch: DatabaseError
    ↓
Show error state in chat view
    ↓
Provide "Retry" button
    ↓
Log error to audit trail
```

## Security Flow

### Message Encryption

```
User sends message
       ↓
Encrypt content (client-side)
       ↓
Store encrypted in database
       ↓
Send to WhatsApp (TLS)
       ↓
Audit log entry
```

### Access Control

```
User opens conversation
       ↓
Check user permissions
       ↓
    ┌──────┴──────┐
    ↓             ↓
Authorized    Unauthorized
    ↓             ↓
Load data     Show error
    ↓             ↓
Log access    Log attempt
```

## Testing Strategy

### Unit Tests

```
test_message_bubble.py
    - Test rendering
    - Test status icons
    - Test context menu
    - Test dark mode

test_conversation_list_item.py
    - Test avatar generation
    - Test time formatting
    - Test unread badge
    - Test hover effects

test_quick_replies.py
    - Test filtering
    - Test search
    - Test language toggle
    - Test custom replies

test_ai_suggestions.py
    - Test suggestion display
    - Test confidence scores
    - Test escalation flag
    - Test suggestion selection
```

### Integration Tests

```
test_conversation_flow.py
    - Test conversation selection
    - Test message sending
    - Test message receiving
    - Test status updates
    - Test AI suggestions
    - Test escalation
```

## Browser Compatibility

Tested on:
- Chrome 90+ ✓
- Firefox 88+ ✓
- Safari 14+ ✓
- Edge 90+ ✓

## Mobile Support

- Responsive down to 375px width
- Touch gestures supported
- Virtual keyboard handling
- Swipe to dismiss (planned)

---

**Last Updated**: January 2026
**Version**: 1.0.0
