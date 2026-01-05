# Feature: DocAssist Mobile Lite MVP

> A privacy-first mobile companion app that syncs patient records from desktop and provides view-only access with quick actions

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Indian doctors work across multiple locations — main clinic, satellite clinics, home, hospital rounds. The desktop EMR is powerful but creates friction when doctors need patient information away from their desk. Common scenarios:

1. **Home call from patient**: "Doctor, I'm having chest pain" — need to quickly look up their history
2. **Hospital rounds**: Checking recent lab values while at bedside
3. **Satellite clinic**: Verifying what was prescribed in main clinic
4. **After hours**: Reviewing tomorrow's appointments

Without mobile access, doctors either:
- Skip the EMR and rely on memory (dangerous)
- Call office staff to look up records (inconvenient)
- Don't adopt EMR at all (the worst outcome)

**Goal**: Remove the "I'm not at my desk" barrier to EMR adoption.

## User Stories

### Primary User Story
**As a** doctor away from my clinic
**I want to** view my patient records on my phone
**So that** I can make informed decisions even when I'm not at my desktop

### Additional Stories
- As a doctor, I want to search patients by name/phone so I can quickly find who's calling me
- As a doctor, I want to see today's appointments so I can prepare while commuting
- As a doctor, I want to view a patient's recent visits so I can recall their treatment history
- As a doctor, I want to see lab results so I can interpret values during hospital rounds
- As a doctor, I want to call a patient directly from the app so I can follow up easily
- As a doctor, I want to view prescriptions so I can answer "what medicines did you give me?" questions
- As a doctor, I want the app to work offline so I can use it even without internet

## Requirements

### Functional Requirements

#### Sync & Data
1. **FR-1**: App downloads encrypted backup from DocAssist Cloud on first setup
2. **FR-2**: App decrypts backup locally using doctor's password (same as desktop)
3. **FR-3**: App stores decrypted SQLite database locally for offline access
4. **FR-4**: App syncs in background when WiFi/mobile data available
5. **FR-5**: App shows last sync timestamp prominently
6. **FR-6**: App gracefully handles sync failures with retry

#### Patient List
7. **FR-7**: Display scrollable list of all patients (sorted by recent first)
8. **FR-8**: Search patients by name, UHID, or phone number
9. **FR-9**: Show patient card with name, age, gender, last visit date
10. **FR-10**: Tap patient to view details

#### Patient Detail View
11. **FR-11**: Show patient header (name, UHID, age, gender, phone)
12. **FR-12**: Show tabbed view: Visits | Labs | Procedures
13. **FR-13**: Visits tab: List of visits with date, chief complaint, diagnosis
14. **FR-14**: Labs tab: List of investigations with date, result, abnormal flag
15. **FR-15**: Procedures tab: List of procedures with date and details
16. **FR-16**: Tap on visit to expand and see full notes/prescription

#### Quick Actions
17. **FR-17**: "Call Patient" button that opens phone dialer with patient's number
18. **FR-18**: "Share Prescription" button to share last prescription PDF via WhatsApp/email
19. **FR-19**: "Add Appointment" quick action to schedule follow-up

#### Appointments
20. **FR-20**: Show today's appointments on home screen
21. **FR-21**: Tap appointment to jump to patient detail
22. **FR-22**: Show appointment time and patient name

#### Settings
23. **FR-23**: Login with DocAssist Cloud credentials
24. **FR-24**: Logout (clears local data)
25. **FR-25**: Manual sync button
26. **FR-26**: Dark mode toggle
27. **FR-27**: About screen with version info

### Non-Functional Requirements

1. **NFR-1**: Performance — App launches in < 2 seconds
2. **NFR-2**: Performance — Patient list scrolls at 60fps
3. **NFR-3**: Performance — Search returns results in < 500ms
4. **NFR-4**: Storage — App uses < 100MB base + patient data
5. **NFR-5**: Battery — Background sync uses minimal battery
6. **NFR-6**: Offline — All read operations work without internet
7. **NFR-7**: Security — Data encrypted at rest on device
8. **NFR-8**: Security — Password never stored, only derived key
9. **NFR-9**: Compatibility — Works on Android 8+ and iOS 13+
10. **NFR-10**: Compatibility — Works on phones with 3GB+ RAM
11. **NFR-11**: UX — Touch targets minimum 48px
12. **NFR-12**: UX — Follows premium design system from desktop

## Acceptance Criteria

### Sync
- [ ] Given a new install, when I enter my cloud credentials and password, then the app downloads and decrypts my patient database
- [ ] Given I'm offline, when I open the app, then I can still view all previously synced data
- [ ] Given I'm online, when I pull-to-refresh, then the app syncs latest data from cloud

### Patient List
- [ ] Given I have 500 patients, when I scroll the list, then it maintains 60fps with no jank
- [ ] Given I type "Ram" in search, when I wait 300ms, then I see patients matching "Ram"
- [ ] Given I search by phone "98765", when results appear, then matching patients are shown

### Patient Detail
- [ ] Given I tap a patient, when the detail view opens, then I see their header info immediately
- [ ] Given I'm viewing a patient, when I tap Visits tab, then I see their visit history
- [ ] Given I'm viewing a patient, when I tap Labs tab, then I see their lab results with abnormal flags

