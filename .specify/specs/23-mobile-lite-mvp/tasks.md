# Mobile Lite MVP - Implementation Tasks

## Phase 1: Foundation (Day 1-2)

### 1.1 Project Setup
- [ ] Create `docassist_mobile/` directory structure
- [ ] Create `requirements.txt` with mobile dependencies
- [ ] Create `main.py` entry point
- [ ] Set up shared imports from desktop (`tokens.py`, `schemas.py`)
- [ ] Verify Flet mobile build works (`flet build apk` / `flet build ipa`)

### 1.2 Design System Integration
- [ ] Copy/symlink `tokens.py` from desktop
- [ ] Copy/symlink `themes.py` from desktop
- [ ] Create mobile-specific `navigation.py` (bottom nav bar)
- [ ] Test design tokens render correctly on mobile

## Phase 2: Core Services (Day 3-4)

### 2.1 Authentication Service
- [ ] Create `auth_service.py`
- [ ] Implement `authenticate(email, password)` → returns token + key
- [ ] Implement `logout()` → clears credentials
- [ ] Implement secure credential storage (keychain/keystore)
- [ ] Handle auth errors gracefully

### 2.2 Sync Client Service
- [ ] Create `sync_client.py`
- [ ] Implement `download_backup(token)` → downloads encrypted blob
- [ ] Implement `decrypt_backup(blob, key)` → returns SQLite file
- [ ] Implement `get_sync_status()` → last sync time, pending changes
- [ ] Implement background sync with exponential backoff
- [ ] Handle network failures gracefully

### 2.3 Local Database Service
- [ ] Create `local_db.py`
- [ ] Implement `get_all_patients()` → list of patients
- [ ] Implement `search_patients(query)` → filtered list
- [ ] Implement `get_patient(id)` → single patient with details
- [ ] Implement `get_patient_visits(patient_id)` → visit history
- [ ] Implement `get_patient_investigations(patient_id)` → lab results
- [ ] Implement `get_patient_procedures(patient_id)` → procedures
- [ ] Implement `get_todays_appointments()` → today's schedule
- [ ] Optimize queries with proper indexes

## Phase 3: UI Screens (Day 5-8)

### 3.1 Login Screen
- [ ] Create `login_screen.py`
- [ ] Email input field
- [ ] Password input field
- [ ] "Login" button with loading state
- [ ] Error message display
- [ ] "Forgot password" link (opens web browser)
- [ ] Premium styling matching desktop

### 3.2 Home Screen
- [ ] Create `home_screen.py`
- [ ] Today's appointments section (scrollable)
- [ ] Quick access to recent patients
- [ ] Sync status indicator
- [ ] Pull-to-refresh gesture
- [ ] Empty state when no appointments

### 3.3 Patient List Screen
- [ ] Create `patient_list.py`
- [ ] Search bar at top (sticky)
- [ ] Scrollable patient list with lazy loading
- [ ] Patient card component (name, age, gender, last visit)
- [ ] Tap to navigate to detail
- [ ] Empty state for no results
- [ ] Alphabet quick-scroll (optional)

### 3.4 Patient Detail Screen
- [ ] Create `patient_detail.py`
- [ ] Header: name, UHID, age, gender, phone
- [ ] Quick action buttons: Call, Share Rx, Add Appointment
- [ ] Tabbed view: Visits | Labs | Procedures
- [ ] Visits tab: expandable visit cards
- [ ] Labs tab: lab results with abnormal highlighting
- [ ] Procedures tab: procedure list
- [ ] Back navigation

### 3.5 Settings Screen
- [ ] Create `settings_screen.py`
- [ ] Account info (logged in as...)
- [ ] Sync status and manual sync button
- [ ] Dark mode toggle
- [ ] About section (version, support link)
- [ ] Logout button with confirmation

### 3.6 Navigation
- [ ] Create `navigation.py`
- [ ] Bottom navigation bar: Home | Patients | Settings
- [ ] Active state indication
- [ ] Smooth transitions between screens

## Phase 4: Components (Day 5-8, parallel with screens)

