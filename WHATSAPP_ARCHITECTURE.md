# WhatsApp Integration Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DocAssist EMR - WhatsApp Integration              │
└─────────────────────────────────────────────────────────────────────────────┘

                                  USER INTERFACE
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │  Settings Dialog │  │  Central Panel   │  │ Appointment Panel│        │
│  │                  │  │                  │  │                  │        │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │        │
│  │  │ WhatsApp   │  │  │  │  Share     │  │  │  │ Schedule   │  │        │
│  │  │ Settings   │  │  │  │  WhatsApp  │  │  │  │ Reminders  │  │        │
│  │  │ Panel      │  │  │  │  Button    │  │  │  │ Button     │  │        │
│  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    WhatsApp UI Components                           │  │
│  │                                                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │ Send Message │  │  Template    │  │  Reminder    │            │  │
│  │  │   Dialog     │  │  Selector    │  │  Scheduler   │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  │                                                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │ Conversation │  │  Message     │  │  Quick       │            │  │
│  │  │   Panel      │  │  Bubbles     │  │  Replies     │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↕
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                                  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    WhatsApp Settings Service                         │  │
│  │  - Credential storage (Phone Number ID, Access Token)               │  │
│  │  - Mock mode configuration                                           │  │
│  │  - Connection testing                                                │  │
│  │  - Enable/disable features                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                       ↕                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    WhatsApp Message Queue                            │  │
│  │  - Queue text messages                                               │  │
│  │  - Queue template messages                                           │  │
│  │  - Queue documents (PDFs)                                            │  │
│  │  - Schedule appointment reminders                                    │  │
│  │  - Automatic retry (exponential backoff)                             │  │
│  │  - Rate limiting (20/minute)                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                       ↕                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  Notification Queue Service                          │  │
│  │  - Persistent queue (SQLite)                                         │  │
│  │  - Priority handling                                                 │  │
│  │  - Status tracking                                                   │  │
│  │  - Retry management                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↕
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WhatsApp Client                                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    WhatsApp Business API Client                      │  │
│  │  - send_text(to, message)                                            │  │
│  │  - send_template(to, template_name, components)                      │  │
│  │  - send_document(to, document_url, filename)                         │  │
│  │  - upload_media(file_path, mime_type)                                │  │
│  │  - send_interactive_buttons(...)                                     │  │
│  │  - mark_as_read(message_id)                                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↕
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                      │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         SQLite Database                              │  │
│  │                         data/clinic.db                               │  │
│  │                                                                      │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │  │
│  │  │  whatsapp_       │  │  whatsapp_       │  │  whatsapp_       │  │  │
│  │  │  conversations   │  │  messages        │  │  escalations     │  │  │
│  │  │                  │  │                  │  │                  │  │  │
│  │  │  - id            │  │  - id            │  │  - id            │  │  │
│  │  │  - patient_id    │  │  - message_id    │  │  - message_id    │  │  │
│  │  │  - last_message  │  │  - conversation  │  │  - patient_id    │  │  │
│  │  │  - unread_count  │  │  - content       │  │  - urgency       │  │  │
│  │  │  - is_pinned     │  │  - status        │  │  - symptoms      │  │  │
│  │  └──────────────────┘  │  - attachment    │  │  - status        │  │  │
│  │                        └──────────────────┘  └──────────────────┘  │  │
│  │                                                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │              notification_queue                              │  │  │
│  │  │  - id, patient_id, phone, message, priority, status          │  │  │
│  │  │  - retry_count, scheduled_for, sent_at                       │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    WhatsApp Settings File                            │  │
│  │                    data/whatsapp_settings.json                       │  │
│  │                                                                      │  │
│  │  {                                                                   │  │
│  │    "phone_number_id": "...",                                         │  │
│  │    "access_token": "...",                                            │  │
│  │    "enabled": true,                                                  │  │
│  │    "mock_mode": false                                                │  │
│  │  }                                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↕
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL SERVICES                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐          │
│  │              WhatsApp Business Cloud API                    │          │
│  │              graph.facebook.com/v18.0                       │          │
│  │                                                             │          │
│  │  - Send messages                                            │          │
│  │  - Upload media                                             │          │
│  │  - Receive webhooks (future)                                │          │
│  │  - Get message status                                       │          │
│  └─────────────────────────────────────────────────────────────┘          │
│                                                                             │
│                   OR (when mock_mode = true)                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐          │
│  │              Console Logger (Mock Mode)                     │          │
│  │                                                             │          │
│  │  [MOCK MODE] Would send WhatsApp message to +91...         │          │
│  │  Message: Dear patient, your prescription is ready...      │          │
│  └─────────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### Flow 1: Send Prescription via WhatsApp

```
1. Doctor → Click "Share WhatsApp" button in Central Panel
           ↓
2. UI     → Opens SendMessageDialog
           ↓
3. Dialog → Loads patient info, prescription, PDF path
           ↓
4. Dialog → User selects message type (Text/Template/PDF)
           ↓
5. Dialog → User previews message
           ↓
6. Dialog → User clicks "Send Message"
           ↓
7. Dialog → Checks WhatsAppSettingsService
           ↓
           ├─ Mock Mode? → Log to console → Done
           └─ Production? → Continue
                           ↓
8. Dialog → Calls WhatsAppClient.send_document() or send_text()
           ↓
9. Client → Uploads media (if PDF)
           ↓
10. Client → Sends message via WhatsApp API
           ↓
11. Client → Returns result (message_id, status)
           ↓
12. Dialog → Shows success/error
           ↓
13. Dialog → Stores message in whatsapp_messages table
           ↓
14. Done  → Patient receives WhatsApp message
```

