# DocAssist Mobile - Complete Guide

**Privacy-first mobile companion app for DocAssist EMR**

A premium mobile application built with Flet that provides doctors with on-the-go access to patient records, appointments, and clinical workflows.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
6. [Screens Reference](#screens-reference)
7. [Components Reference](#components-reference)
8. [Services Reference](#services-reference)
9. [Building for Mobile](#building-for-mobile)
10. [Development Guidelines](#development-guidelines)

---

## Overview

DocAssist Mobile is a **Mobile Lite** tier companion app that provides:
- **View-only access** to patient records (synced from desktop)
- **Quick patient search** (local SQLite, no LLM needed)
- **Today's appointments** at a glance
- **Quick note capture** with voice-to-text
- **Offline-first** architecture with background sync
- **Premium UX** with 60fps animations and haptic feedback

### Design Philosophy

- **Privacy-first**: All data stays on device, E2E encrypted sync
- **Offline-first**: App works immediately, syncs in background
- **Premium UX**: Smooth animations, haptic feedback, AMOLED dark mode
- **India-optimized**: Works on ₹10K phones, low RAM tolerance
- **48px touch targets**: Optimized for thumbs, not mouse
- **Skeleton screens**: Never show blank loading states

---

## Features

### Core Features (Mobile Lite)

✅ **Home Screen**
- Today's appointments with time and reason
- Recent patient access
- Sync status indicator
- Pull-to-refresh

✅ **Patient Directory**
- Searchable patient list (debounced search)
- Filter by recent, all, favorites
- Patient cards with demographics and last visit
- Infinite scroll / lazy loading

✅ **Patient Detail**
- Patient demographics and UHID
- Visit history (expandable cards)
- Lab results with abnormal flags
- Procedures timeline
- Prescription viewer
- Quick actions: Call, WhatsApp, Share

✅ **Quick Note**
- Large voice input button
- Text input fallback
- AI-extracted SOAP note preview
- Save as draft / Save to patient
- Works offline, syncs later

✅ **Settings**
- Sync status and manual sync
- Dark mode toggle
- Notification preferences
- Language selection (English/Hindi)
- Logout with confirmation

### Edit Capabilities (Phase 2)

✅ **Add Patient**
- Quick add with essential fields
- Gender selection with radio buttons
- Phone number validation
- Open patient after creation option

✅ **Add Visit**
- Chief complaint and clinical notes
- Multi-drug prescription builder
- AI-powered drug search
- Follow-up date picker

✅ **Add Lab Result**
- Test name with autocomplete
- Result, unit, reference range
- Abnormal flag (auto-detected)
- Test date picker

✅ **Schedule Appointment**
- Date and time picker
- Reason for visit
- Reminder settings

---

## Architecture

### Data Flow

```
┌─────────────────┐                    ┌─────────────────┐
│  Desktop EMR    │                    │   Mobile App    │
│  (Primary)      │                    │  (Companion)    │
├─────────────────┤                    ├─────────────────┤
│ SQLite + Chroma │                    │ SQLite (subset) │
│ Full LLM        │                    │ No LLM (Lite)   │
│ Full features   │                    │ Core features   │
└────────┬────────┘                    └────────▲────────┘
         │                                      │
         ▼                                      │
┌─────────────────────────────────────────────────────────┐
│              DocAssist Cloud (E2E Encrypted)            │
│  - Encrypted backup blobs (server cannot decrypt)       │
│  - Sync metadata (timestamps, patient count only)       │
│  - Conflict resolution via timestamp + device ID        │
└─────────────────────────────────────────────────────────┘
```

### Offline-First Strategy

1. **Immediate UI**: App shows cached data instantly
2. **Background Sync**: Auto-sync every 15 minutes
3. **Edit Queue**: Local edits queued for sync when online
4. **Conflict Detection**: Timestamp-based conflict resolution
5. **Manual Sync**: Pull-to-refresh on any screen

### Security & Privacy

- **E2E Encryption**: All cloud data encrypted on device
- **Zero-knowledge server**: Cloud cannot decrypt data
- **Local-first**: No patient data sent to cloud AI
- **Biometric auth**: Optional Face ID / Fingerprint
- **Auto-lock**: Configurable timeout (30s - 5min)

---

## Project Structure

```
docassist_mobile/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── README.md                        # This file
├── ANIMATIONS_HAPTICS.md           # Animation guidelines
├── EDIT_SCREENS_README.md          # Edit screens usage
├── PRESCRIPTION_USAGE.md           # Prescription viewer guide
│
├── src/
│   ├── __init__.py
│   │
│   ├── ui/                          # UI Layer
│   │   ├── __init__.py
│   │   ├── mobile_app.py           # Main app controller
│   │   ├── tokens.py               # Design tokens (colors, spacing, typography)
│   │   ├── animations.py           # Animation utilities
│   │   ├── haptics.py              # Haptic feedback
│   │   ├── navigation.py           # Navigation helpers
│   │   │
│   │   ├── screens/                # Screen components
│   │   │   ├── __init__.py
│   │   │   ├── home_screen.py              # Home with appointments
│   │   │   ├── patient_list.py             # Patient directory
│   │   │   ├── patient_detail.py           # Patient detail view
│   │   │   ├── quick_note_screen.py        # Quick clinical notes
│   │   │   ├── settings_screen.py          # Settings
│   │   │   ├── login_screen.py             # Login
│   │   │   ├── onboarding_screen.py        # First-time onboarding
│   │   │   ├── welcome_back_screen.py      # Returning user welcome
│   │   │   ├── add_patient_screen.py       # Add new patient
│   │   │   ├── add_visit_screen.py         # Add visit
│   │   │   ├── add_lab_screen.py           # Add lab result
│   │   │   ├── add_appointment_screen.py   # Schedule appointment
│   │   │   ├── edit_patient_screen.py      # Edit patient
│   │   │   ├── prescription_viewer.py      # View prescription
│   │   │   └── biometric_prompt.py         # Biometric auth
│   │   │
│   │   └── components/             # Reusable components
│   │       ├── __init__.py
│   │       ├── bottom_nav.py               # Bottom navigation bar
│   │       ├── patient_card.py             # Patient list item
│   │       ├── appointment_card.py         # Appointment card
│   │       ├── visit_card.py               # Visit card
│   │       ├── lab_card.py                 # Lab result card
│   │       ├── prescription_card.py        # Prescription card
│   │       ├── search_bar.py               # Search input
│   │       ├── sync_indicator.py           # Sync status
│   │       ├── sync_status_bar.py          # Pending changes bar
│   │       ├── floating_action_button.py   # FAB with speed dial
│   │       ├── speed_dial.py               # Speed dial menu
│   │       ├── skeleton.py                 # Skeleton loaders
│   │       ├── pull_to_refresh.py          # Pull to refresh
│   │       ├── page_indicator.py           # Onboarding dots
│   │       └── onboarding_page.py          # Onboarding page
│   │
│   ├── services/                    # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── local_db.py             # SQLite operations
│   │   ├── sync_client.py          # E2E encrypted sync
│   │   ├── sync_manager.py         # Sync orchestration
│   │   ├── auth_service.py         # Authentication
│   │   ├── biometric_service.py    # Biometric auth
│   │   ├── preferences_service.py  # User preferences
│   │   ├── pdf_service.py          # PDF generation/viewing
│   │   └── offline_queue.py        # Offline edit queue
│   │
│   └── models/                      # Data Models
│       ├── __init__.py
│       └── schemas.py              # Pydantic models
│
└── assets/                          # Static Assets
    └── icons/                       # App icons
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Flet 0.21.0+
- Active DocAssist account (for sync)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running Locally (Desktop Mode)

```bash
# Run as desktop app for development
python main.py
```

### Environment Variables

Create a `.env` file in `docassist_mobile/`:

```env
# API Configuration
API_BASE_URL=https://api.docassist.app
# or for local development:
# API_BASE_URL=http://localhost:8000

# Optional: Pre-populate email for testing
TEST_EMAIL=doctor@example.com
```

---

## Screens Reference

### 1. HomeScreen

**Purpose**: Today's appointments and quick access

**Key Features**:
- Today's appointment cards with time slots
- Recent patients (last 5 viewed)
- Sync status indicator
- Pull-to-refresh

**Usage**:
```python
from src.ui.screens import HomeScreen, AppointmentData

home = HomeScreen(
    on_appointment_click=handle_appointment_click,
    on_patient_click=handle_patient_click,
    on_refresh=handle_refresh,
    sync_status="synced",  # or "syncing"
    last_sync="2 mins ago",
)

# Set appointments
appointments = [
    AppointmentData(
        id=1,
        patient_id=42,
        patient_name="Ram Lal",
        time="10:30 AM",
        reason="Follow-up checkup",
    ),
]
home.set_appointments(appointments)
```

---

### 2. PatientListScreen

**Purpose**: Searchable patient directory

**Key Features**:
- Debounced search (300ms delay)
- Patient cards with avatar, demographics, last visit
- Infinite scroll
- Empty state for no results

**Usage**:
```python
from src.ui.screens import PatientListScreen, PatientData

patients = PatientListScreen(
    on_patient_click=handle_patient_click,
    on_search=handle_search,
)

# Set patient data
patient_data = [
    PatientData(
        id=1,
        name="Ram Lal",
        age=65,
        gender="M",
        phone="9876543210",
        last_visit="2 days ago",
    ),
]
patients.set_patients(patient_data)
```

---

### 3. PatientDetailScreen

**Purpose**: Complete patient record view

**Key Features**:
- Patient header with demographics
- Visit history (expandable cards)
- Lab results with abnormal highlighting
- Procedures timeline
- Quick actions: Call, WhatsApp, Share
- View prescriptions

**Usage**:
```python
from src.ui.screens import PatientDetailScreen, PatientInfo, VisitData, LabData

detail = PatientDetailScreen(
    patient=PatientInfo(
        id=1,
        name="Ram Lal",
        uhid="EMR-2024-0001",
        age=65,
        gender="M",
        phone="9876543210",
        address="123 Main St",
    ),
    on_back=handle_back,
    on_call=handle_call,
    on_share=handle_share_rx,
)

# Load visits
detail.set_visits([...])
detail.set_labs([...])
detail.set_procedures([...])
```

---

### 4. QuickNoteScreen

**Purpose**: Voice-to-text clinical notes

**Key Features**:
- Large voice recording button
- Text input fallback
- AI-extracted SOAP note preview (S/O/A/P)
- Save as draft or to patient
- Works offline, queued for sync

**Usage**:
```python
from src.ui.screens import QuickNoteScreen, QuickNoteData

quick_note = QuickNoteScreen(
    patient_id=42,  # Optional
    patient_name="Ram Lal",  # Optional
    on_save=handle_save_note,
    on_back=handle_back,
    haptic_feedback=haptic,
)

def handle_save_note(note_data: QuickNoteData):
    # note_data contains:
    # - patient_id
    # - note_text
    # - subjective, objective, assessment, plan (SOAP)
    # - created_at
    save_to_queue(note_data)
```

---

### 5. SettingsScreen

**Purpose**: App settings and sync control

**Key Features**:
- User profile (name, email)
- Database stats (patient count, visit count)
- Sync status and manual sync button
- Dark mode toggle
- Language selection
- Logout with confirmation

**Usage**:
```python
from src.ui.screens import SettingsScreen

settings = SettingsScreen(
    user_name="Dr. Kumar",
    user_email="kumar@example.com",
    patient_count=150,
    visit_count=1250,
    last_sync="Just now",
    is_dark_mode=False,
    app_version="1.0.0",
    on_sync=handle_sync,
    on_toggle_dark_mode=handle_dark_mode,
    on_logout=handle_logout,
)
```

---

### 6. AddPatientScreen

**Purpose**: Add new patient

**Key Features**:
- Essential fields (name, phone, age, gender)
- Gender radio buttons
- Phone validation
- Option to open patient after creation

**Usage**:
```python
from src.ui.screens import AddPatientScreen

add_patient = AddPatientScreen(
    on_back=handle_back,
    on_save=handle_save_patient,
    haptic_feedback=haptic,
)

def handle_save_patient(patient_data: dict, open_after: bool):
    patient_id = db.add_patient(**patient_data)
    if open_after:
        navigate_to_patient(patient_id)
```

See `EDIT_SCREENS_README.md` for more edit screens.

---

## Components Reference

### BottomNavBar

**Purpose**: Main navigation with 4 tabs

**Usage**:
```python
from src.ui.components import BottomNavBar, NavTab

nav = BottomNavBar(
    selected_tab=NavTab.HOME,
    on_change=handle_nav_change,
    notification_count=3,  # Badge on Quick Note tab
    haptic_feedback=haptic,
)

def handle_nav_change(tab: NavTab):
    if tab == NavTab.HOME:
        show_home()
    elif tab == NavTab.PATIENTS:
        show_patients()
    elif tab == NavTab.QUICK_NOTE:
        show_quick_note()
    elif tab == NavTab.SETTINGS:
        show_settings()
```

### PatientCard

**Purpose**: Patient list item with avatar

**Usage**:
```python
from src.ui.components import PatientCard

card = PatientCard(
    name="Ram Lal",
    age=65,
    gender="M",
    phone="9876543210",
    last_visit="2 days ago",
    on_click=lambda e: handle_click(patient_id),
    haptic_feedback=haptic,
)
```

### SyncIndicator

**Purpose**: Shows sync status

**Usage**:
```python
from src.ui.components import SyncIndicator

sync = SyncIndicator(
    status="synced",  # or "syncing", "error"
    last_sync="Just now",
)
```

### FloatingActionButton (FAB)

**Purpose**: Quick actions with speed dial

**Usage**:
```python
from src.ui.components import FloatingActionButton, FABAction

fab = FloatingActionButton(
    actions=[
        FABAction(icon=ft.Icons.PERSON_ADD, label="Add Patient", on_click=...),
        FABAction(icon=ft.Icons.NOTE_ADD, label="New Visit", on_click=...),
        FABAction(icon=ft.Icons.SCIENCE, label="Add Lab", on_click=...),
    ],
    page=page,
    haptic_feedback=haptic,
)
```

See component files for complete documentation.

---

## Services Reference

### LocalDatabase

**Purpose**: SQLite operations with offline queue

**Usage**:
```python
from src.services.local_db import LocalDatabase

db = LocalDatabase("data/clinic.db", enable_queue=True)

# Read operations
patients = db.get_all_patients(limit=100)
patient = db.get_patient(patient_id=1)
results = db.search_patients("Ram")
visits = db.get_patient_visits(patient_id=1)
labs = db.get_patient_investigations(patient_id=1)

# Write operations (queued for sync)
patient_id = db.add_patient(name="Ram Lal", age=65, gender="M")
op_id = db.add_visit_queued(patient_id=1, visit_data={...})
```

### SyncClient

**Purpose**: E2E encrypted cloud sync

**Usage**:
```python
from src.services.sync_client import SyncClient

sync = SyncClient(data_dir="data")
sync.set_credentials(auth_token, encryption_key)

# Manual sync
sync.sync(background=True)

# Get status
status = sync.get_sync_status()
last_sync_text = sync.get_last_sync_text()  # "2 mins ago"
```

### AuthService

**Purpose**: User authentication

**Usage**:
```python
from src.services.auth_service import AuthService

auth = AuthService()

# Login
success = auth.login(email, password)
if success:
    token = auth.get_token()
    key = auth.get_encryption_key()

# Check auth
if auth.is_authenticated():
    user_name, email = auth.get_user_info()

# Logout
auth.logout()
```

---

## Building for Mobile

### Android (APK)

```bash
# Build APK
flet build apk

# Output: build/apk/docassist_mobile.apk
```

### iOS (IPA)

```bash
# Build IPA (requires macOS + Xcode)
flet build ipa

# Output: build/ipa/docassist_mobile.ipa
```

### Build Configuration

Edit `flet.yaml` for app metadata:

```yaml
name: DocAssist
description: Privacy-first EMR for Indian doctors
version: 1.0.0
build_number: 1

android:
  package: app.docassist.mobile
  min_sdk_version: 21
  target_sdk_version: 33

ios:
  bundle_id: app.docassist.mobile
  deployment_target: 13.0
```

---

## Development Guidelines

### 1. Design Tokens (tokens.py)

**Always use design tokens, never hardcode values**:

```python
from src.ui.tokens import Colors, MobileSpacing, MobileTypography, Radius

# ✅ Good
ft.Text("Hello", color=Colors.NEUTRAL_900, size=MobileTypography.BODY_LARGE)
ft.Container(padding=MobileSpacing.CARD_PADDING, border_radius=Radius.MD)

# ❌ Bad
ft.Text("Hello", color="#1A1A1A", size=16)
ft.Container(padding=12, border_radius=8)
```

### 2. Haptic Feedback

**Add haptic feedback for all interactions**:

```python
def handle_click(e):
    if self.haptic_feedback:
        self.haptic_feedback.light()  # Tap
        # or .medium() for button press
        # or .success() for completion
        # or .error() for errors
```

### 3. Animations

**Use built-in animation utilities**:

```python
from src.ui.animations import Animations

ft.Container(
    animate_scale=Animations.scale_tap(),  # Tap animation
    animate_opacity=Animations.fade_in(),   # Fade in
    scale=1.0,
)
```

### 4. Loading States

**Always show skeleton screens, never blank**:

```python
from src.ui.components import SkeletonPatientCard

if loading:
    return SkeletonPatientCard()
else:
    return PatientCard(...)
```

### 5. Touch Targets

**Minimum 48px for all interactive elements**:

```python
# ✅ Good
ft.IconButton(icon=ft.Icons.SETTINGS, icon_size=24)  # Button is 48x48

# ❌ Bad
ft.GestureDetector(
    content=ft.Icon(ft.Icons.SETTINGS, size=16),  # Too small
)
```

### 6. Offline-First

**All features must work offline**:

```python
# Queue writes for sync
if db.enable_queue:
    operation_id = db.add_visit_queued(patient_id, data)
    show_snackbar("Visit saved. Will sync when online.")

# Reads always work (from cache)
visits = db.get_patient_visits(patient_id)
```

### 7. Error Handling

**Graceful degradation, never crash**:

```python
try:
    data = fetch_from_db()
except Exception as e:
    logger.error(f"DB error: {e}")
    show_error_state("Couldn't load data. Try again.")
```

---

## Testing

### Manual Testing Checklist

- [ ] App works with no internet (airplane mode)
- [ ] Sync works after going back online
- [ ] Animations are smooth (60fps)
- [ ] Haptic feedback on all interactions
- [ ] Dark mode works correctly
- [ ] Touch targets are 48px minimum
- [ ] Loading states show skeletons
- [ ] Back button works on all screens

### Test Data

Use the desktop app to create test patients and sync to mobile.

---

## Performance Optimization

### 1. Lazy Loading

Lists use lazy loading with pagination:

```python
patients = db.get_all_patients(limit=50, offset=page * 50)
```

### 2. Debounced Search

Search has 300ms debounce to avoid excessive queries:

```python
search_bar = SearchBar(
    on_search=debounced_search,
    debounce_ms=300,
)
```

### 3. Background Sync

Sync happens in background thread, never blocks UI:

```python
sync_client.sync(background=True)  # Non-blocking
```

---

## Troubleshooting

### "Database not found" error

**Solution**: Login and sync first. Database is created after first sync.

### Sync not working

**Solution**: Check credentials:
```python
auth_service.is_authenticated()  # Should be True
```

### Dark mode not applying

**Solution**: Ensure page.theme_mode is set:
```python
page.theme_mode = ft.ThemeMode.DARK
page.update()
```

---

## Roadmap

### Phase 1: Mobile Lite MVP ✅ (Current)
- View patient records
- Quick search
- Today's appointments
- Quick notes
- Offline sync

### Phase 2: Edit Capabilities ✅ (Complete)
- Add patients
- Add visits
- Add lab results
- Schedule appointments

### Phase 3: On-device LLM (Q2 2026)
- Gemma 2B integration
- AI-powered search
- Smart prescription suggestions
- Voice transcription

### Phase 4: Cloud LLM Option (Q3 2026)
- Opt-in cloud AI
- Faster inference
- Advanced diagnostics

### Phase 5: Multi-device Sync (Q4 2026)
- Real-time sync across devices
- Conflict resolution UI
- Collaborative features

---

## Support

**Documentation**: See individual README files in subdirectories
**Issues**: Report to tech@docassist.app
**Community**: Join our Discord (link in desktop app)

---

## License

Proprietary. Copyright © 2024 DocAssist Technologies Pvt Ltd.

---

**Built with ❤️ for Indian doctors**