### 4.1 Patient Card
- [ ] Create `patient_card.py`
- [ ] Avatar with initials
- [ ] Name (primary text)
- [ ] Age/gender (secondary text)
- [ ] Last visit date
- [ ] Tap ripple effect
- [ ] Selected state

### 4.2 Visit Card
- [ ] Create `visit_card.py`
- [ ] Date header
- [ ] Chief complaint preview
- [ ] Diagnosis chips
- [ ] Expandable for full details
- [ ] Prescription summary

### 4.3 Lab Card
- [ ] Create `lab_card.py`
- [ ] Test name
- [ ] Result with unit
- [ ] Reference range
- [ ] Abnormal indicator (red/yellow)
- [ ] Date

### 4.4 Appointment Card
- [ ] Create `appointment_card.py`
- [ ] Time prominently displayed
- [ ] Patient name
- [ ] Tap to view patient

### 4.5 Sync Indicator
- [ ] Create `sync_indicator.py`
- [ ] Synced state (green checkmark + time)
- [ ] Syncing state (spinner)
- [ ] Error state (red warning)
- [ ] Offline state (gray)

### 4.6 Search Bar
- [ ] Create `search_bar.py`
- [ ] Text input with search icon
- [ ] Clear button when has text
- [ ] Debounced search (300ms)
- [ ] Focus/blur states

## Phase 5: Integration & Polish (Day 9-10)

### 5.1 Share Service
- [ ] Create `share_service.py`
- [ ] Share prescription PDF via system share sheet
- [ ] WhatsApp deep link for prescription
- [ ] Handle missing share targets gracefully

### 5.2 Offline Handling
- [ ] Detect network status changes
- [ ] Show offline banner when disconnected
- [ ] Queue actions for later (appointments)
- [ ] Graceful degradation of features

### 5.3 Error Handling
- [ ] Global error boundary
- [ ] User-friendly error messages
- [ ] Retry mechanisms
- [ ] Crash reporting setup

### 5.4 Performance Optimization
- [ ] Profile on low-end device
- [ ] Optimize list rendering (virtualization)
- [ ] Image/asset optimization
- [ ] Reduce app bundle size

### 5.5 Final Polish
- [ ] Review all animations (60fps)
- [ ] Check touch targets (48px minimum)
- [ ] Test dark mode consistency
- [ ] Accessibility review
- [ ] Hindi font rendering test

## Phase 6: Testing & Release (Day 11-14)

### 6.1 Testing
- [ ] Unit tests for services
- [ ] Integration tests for sync flow
- [ ] UI tests for critical paths
- [ ] Manual testing on Android
- [ ] Manual testing on iOS
- [ ] Test on low-end device (3GB RAM)

### 6.2 Build & Release Prep
- [ ] Create app icons (all sizes)
- [ ] Create splash screen
- [ ] Write App Store description
- [ ] Write Play Store description
- [ ] Prepare screenshots (phone + tablet if needed)
- [ ] Create privacy policy page
- [ ] Build release APK
- [ ] Build release IPA

### 6.3 Submission
- [ ] Submit to Google Play (internal testing)
- [ ] Submit to Apple TestFlight
- [ ] Address review feedback
- [ ] Promote to production

---

## Parallel Track: Cloud API

These tasks run parallel to mobile development:

### API Endpoints Needed
- [ ] `POST /auth/login` — authenticate doctor
- [ ] `GET /backup/latest` — get latest backup metadata
- [ ] `GET /backup/download/{id}` — download encrypted backup
- [ ] `GET /sync/status` — check if newer backup exists

### API Implementation
- [ ] Set up FastAPI/Flask backend
- [ ] Implement authentication (JWT)
- [ ] Connect to backup storage (S3/cloud)
- [ ] Deploy to cloud (Railway/Render/AWS)
- [ ] Set up SSL certificate
- [ ] Rate limiting and security

---

## Definition of Done

A task is complete when:
- [ ] Code is written and follows design system
- [ ] Works on both Android and iOS
- [ ] Works offline (for applicable features)
- [ ] Handles errors gracefully
- [ ] Has appropriate loading states
- [ ] Matches premium UI standards
- [ ] Has basic test coverage

---
*Tasks created: 2026-01-04*
