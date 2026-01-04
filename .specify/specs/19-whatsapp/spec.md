# Feature: WhatsApp Prescription Sharing

> Share prescriptions with patients via WhatsApp for easy access

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Paper prescriptions get lost. Patients forget to bring them to the pharmacy. Sharing a digital copy via WhatsApp (India's dominant messaging app) would ensure patients always have their prescription accessible.

## User Stories

### Primary User Story
**As a** doctor
**I want to** share prescriptions via WhatsApp
**So that** patients have easy access to their prescription

### Additional Stories
- As a doctor, I want to share with one click after printing
- As a doctor, I want to share the PDF, not just text
- As a patient, I want to receive the prescription on my phone

## Requirements

### Functional Requirements

**Share Flow:**
1. **FR-1**: "Share via WhatsApp" button after generating prescription
2. **FR-2**: Pre-populate patient's phone number
3. **FR-3**: Open WhatsApp with PDF attached
4. **FR-4**: Works on desktop via WhatsApp Web/Desktop

**Content:**
5. **FR-5**: Share prescription PDF
6. **FR-6**: Include brief text message with prescription
7. **FR-7**: Option to share text-only version

**Tracking:**
8. **FR-8**: Log when prescription was shared
9. **FR-9**: Show "Shared via WhatsApp" indicator on visit

### Non-Functional Requirements
1. **NFR-1**: One-click sharing (minimal steps)
2. **NFR-2**: Works without installing additional software
3. **NFR-3**: No data stored on external servers

## Acceptance Criteria

- [ ] "Share" button visible after generating Rx
- [ ] Clicking opens WhatsApp with patient number
- [ ] PDF attached to message
- [ ] Text message previews prescription content
- [ ] Works via WhatsApp Web link
- [ ] Visit shows "Shared" indicator after sharing

## Technical Approach

### Option 1: WhatsApp Web API (Recommended)
```python
import urllib.parse
import webbrowser

def share_via_whatsapp(phone: str, message: str, pdf_path: str = None):
    # Clean phone number (add country code)
    phone = phone.replace("+", "").replace(" ", "")
    if not phone.startswith("91"):
        phone = "91" + phone

    # Encode message
    encoded_message = urllib.parse.quote(message)

    # WhatsApp Web URL
    whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"

    # Open in browser
    webbrowser.open(whatsapp_url)

    # Note: PDF must be attached manually or via WhatsApp Desktop API
```

### Option 2: WhatsApp Business API (Requires approval)
- More control but requires Meta Business approval
- Overkill for single-doctor use

### Option 3: WhatsApp Desktop (if installed)
```python
# Use pyautogui or similar to automate WhatsApp Desktop
# More complex, less reliable
```

## UI Design

### Share Button
```
┌──────────────────────────────────────────────────────────────────┐
│ Prescription generated successfully!                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [🖨️ Print]   [📥 Download PDF]   [📱 Share via WhatsApp]        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### WhatsApp Message Preview
```
┌─────────────────────────────────────────┐
│ Share Prescription                  [X] │
├─────────────────────────────────────────┤
│                                         │
│ To: 9876543210 (Ram Lal)               │
│                                         │
│ Message:                                │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Prescription from Kumar Clinic  │ │
│ │ Patient: Ram Lal                   │ │
│ │ Date: 02-Jan-2026                  │ │
│ │                                    │ │
│ │ Diagnosis: Type 2 Diabetes         │ │
│ │                                    │ │
│ │ Please find attached PDF.         │ │
│ │                                    │ │
│ │ Next follow-up: 2 weeks           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 📎 Prescription_RamLal_020126.pdf      │
│                                         │
├─────────────────────────────────────────┤
│              [Cancel]  [Open WhatsApp]  │
└─────────────────────────────────────────┘
```

## Message Template

```
📋 *Prescription from {clinic_name}*
━━━━━━━━━━━━━━━━━━

*Patient:* {patient_name}
*Date:* {date}

*Diagnosis:* {diagnosis}

*Medications:*
{medications_list}

*Advice:*
{advice_list}

*Follow-up:* {follow_up}

━━━━━━━━━━━━━━━━━━
_This is a computer-generated prescription._
```

## Limitations

1. **PDF Attachment**: WhatsApp Web API doesn't support file attachment via URL. User must:
   - Download PDF first
   - Attach manually in WhatsApp
   - Or use WhatsApp Desktop with file copy

2. **Workaround**: Open WhatsApp with message, prompt user to attach PDF that was auto-opened/saved

## Out of Scope

- Automated sending without user interaction
- Bulk prescription sharing
- WhatsApp Business catalog integration
- Read receipts tracking

## Dependencies

- PDF generation (existing)
- Patient phone number in database

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WhatsApp Web URL scheme changes | Feature breaks | Monitor, update URL |
| No WhatsApp on doctor's computer | Can't share | Fallback to SMS or download |
| Wrong phone number | Sent to wrong person | Confirm before sending |

## Privacy Considerations

- Prescription contains PHI
- User must consent to digital sharing
- No data stored on third-party servers
- WhatsApp's E2E encryption protects in transit

## Open Questions

- [x] How to attach PDF? **Decision: Download PDF, open WhatsApp with message, user attaches manually**
- [x] SMS fallback? **Decision: Future enhancement**

---
*Spec created: 2026-01-02*
