# DocAssist Communication Services

Automated patient communication system for appointments, reminders, broadcasts, and health tips.

## Overview

The Communication Services module provides a complete system for automated patient engagement:

1. **Template Manager** - Bilingual message templates (English + Hindi)
2. **Reminder Service** - Automated appointment, medication, and preventive care reminders
3. **Broadcast Service** - Clinic notices, health tips, and marketing campaigns
4. **Notification Queue** - Priority-based queue with retry logic and rate limiting

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Communication Services                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Template   │  │   Reminder   │  │  Broadcast   │          │
│  │   Manager    │  │   Service    │  │   Service    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                  │
│         └─────────────────┼──────────────────┘                  │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │  Notification   │                            │
│                  │     Queue       │                            │
│                  └────────┬────────┘                            │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │    WhatsApp     │                            │
│                  │     Client      │                            │
│                  └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Template Manager

Manages bilingual message templates with variable substitution.

**Features:**
- Predefined templates for common scenarios
- Custom template creation
- English + Hindi support
- Variable placeholders (e.g., `{patient_name}`, `{date}`)

**Usage:**
```python
from src.services.communications import TemplateManager

tm = TemplateManager()

# Render a template
message = tm.render("appointment_reminder", {
    "patient_name": "Ram Lal",
    "doctor_name": "Dr. Sharma",
    "clinic_name": "DocAssist Clinic",
    "date": "15-Jan-2024",
    "time": "10:00 AM"
}, language="en")

# Create custom template
tm.create_custom_template(
    "welcome_new_patient",
    "Welcome {patient_name} to {clinic_name}!",
    "स्वागत है {patient_name} {clinic_name} में!",
    ["patient_name", "clinic_name"]
)
```

**Predefined Templates:**
- `appointment_reminder` - Appointment reminders (1 day, 2 hours before)
- `follow_up_reminder` - Follow-up visit reminders
- `medication_reminder` - Daily medication reminders
- `lab_due` - Overdue lab test reminders
- `health_tip` - Weekly health tips
- `clinic_notice` - Clinic closure/holiday notices
- `preventive_care_annual` - Annual checkup reminders
- `prescription_ready` - Prescription ready for pickup
- `birthday_wishes` - Patient birthday messages
- `test_results_ready` - Lab results available

### 2. Reminder Service

Automated reminder scheduling with intelligent timing.

**Features:**
- Appointment reminders (1 day + 2 hours before)
- Follow-up visit reminders
- Daily medication reminders
- Preventive care reminders (annual checkup, screenings)
- Lab due reminders
- Patient preference support (time, channel)
- Reminder cancellation

**Usage:**
```python
from src.services.communications import ReminderService
from datetime import datetime, timedelta

rs = ReminderService()

# Schedule appointment reminders
appointment = {
    "id": 123,
    "patient_id": 45,
    "doctor_name": "Dr. Sharma",
    "appointment_time": datetime.now() + timedelta(days=2),
    "clinic_name": "DocAssist Clinic",
    "clinic_phone": "9876543210"
}
reminder_ids = rs.schedule_appointment_reminder(appointment)

# Schedule medication reminders
prescription = {
    "medications": [{
        "drug_name": "Metformin",
        "dose": "500mg",
        "frequency": "BD",
        "duration": "30 days",
        "instructions": "after meals"
    }]
}
patient = {"id": 45, "name": "Ram Lal"}
rs.schedule_medication_reminders(prescription, patient)

# Get pending reminders
reminders = rs.get_pending_reminders(patient_id=45)
```

**Reminder Types:**
- `APPOINTMENT` - Appointment confirmations and reminders
- `FOLLOW_UP` - Follow-up visit reminders
- `MEDICATION` - Daily medication adherence reminders
- `PREVENTIVE_CARE` - Annual checkup, screening reminders
- `LAB_DUE` - Overdue or upcoming lab test reminders

**Channels:**
- `WHATSAPP` - WhatsApp Business Cloud API
- `SMS` - SMS (future implementation)
- `BOTH` - Both channels

### 3. Broadcast Service

Mass communication for clinic notices, health tips, and campaigns.

**Features:**
- Clinic notices (holidays, closures)
- Health tips to patient segments
- Marketing campaigns
- Patient segmentation (diagnosis, age, gender, etc.)
- Delivery statistics
- Opt-out management
- Scheduled broadcasts

**Usage:**
```python
from src.services.communications import BroadcastService, Campaign
from datetime import datetime, timedelta

bs = BroadcastService()

# Create patient segment
segment = bs.create_patient_segment(
    "Diabetic Patients 40+",
    {
        "diagnosis": "diabetes",
        "age_range": [40, 100]
    }
)

# Send clinic notice
patient_ids = [1, 2, 3, 4, 5]
notice = "Clinic closed on 26-Jan for Republic Day"
bs.send_clinic_notice(patient_ids, notice)

# Send health tip
tip = "Drink 8 glasses of water daily for better health"
bs.send_health_tip("diabetics", tip)

# Send campaign
campaign = Campaign(
    name="Free Diabetes Screening",
    message="Join our FREE screening camp on 20-Jan!",
    segment_id=segment.id,
    scheduled_time=datetime.now() + timedelta(days=5)
)
bs.send_campaign(campaign)

# Get delivery stats
stats = bs.get_delivery_stats(broadcast_id)
print(f"Delivered: {stats.delivered}/{stats.total}")
```