### Flow 2: Schedule Appointment Reminders

```
1. Receptionist → Opens Reminder Scheduler
                 ↓
2. Scheduler   → Loads upcoming appointments from database
                 ↓
3. Scheduler   → Displays list with schedule status
                 ↓
4. Receptionist → Selects reminder time (e.g., 1 day before)
                 ↓
5. Receptionist → Clicks "Schedule Reminders for All"
                 ↓
6. Scheduler   → For each appointment:
                 ↓
7. Scheduler   → Calculates send time (appointment - 1 day)
                 ↓
8. Scheduler   → Creates Notification object
                 ↓
9. Scheduler   → Calls WhatsAppMessageQueue.schedule_appointment_reminder()
                 ↓
10. Queue      → Enqueues notification with scheduled_for time
                 ↓
11. Queue      → Stores in notification_queue table
                 ↓
12. Done       → Reminders scheduled
                 ↓
--- At scheduled time ---
                 ↓
13. Queue      → process_queue() runs (manual or cron)
                 ↓
14. Queue      → Finds notifications where scheduled_for <= now
                 ↓
15. Queue      → Sends via WhatsAppClient
                 ↓
16. Queue      → Updates status to "sent"
                 ↓
17. Done       → Patients receive reminders
```

### Flow 3: Mock Mode (No Credentials)

```
1. Doctor      → Clicks "Share WhatsApp"
                ↓
2. Dialog      → Checks WhatsAppSettingsService
                ↓
3. Settings    → Returns credentials with mock_mode=true
                ↓
4. Dialog      → Shows normal UI
                ↓
5. Doctor      → Fills in details, clicks "Send"
                ↓
6. Dialog      → Checks mock_mode
                ↓
7. Dialog      → Logs to console:
                 [MOCK MODE] Would send WhatsApp message to +919876543210:
                 Dear Rajesh Kumar, Your prescription is ready...
                ↓
8. Dialog      → Shows success message
                ↓
9. Done        → No external API calls made
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                      │
└─────────────────────────────────────────────────────────┘

Layer 1: Credential Storage
──────────────────────────
• Credentials stored in data/whatsapp_settings.json
• File permissions: 600 (owner read/write only)
• Never logged or displayed in plain text
• Access tokens marked as password fields in UI

Layer 2: Mock Mode Safety
──────────────────────────
• Default mode: mock_mode=true
• Prevents accidental sends during development
• All UI functions work without credentials
• Clear visual indicator in settings

Layer 3: Database Security
──────────────────────────
• All messages encrypted at rest (future)
• Audit trail for all communications
• Foreign key constraints enforced
• Patient consent tracking (future)

Layer 4: API Security
──────────────────────
• HTTPS only (WhatsApp API)
• Bearer token authentication
• Rate limiting enforced
• Timeout on all requests

Layer 5: HIPAA Compliance
──────────────────────────
• Patient data never in logs (production)
• Message content encrypted in DB (future)
• Access control and audit trails
• Secure deletion when needed
```

## Error Handling & Retry Logic

```
┌─────────────────────────────────────────────────────────┐
│                  Error Handling Flow                    │
└─────────────────────────────────────────────────────────┘

Message Send Attempt
        ↓
   Success? ─────Yes────→ Mark as "sent"
        │                      ↓
        No                Store message_id
        ↓                      ↓
   Check retry count           Done
        ↓
   < max_retries? ────No────→ Mark as "failed"
        │                      ↓
        Yes               Alert admin
        ↓
   Calculate backoff
   (5min, 15min, 1hr, 4hr)
        ↓
   Update next_retry_at
        ↓
   Mark as "retry"
        ↓
   Wait for next cycle
        ↓
   Retry send
```

## Performance Considerations

### Rate Limiting
- WhatsApp API: 20 messages/minute
- Queue processor: Enforced delays between sends
- Bulk operations: Batched appropriately

### Database Performance
- Indexes on conversation_id, patient_id, timestamp
- Pagination for large message lists
- Lazy loading of conversation history

### UI Performance
- Async/await for all API calls
- Threading for long operations
- Loading indicators for user feedback
- Debounced search in conversation list

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Development Environment                  │
│  - Mock mode enabled by default                        │
│  - Console logging for messages                        │
│  - No external dependencies                            │
│  - Full UI functionality                               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                Staging Environment                      │
│  - Test credentials from Meta sandbox                  │
│  - Real API calls to test numbers                      │
│  - Limited rate (for testing)                          │
│  - Full monitoring                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                Production Environment                   │
│  - Production credentials                              │
│  - Mock mode disabled                                  │
│  - Full rate limits                                    │
│  - Patient consent verified                            │
│  - Monitoring and alerts                               │
│  - Backup and disaster recovery                        │
└─────────────────────────────────────────────────────────┘
```

---

**Key Architectural Decisions:**

1. **Mock Mode by Default** - Prevents accidental sends, perfect for demos
2. **Queue-Based Messaging** - Reliability, retry logic, rate limiting
3. **Modular UI Components** - Each can be used independently
4. **Settings-Based Configuration** - No code changes for credentials
5. **Database-First** - All messages persisted before sending
6. **Graceful Degradation** - Works without WhatsApp API

This architecture ensures DocAssist EMR can demo and develop WhatsApp features without external setup, while being production-ready when credentials are configured.