### Quick Actions
- [ ] Given I'm viewing a patient with a phone number, when I tap Call, then the phone dialer opens
- [ ] Given a patient has a recent prescription, when I tap Share, then I can send via WhatsApp

### Appointments
- [ ] Given I have 5 appointments today, when I open the app, then I see them on the home screen
- [ ] Given I tap an appointment, when the view changes, then I see that patient's details

### Offline
- [ ] Given I have no internet, when I open the app, then I see "Offline mode" indicator
- [ ] Given I'm offline, when I search patients, then search still works on local data

## Out of Scope (MVP)

These are NOT included in Mobile Lite MVP:

- **No editing**: Cannot add/edit visits, investigations, procedures
- **No prescription generation**: Requires desktop
- **No AI features**: No natural language search, no LLM
- **No voice input**: Requires on-device LLM
- **No real-time sync**: Only periodic background sync
- **No multi-user**: Single doctor per app instance
- **No push notifications**: Will be added in Phase 2

## Technical Architecture

### Directory Structure
```
docassist_mobile/
├── main.py                     # Entry point
├── requirements.txt            # Mobile-specific dependencies
├── assets/
│   ├── icons/                  # App icons (various sizes)
│   ├── splash/                 # Splash screen
│   └── fonts/                  # Noto Sans for Hindi
├── src/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── mobile_app.py       # Main Flet app
│   │   ├── screens/
│   │   │   ├── home_screen.py      # Appointments + quick access
│   │   │   ├── patient_list.py     # All patients
│   │   │   ├── patient_detail.py   # Single patient view
│   │   │   ├── login_screen.py     # Cloud login
│   │   │   └── settings_screen.py  # App settings
│   │   ├── components/
│   │   │   ├── patient_card.py     # Patient list item
│   │   │   ├── visit_card.py       # Visit summary
│   │   │   ├── lab_card.py         # Lab result item
│   │   │   ├── appointment_card.py # Today's appointment
│   │   │   ├── sync_indicator.py   # Sync status widget
│   │   │   └── search_bar.py       # Search input
│   │   └── navigation.py       # Bottom navigation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sync_client.py      # Download + decrypt backups
│   │   ├── local_db.py         # SQLite read operations
│   │   ├── auth_service.py     # Cloud authentication
│   │   └── share_service.py    # Share via WhatsApp/email
│   └── models/
│       └── schemas.py          # Shared with desktop (symlink or copy)
└── tests/
    ├── test_sync.py
    ├── test_local_db.py
    └── test_ui.py
```

### Shared Code from Desktop
```
Reuse from desktop (src/):
├── services/crypto.py      # 100% reuse — PyNaCl decryption
├── services/backup.py      # Partial — extraction only
├── models/schemas.py       # 100% reuse — Pydantic models
├── ui/tokens.py            # 100% reuse — design tokens
├── ui/themes.py            # 100% reuse — light/dark themes
└── ui/widgets/             # 80% reuse — buttons, cards
```

### Data Flow
```
┌─────────────────────────────────────────────────────────────┐
│                     Mobile App                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Login Screen                                             │
│     └─→ auth_service.authenticate(email, password)          │
│         └─→ Returns: cloud_token, encryption_key             │
│                                                              │
│  2. Initial Sync                                             │
│     └─→ sync_client.download_backup(cloud_token)            │
│         └─→ sync_client.decrypt(backup, encryption_key)     │
│             └─→ Extracts: clinic.db (SQLite)                │
│                                                              │
│  3. Local Storage                                            │
│     └─→ local_db.open("clinic.db")                          │
│         └─→ All reads from local SQLite                     │
│                                                              │
│  4. Background Sync (periodic)                               │
│     └─→ Check cloud for newer backup                        │
│         └─→ If newer: download, decrypt, merge              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Dependencies

### Internal Dependencies
- Desktop backup service (already implemented)
- Desktop crypto service (already implemented)
- DocAssist Cloud API (needs implementation)
- Shared design tokens (from premium UI branch)

### External Dependencies
- Flet >= 0.25.0 (mobile build support)
- PyNaCl (encryption — same as desktop)
- requests (HTTP client for cloud API)

### Infrastructure Dependencies
- DocAssist Cloud API endpoint for:
  - Authentication
  - Backup download
  - Sync status check

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flet mobile build issues | High | Test early on real devices, not just emulators |
| Large database slow on phone | Medium | Implement pagination, lazy loading |
| Encryption performance on old phones | Medium | Test on low-end devices, optimize if needed |
| Cloud API not ready | High | Build mock API first, parallel development |
| App Store rejection | Medium | Follow guidelines strictly, prepare privacy policy |

## Open Questions

- [x] Should we support tablet layout? **Decision: No, phone-first for MVP**
- [x] Should offline editing queue changes? **Decision: No, view-only for MVP**
- [ ] What's the minimum sync frequency? (Every 15 min? 1 hour? Manual only?)
- [ ] Should we encrypt SQLite on device or rely on OS encryption?
- [ ] Do we need biometric unlock (fingerprint/face)?

## Success Metrics

| Metric | Target |
|--------|--------|
| App Store rating | 4.5+ stars |
| Crash-free rate | 99.5%+ |
| App launch time | < 2 seconds |
| Daily active users | 30% of desktop users |
| Sync success rate | 99%+ |

---
*Spec created: 2026-01-04 | Last updated: 2026-01-04*