**Segment Criteria:**
- `diagnosis` - Filter by diagnosis (e.g., "diabetes", "hypertension")
- `age_range` - Age range [min, max]
- `gender` - Patient gender (M/F/O)
- `last_visit_days` - Last visit within N days

### 4. Notification Queue

Priority-based queue with automatic retries and rate limiting.

**Features:**
- Priority queue (urgent > high > normal > low)
- Automatic retries with exponential backoff
- Rate limiting (20 messages/minute)
- Delivery tracking (sent, delivered, read, failed)
- Queue status monitoring
- Failed message retry

**Usage:**
```python
from src.services.communications import NotificationQueue, Notification, NotificationPriority
import asyncio

nq = NotificationQueue()

# Enqueue notification
notification = Notification(
    patient_id=45,
    phone="9876543210",
    message="Your appointment is tomorrow at 10 AM",
    priority=NotificationPriority.HIGH,
    channel="whatsapp"
)
notif_id = nq.enqueue(notification)

# Process queue (async)
async def process():
    stats = await nq.process_queue(max_batch_size=50)
    print(f"Sent: {stats['sent']}, Failed: {stats['failed']}")

asyncio.run(process())

# Get queue status
status = nq.get_queue_status()
print(f"Pending: {status.pending}, Failed: {status.failed}")

# Retry failed notification
nq.retry_failed(notif_id)
```

**Priority Levels:**
- `URGENT` - Critical messages (test results, emergencies)
- `HIGH` - Important messages (appointment confirmations)
- `NORMAL` - Regular messages (reminders)
- `LOW` - Non-urgent messages (health tips)

**Retry Strategy:**
- 1st retry: 5 minutes
- 2nd retry: 15 minutes
- 3rd retry: 1 hour
- 4th retry: 4 hours
- Max retries: 3 (configurable)

## Database Schema

### reminders
```sql
CREATE TABLE reminders (
    id TEXT PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,
    message TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT,
    sent_at TEXT,
    error_message TEXT
);
```

### broadcasts
```sql
CREATE TABLE broadcasts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    message TEXT NOT NULL,
    segment_id TEXT,
    scheduled_time TEXT,
    status TEXT NOT NULL,
    delivery_stats TEXT,
    created_at TEXT,
    completed_at TEXT
);
```

### notification_queue
```sql
CREATE TABLE notification_queue (
    id TEXT PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    message TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    channel TEXT DEFAULT 'whatsapp',
    metadata TEXT,
    created_at TEXT NOT NULL,
    scheduled_for TEXT,
    sent_at TEXT,
    delivered_at TEXT,
    error_message TEXT,
    next_retry_at TEXT
);
```

### patient_segments
```sql
CREATE TABLE patient_segments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    criteria TEXT NOT NULL,
    patient_count INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
```

## Integration with WhatsApp

All messages are sent via WhatsApp Business Cloud API (from `src/services/whatsapp/client.py`).

**Setup:**
1. Create Meta Business account
2. Set up WhatsApp Business API
3. Add credentials to `.env`:
   ```
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   WHATSAPP_ACCESS_TOKEN=your_access_token
   ```

**Message Types Supported:**
- Text messages
- Template messages (pre-approved)
- Documents (prescription PDFs)
- Interactive buttons

## Patient Privacy & Consent

**Opt-Out Management:**
- Patients can opt out of broadcasts, health tips, or reminders
- Stored in `patient_communication_preferences` table
- Automatically filtered before sending

**Data Protection:**
- All patient data encrypted at rest (E2E encryption via backup service)
- No data leaves device except via encrypted backup
- WhatsApp messages use E2E encryption
- Audit trail for all communications

## Background Processing

**Recommended Setup:**

1. **Cron job for reminder processing:**
```bash
# Check for due reminders every 15 minutes
*/15 * * * * cd /path/to/docassist && python3 -m src.services.communications.process_reminders
```

2. **Systemd service for queue processing:**
```ini
[Unit]
Description=DocAssist Notification Queue Worker
After=network.target

[Service]
Type=simple
User=docassist
WorkingDirectory=/path/to/docassist
ExecStart=/usr/bin/python3 -m src.services.communications.queue_worker
Restart=always

[Install]
WantedBy=multi-user.target
```

## Testing

Run the demo script:
```bash
python3 examples/communications_demo.py
```

## Error Handling

All services implement:
- Graceful degradation (continue on single message failure)
- Detailed error logging
- Transaction rollback on database errors
- Automatic retry for transient failures

## Rate Limiting

**WhatsApp Business API Limits:**
- 20 messages/minute (configurable)
- Automatically enforced by `NotificationQueue`
- Queued messages sent in batches with delays

## Future Enhancements

- [ ] SMS gateway integration (Twilio/MSG91)
- [ ] Email notifications
- [ ] Voice call reminders (IVR)
- [ ] Rich media messages (images, videos)
- [ ] Two-way communication (chatbot)
- [ ] Analytics dashboard
- [ ] A/B testing for messages
- [ ] Smart send time optimization
- [ ] Sentiment analysis for responses

## Pricing Integration

Communication costs are tracked per tier:

| Tier | Monthly Message Quota | Overage Cost |
|------|----------------------|--------------|
| Free | 100 | Not available |
| Essential | 500 | ₹0.25/message |
| Professional | 2,000 | ₹0.20/message |
| Clinic | 10,000 | ₹0.15/message |
| Hospital | Unlimited | ₹0.10/message |

## Support

For issues or questions:
- GitHub Issues: https://github.com/docassist/emr/issues
- Email: support@docassist.in
- WhatsApp: +91-XXXXXXXXXX
