# Feature: Patient Reminders

> Automated follow-up reminders via SMS/WhatsApp to reduce no-shows

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Patients forget follow-up appointments. No-shows waste slots and delay care. Automated reminders would improve attendance and patient outcomes.

## User Stories

### Primary User Story
**As a** doctor
**I want to** send automated appointment reminders
**So that** patients don't forget their follow-ups

### Additional Stories
- As a patient, I want a reminder the day before my appointment
- As a doctor, I want to remind about overdue medications/tests
- As a doctor, I want to know if reminders were delivered

## Requirements

### Functional Requirements

**Appointment Reminders:**
1. **FR-1**: Automatic reminder 1 day before appointment
2. **FR-2**: Optional reminder 1 hour before
3. **FR-3**: Reminder via WhatsApp (preferred) or SMS
4. **FR-4**: Include appointment date, time, clinic name

**Clinical Reminders:**
5. **FR-5**: Lab test due reminders
6. **FR-6**: Medication refill reminders
7. **FR-7**: Screening due reminders (from flowsheets)

**Management:**
8. **FR-8**: View pending reminders
9. **FR-9**: Cancel/pause reminders for a patient
10. **FR-10**: Log reminder delivery status
11. **FR-11**: Opt-out option for patients

### Non-Functional Requirements
1. **NFR-1**: Reminders sent even if app is closed (system scheduler)
2. **NFR-2**: Graceful failure if SMS service unavailable
3. **NFR-3**: No more than 1 reminder per day per patient

## Acceptance Criteria

- [ ] Appointment reminder sent 1 day before
- [ ] Reminder includes date, time, clinic name
- [ ] WhatsApp used if patient has WhatsApp
- [ ] SMS used as fallback
- [ ] Delivery status logged
- [ ] Patient can opt out
- [ ] Admin can view reminder queue

## Technical Approach

### Reminder Engine
```python
# Run daily at 6 PM to send next-day reminders
def send_appointment_reminders():
    tomorrow = date.today() + timedelta(days=1)
    appointments = get_appointments_for_date(tomorrow)

    for appt in appointments:
        patient = get_patient(appt.patient_id)
        if patient.reminder_opted_out:
            continue

        message = format_reminder(appt, patient)

        # Try WhatsApp first, then SMS
        if send_whatsapp(patient.phone, message):
            log_reminder(appt.id, 'whatsapp', 'sent')
        elif send_sms(patient.phone, message):
            log_reminder(appt.id, 'sms', 'sent')
        else:
            log_reminder(appt.id, 'failed', 'both failed')
```

### SMS Gateway Options (India)
1. **MSG91** - Popular, reasonable pricing
2. **Twilio** - International, more expensive
3. **Fast2SMS** - Cheap but basic
4. **TextLocal** - Good API

### Running Without App Open
- Windows: Task Scheduler
- macOS: launchd
- Linux: cron

```bash
# Example cron job
0 18 * * * /path/to/python /path/to/send_reminders.py
```

## Database Schema

```sql
CREATE TABLE patient_preferences (
    patient_id INTEGER PRIMARY KEY,
    reminder_opted_out INTEGER DEFAULT 0,
    preferred_channel TEXT DEFAULT 'whatsapp',
    reminder_timing TEXT DEFAULT '1_day',
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE TABLE reminder_log (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    reminder_type TEXT NOT NULL,  -- 'appointment', 'lab_due', 'medication'
    reference_id INTEGER,  -- appointment_id or null
    channel TEXT NOT NULL,  -- 'whatsapp', 'sms'
    status TEXT NOT NULL,  -- 'sent', 'delivered', 'failed', 'opted_out'
    message TEXT,
    sent_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

CREATE INDEX idx_reminder_patient ON reminder_log(patient_id);
CREATE INDEX idx_reminder_date ON reminder_log(sent_at);
```

## Message Templates

### Appointment Reminder
```
🏥 *Appointment Reminder*

Dear {patient_name},

This is a reminder of your appointment:

📅 Date: {date}
⏰ Time: {time}
🏥 {clinic_name}

If you need to reschedule, please call {clinic_phone}.

Thank you!
```

### Lab Due Reminder
```
🔬 *Lab Test Reminder*

Dear {patient_name},

Your {test_name} is due for a recheck. Your last test was on {last_date}.

Please schedule your test at your convenience.

{clinic_name}
{clinic_phone}
```

## UI Design

### Reminder Settings (per patient)
```
┌─────────────────────────────────────────┐
│ Reminder Settings: Ram Lal          [X] │
├─────────────────────────────────────────┤
│                                         │
│ [✓] Enable appointment reminders        │
│                                         │
│ Preferred Channel:                      │
│ (●) WhatsApp  ( ) SMS  ( ) Both        │
│                                         │
│ Reminder Timing:                        │
│ [✓] 1 day before                        │
│ [ ] 1 hour before                       │
│                                         │
│ [✓] Enable clinical reminders           │
│     (lab due, screening due)            │
│                                         │
├─────────────────────────────────────────┤
│                     [Cancel]  [Save]    │
└─────────────────────────────────────────┘
```

### Reminder Queue (Admin)
```
┌──────────────────────────────────────────────────────────────────┐
│ Pending Reminders                                                │
├──────────────────────────────────────────────────────────────────┤
│ Patient      │ Type        │ Scheduled     │ Channel │ Actions  │
│ ────────────────────────────────────────────────────────────────│
│ Ram Lal      │ Appointment │ Today 6 PM    │ WA      │ [Cancel] │
│ Priya Sharma │ Lab Due     │ Today 6 PM    │ SMS     │ [Cancel] │
│ Amit Kumar   │ Appointment │ Tomorrow 6 PM │ WA      │ [Cancel] │
└──────────────────────────────────────────────────────────────────┘
```

## Cost Considerations

| Channel | Cost (India) | Notes |
|---------|--------------|-------|
| WhatsApp | Free* | Via personal WhatsApp, user interaction required |
| WhatsApp Business API | ₹0.50-1.00/msg | Requires Meta approval |
| SMS (Transactional) | ₹0.15-0.25/msg | Need DLT registration |

*Free approach opens WhatsApp Web; doctor must click send

## Out of Scope

- Two-way SMS/WhatsApp (patient replies)
- Bulk marketing messages
- Voice call reminders
- Email reminders

## Dependencies

- Appointment Calendar (#20)
- WhatsApp Integration (#19)
- SMS Gateway account

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SMS costs add up | Expense | Default to WhatsApp, SMS as fallback |
| Spam complaints | Blocked number | Easy opt-out, limit frequency |
| DLT registration complex | Can't send SMS | Use WhatsApp only initially |
| Reminder sent, appt cancelled | Confusion | Sync reminder queue with appt status |

## Open Questions

- [x] WhatsApp Business vs personal? **Decision: Personal for MVP (manual send)**
- [x] SMS gateway? **Decision: MSG91 for Indian SMS**
- [x] Who pays for SMS? **Decision: Doctor (operational cost)**

---
*Spec created: 2026-01-02*
