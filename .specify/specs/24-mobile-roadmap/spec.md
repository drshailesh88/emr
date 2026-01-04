# DocAssist Mobile - Comprehensive Product Roadmap

> Master roadmap covering all phases from MVP to full-featured mobile EMR with AI capabilities

## Current State Analysis (As of 2026-01-04)

### What's Built

| Category | Status | Files | Notes |
|----------|--------|-------|-------|
| **Core App Structure** | COMPLETE | `mobile_app.py` | Navigation, theming, page routing |
| **Authentication** | COMPLETE | `auth_service.py` | Cloud login, token management |
| **Sync Infrastructure** | COMPLETE | `sync_client.py`, `sync_manager.py` | E2E encrypted backup download |
| **Local Database** | COMPLETE | `local_db.py` | SQLite read + write operations |
| **Patient List** | COMPLETE | `patient_list.py` | Search, skeleton loading, animations |
| **Patient Detail** | COMPLETE | `patient_detail.py` | Tabs for visits, labs, procedures, Rx |
| **Home Screen** | COMPLETE | `home_screen.py` | Appointments, sync status |
| **Settings Screen** | COMPLETE | `settings_screen.py` | Account, sync, dark mode |
| **Onboarding** | COMPLETE | `onboarding_screen.py` | 4-page flow, page indicators |
| **Welcome Back** | COMPLETE | `welcome_back_screen.py` | Returning user greeting |
| **Biometric Auth** | COMPLETE | `biometric_service.py`, `biometric_prompt.py` | Face ID/Fingerprint |
| **FAB Quick Actions** | COMPLETE | `floating_action_button.py` | Expandable + speed dial |
| **Add Patient** | COMPLETE | `add_patient_screen.py` | Quick patient entry |
| **Offline Queue** | COMPLETE | `offline_queue.py` | SQLite-backed pending changes |
| **Pull-to-Refresh** | COMPLETE | `pull_to_refresh.py` | Premium animations |
| **Sync Status Bar** | COMPLETE | `sync_status_bar.py` | Pending changes indicator |
| **Prescription Viewer** | COMPLETE | `prescription_viewer.py` | View + share PDFs |
| **PDF Service** | COMPLETE | `pdf_service.py` | Generate + cache PDFs |
| **Design System** | COMPLETE | `tokens.py`, `animations.py`, `haptics.py` | Premium UX |
| **Skeleton Loaders** | COMPLETE | `skeleton.py` | Loading states |
| **Cloud API** | COMPLETE | `cloud-api/` | FastAPI backend |

### What's Built but NOT Wired

These screens exist but show "coming soon" when accessed from FAB:

| Screen | File Exists | Wired to Mobile App |
|--------|-------------|---------------------|
| Add Visit | `add_visit_screen.py` | NO - shows snackbar |
| Add Lab | `add_lab_screen.py` | NO - shows snackbar |
| Add Appointment | `add_appointment_screen.py` | NO - shows snackbar |
| Edit Patient | `edit_patient_screen.py` | NO - not connected |

### Original MVP Spec Status

From `.specify/specs/23-mobile-lite-mvp/spec.md`:

| Requirement | Status | Notes |
|-------------|--------|-------|
| FR-1: Download encrypted backup | DONE | `sync_client.py` |
| FR-2: Decrypt backup locally | DONE | `sync_client.py` |
| FR-3: Store SQLite locally | DONE | `local_db.py` |
| FR-4: Background sync | DONE | `sync_manager.py` |
| FR-5: Show last sync timestamp | DONE | `home_screen.py` |
| FR-6: Graceful sync failures | DONE | Error states, retry |
| FR-7: Scrollable patient list | DONE | `patient_list.py` |
| FR-8: Search by name/UHID/phone | DONE | Local SQLite search |
| FR-9: Patient card display | DONE | `patient_card.py` |
| FR-10: Tap to view details | DONE | Navigation |
| FR-11: Patient header | DONE | `patient_detail.py` |
| FR-12: Tabbed view | DONE | Visits, Labs, Procedures, Rx |
| FR-13: Visits tab | DONE | `visit_card.py` |
| FR-14: Labs tab | DONE | `lab_card.py`, abnormal flags |
| FR-15: Procedures tab | DONE | `patient_detail.py` |
| FR-16: Expand visit details | PARTIAL | Card shows summary |
| FR-17: Call Patient | DONE | Opens dialer |
| FR-18: Share Prescription | DONE | `pdf_service.py` |
| FR-19: Add Appointment | PARTIAL | Screen exists, not wired |
| FR-20: Today's appointments | DONE | `home_screen.py` |
| FR-21: Tap appointment | DONE | Opens patient detail |
| FR-22: Appointment time/name | DONE | `appointment_card.py` |
| FR-23: Cloud login | DONE | `login_screen.py` |
| FR-24: Logout with clear | DONE | `settings_screen.py` |
| FR-25: Manual sync | DONE | Settings + pull-to-refresh |
| FR-26: Dark mode | DONE | Toggle in settings |
| FR-27: About screen | DONE | App version info |

**MVP Completion: ~95%** - Only need to wire remaining screens.

---

## Phase 1: Complete MVP (1 Week)

### Priority 1.1: Wire Existing Screens

**Status**: Screens exist, just need routing

| Task | Effort | Priority |
|------|--------|----------|
| Wire Add Visit screen to FAB | 2 hours | P0 |
| Wire Add Lab screen to FAB | 2 hours | P0 |
| Wire Add Appointment screen to FAB | 2 hours | P0 |
| Add "Edit" button on patient detail | 1 hour | P0 |
| Wire Edit Patient screen | 1 hour | P0 |
| Add visit/lab/appointment write to local_db | 4 hours | P0 |
| Queue writes for sync | 2 hours | P0 |

### Priority 1.2: Visit Detail Expansion

**Status**: Cards show summary, need full expansion

| Task | Effort | Priority |
|------|--------|----------|
| Create VisitDetailScreen | 4 hours | P1 |
| Show full clinical notes | 1 hour | P1 |
| Show full prescription | 2 hours | P1 |
| Navigate from VisitCard tap | 1 hour | P1 |

### Priority 1.3: Testing & Polish

| Task | Effort | Priority |
|------|--------|----------|
| Test on real Android device | 4 hours | P0 |
| Test on real iOS device | 4 hours | P0 |
| Fix any Flet mobile build issues | 8 hours | P0 |
| Performance profiling (60fps check) | 4 hours | P1 |
| Accessibility audit | 4 hours | P2 |

---

## Phase 2: Production Hardening (2 Weeks)

### Priority 2.1: Error Handling & Edge Cases

| Task | Description | Effort |
|------|-------------|--------|
| Network error recovery | Retry with exponential backoff, offline banner | 4 hours |
| Database corruption recovery | Detect, re-sync from cloud | 6 hours |
| Auth token refresh | Auto-refresh before expiry | 4 hours |
| Session timeout handling | Re-authenticate gracefully | 4 hours |
| Large database optimization | Pagination for 10K+ patients | 8 hours |
| Low storage warning | Alert when device storage low | 2 hours |

### Priority 2.2: Security Hardening

| Task | Description | Effort |
|------|-------------|--------|
| Certificate pinning | Prevent MITM attacks | 4 hours |
| Root/jailbreak detection | Warn users on compromised devices | 4 hours |
| Screenshot prevention | Disable screenshots of patient data | 2 hours |
| Session lock on background | Require re-auth after X minutes | 4 hours |
| Audit logging | Track all data access | 6 hours |

### Priority 2.3: Observability

| Task | Description | Effort |
|------|-------------|--------|
| Crash reporting (Sentry/Firebase) | Track errors in production | 4 hours |
| Analytics (privacy-preserving) | Track feature usage, no PII | 6 hours |
| Performance monitoring | Track sync times, load times | 4 hours |
| Health check endpoint | Server availability monitoring | 2 hours |

---

## Phase 3: Mobile Pro - On-Device AI (4 Weeks)

### CLAUDE.md Tier 2 Requirements

```
Tier 2: DocAssist Mobile Pro
- On-device LLM: Gemma 2B (~1.5GB) via llama.cpp or MLC-LLM
- Features:
  - AI-powered natural language patient search
  - Quick prescription generation
  - Voice-to-text clinical notes
- Privacy: High — all processing on-device
```

### Priority 3.1: On-Device LLM Integration

| Task | Description | Effort |
|------|-------------|--------|
| Research: llama.cpp vs MLC-LLM | Benchmark on target devices | 8 hours |
| Integrate LLM runtime | Add llama.cpp Python bindings | 16 hours |
| Model download system | Download Gemma 2B on-demand | 8 hours |
| Model storage management | Store in app cache, clear option | 4 hours |
| RAM-based model selection | Detect device RAM, pick model size | 4 hours |
| Battery optimization | LLM inference only when needed | 8 hours |
| Progress indicator | Show model loading progress | 4 hours |

### Priority 3.2: Natural Language Patient Search

| Task | Description | Effort |
|------|-------------|--------|
| Create MobileRAG service | ChromaDB-lite for mobile | 16 hours |
| Patient embedding generation | Embed patient summaries | 8 hours |
| Query embedding | Embed search queries | 4 hours |
| Vector similarity search | Find relevant patients | 4 hours |
| LLM response generation | Generate natural answers | 8 hours |
| Search UI integration | Replace simple search | 8 hours |

**Example queries**:
- "patients with diabetes on metformin"
- "who had an MI last year"
- "recent abnormal creatinine results"

### Priority 3.3: Voice-to-Text Clinical Notes

| Task | Description | Effort |
|------|-------------|--------|
| Integrate Whisper.cpp | On-device speech recognition | 16 hours |
| Whisper model download | Download whisper-small on-demand | 4 hours |
| Recording UI | Microphone button, waveform | 8 hours |
| Real-time transcription | Stream audio to Whisper | 12 hours |
| Clinical note formatting | Structure transcribed text | 8 hours |
| Dictation in AddVisit screen | Voice input for notes | 4 hours |

### Priority 3.4: Quick Prescription Generation

| Task | Description | Effort |
|------|-------------|--------|
| Prescription prompt template | Optimize for Gemma 2B | 4 hours |
| Drug database on mobile | Subset of desktop drug DB | 8 hours |
| LLM prescription generation | Generate from notes/diagnosis | 8 hours |
| Prescription validation | Check for drug interactions | 8 hours |
| Edit + confirm flow | Doctor reviews AI output | 4 hours |

---

## Phase 4: Mobile Cloud - Cloud AI (2 Weeks)

### CLAUDE.md Tier 3 Requirements

```
Tier 3: DocAssist Mobile Cloud
- Cloud LLM: API calls to privacy-respecting service
- Explicit Consent Flow with anonymization
- Best for: Doctors who prioritize speed over maximum privacy
```

### Priority 4.1: Cloud AI Infrastructure

| Task | Description | Effort |
|------|-------------|--------|
| Cloud AI API design | Endpoints for completion | 8 hours |
| Data anonymization pipeline | Strip PII before sending | 12 hours |
| Consent flow UI | Clear warning + opt-in toggle | 4 hours |
| Cloud LLM integration | GPT-4, Claude API | 8 hours |
| Response de-anonymization | Restore patient context | 4 hours |
| Usage tracking | Track API calls for billing | 4 hours |

### Priority 4.2: Anonymization Pipeline

```python
# Before sending to cloud:
Original: "Ram Lal, 65M, came with chest pain. Cr 1.8"
Anonymized: "[Patient], [Age][Gender], came with chest pain. Cr 1.8"

# Names, phone numbers, addresses → placeholders
# Clinical data preserved for context
```

| Task | Description | Effort |
|------|-------------|--------|
| Name detection + replacement | Regex + NER | 8 hours |
| Phone number stripping | All phone patterns | 2 hours |
| Address detection | Common address patterns | 4 hours |
| UHID replacement | EMR-XXXX → [UHID] | 1 hour |
| Reversible mapping | Restore context in response | 4 hours |

### Priority 4.3: Consent Management

| Task | Description | Effort |
|------|-------------|--------|
| First-time consent dialog | Explain what's sent, get consent | 4 hours |
| Per-query consent option | "Ask every time" mode | 4 hours |
| Consent audit log | Track all consent decisions | 4 hours |
| Revoke consent flow | Turn off cloud AI | 2 hours |
| Settings toggle | Cloud AI on/off | 2 hours |

---

## Phase 5: Advanced Features (6 Weeks)

### Priority 5.1: Push Notifications

| Task | Description | Effort |
|------|-------------|--------|
| FCM integration (Android) | Firebase Cloud Messaging | 8 hours |
| APNs integration (iOS) | Apple Push Notifications | 8 hours |
| Notification types design | Appointments, reminders, sync | 4 hours |
| Appointment reminders | 1 day, 1 hour before | 8 hours |
| Follow-up reminders | Remind doctor to check up | 8 hours |
| Abnormal lab alerts | Push when abnormal result synced | 8 hours |
| Notification preferences | Per-type on/off in settings | 4 hours |

### Priority 5.2: SMS Reminders to Patients

| Task | Description | Effort |
|------|-------------|--------|
| SMS gateway integration | Twilio/MSG91 for India | 8 hours |
| Appointment reminder SMS | "Your appointment is tomorrow at 10 AM" | 4 hours |
| Follow-up reminder SMS | "Time for your follow-up visit" | 4 hours |
| Medication reminder SMS | "Take your evening dose" | 8 hours |
| SMS templates | Customizable messages | 4 hours |
| SMS quota management | Track usage against plan | 4 hours |
| Professional tier gate | Only for ₹499+ plans | 2 hours |

### Priority 5.3: Multi-Language Support

| Task | Description | Effort |
|------|-------------|--------|
| i18n infrastructure | Flutter intl / ARB files | 8 hours |
| Hindi translation | All UI strings | 16 hours |
| Marathi translation | Regional language | 16 hours |
| Tamil translation | Regional language | 16 hours |
| Language picker in settings | Switch language | 4 hours |
| RTL support (if needed) | For Urdu | 8 hours |
| Prescription PDF in Hindi | Localized prescriptions | 8 hours |

### Priority 5.4: Widgets & Quick Actions

| Task | Description | Effort |
|------|-------------|--------|
| Android widget: Today's appointments | Glanceable widget | 12 hours |
| Android widget: Quick patient search | Search from home screen | 12 hours |
| iOS widget: Today's appointments | WidgetKit implementation | 12 hours |
| iOS widget: Quick patient search | WidgetKit implementation | 12 hours |
| Shortcuts/Siri integration | "Hey Siri, open patient Ram" | 16 hours |

### Priority 5.5: Appointment Booking (Patient-Facing)

| Task | Description | Effort |
|------|-------------|--------|
| Public booking page | Shareable URL for clinic | 16 hours |
| Available slots calculation | From doctor's schedule | 8 hours |
| Patient self-booking | Name, phone, reason | 8 hours |
| Booking confirmation SMS | Send to patient | 4 hours |
| Booking sync to mobile | Real-time or next sync | 4 hours |
| Booking management | Approve, reschedule, cancel | 8 hours |

---

## Phase 6: Enterprise Features (4 Weeks)

### Priority 6.1: Multi-User Support (Clinic Tier)

| Task | Description | Effort |
|------|-------------|--------|
| User roles: Admin, Doctor, Staff | Role-based permissions | 12 hours |
| Clinic admin dashboard | Manage users from mobile | 16 hours |
| Staff access: View-only | Limited permissions | 4 hours |
| Doctor assignment | Patients assigned to doctors | 8 hours |
| Audit trail per user | Track who accessed what | 8 hours |
| User invitation flow | Admin invites staff | 8 hours |

### Priority 6.2: Real-Time Sync (Hospital Tier)

| Task | Description | Effort |
|------|-------------|--------|
| WebSocket connection | Real-time updates | 16 hours |
| Conflict resolution UI | When desktop and mobile clash | 12 hours |
| Live collaboration indicators | "Dr. X is viewing this patient" | 8 hours |
| Push sync on save | Immediate sync, not periodic | 8 hours |
| Offline queue with priorities | Critical changes sync first | 8 hours |

### Priority 6.3: Audit Dashboard

| Task | Description | Effort |
|------|-------------|--------|
| Audit log viewer | Who accessed what, when | 12 hours |
| Export audit logs | CSV/PDF for compliance | 4 hours |
| Suspicious activity alerts | Unusual access patterns | 8 hours |
| Data access reports | Per-patient access history | 8 hours |

---

## App Store Strategy

### Android (Google Play)

| Task | Effort | Notes |
|------|--------|-------|
| App signing setup | 2 hours | Generate keystore |
| Store listing | 4 hours | Screenshots, description |
| Privacy policy | 4 hours | GDPR/India DPDP compliant |
| Feature graphic | 2 hours | 1024x500 banner |
| Build APK/AAB | 2 hours | `flet build apk` |
| Internal testing | 4 hours | Test on multiple devices |
| Closed beta | 8 hours | 100 doctors beta |
| Production release | 2 hours | Staged rollout |

### iOS (App Store)

| Task | Effort | Notes |
|------|--------|-------|
| Apple Developer account | 1 hour | $99/year |
| App Store Connect setup | 2 hours | Bundle ID, certificates |
| Store listing | 4 hours | Screenshots (all sizes) |
| Privacy labels | 4 hours | App privacy declaration |
| Build IPA | 4 hours | `flet build ipa` |
| TestFlight beta | 8 hours | 100 doctors beta |
| App Review submission | 2 hours | Respond to any issues |
| Production release | 2 hours | Phased release |

---

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| **Phase 1: Complete MVP** | 1 week | All screens wired, basic testing |
| **Phase 2: Production Hardening** | 2 weeks | Error handling, security, monitoring |
| **Phase 3: Mobile Pro (On-Device AI)** | 4 weeks | Gemma 2B, voice input, AI search |
| **Phase 4: Mobile Cloud** | 2 weeks | Cloud AI with consent, anonymization |
| **Phase 5: Advanced Features** | 6 weeks | Push notifications, SMS, widgets |
| **Phase 6: Enterprise** | 4 weeks | Multi-user, real-time sync, audit |

**Total: ~19 weeks** (4-5 months for full feature set)

---

## Revenue Milestones

| Phase | Features Unlocked | Pricing Impact |
|-------|-------------------|----------------|
| Phase 1 | Basic mobile access | Included in Essential (₹199/mo) |
| Phase 2 | Production-ready app | Table stakes |
| Phase 3 | On-device AI | Mobile Pro add-on (₹299/mo) |
| Phase 4 | Cloud AI | Included in Professional (₹499/mo) |
| Phase 5 | SMS reminders | Professional tier feature |
| Phase 6 | Multi-user | Clinic tier (₹2,499/mo) |

---

## Risk Registry

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Flet mobile build fails | High | Medium | Test early, have Flutter fallback |
| LLM too slow on phones | Medium | Medium | Allow cloud AI fallback |
| App Store rejection | High | Low | Follow guidelines, privacy-first |
| Battery drain from AI | Medium | High | Clear warnings, opt-in only |
| Large DB performance | Medium | Medium | Pagination, lazy loading |
| Sync conflicts | Medium | Medium | Last-write-wins + manual resolve |

---

## Success Metrics

| Metric | Phase 1 Target | Phase 3 Target | Phase 6 Target |
|--------|---------------|----------------|----------------|
| App Store rating | 4.0+ | 4.3+ | 4.5+ |
| Crash-free rate | 99% | 99.5% | 99.9% |
| DAU/MAU | 20% | 40% | 60% |
| Mobile → Desktop conversion | 5% | 15% | 25% |
| Pro tier adoption | - | 10% | 20% |
| Sync success rate | 95% | 99% | 99.9% |
| App launch time | <3s | <2s | <1.5s |
| Patient search latency | <1s | <500ms | <300ms |

---

*Roadmap created: 2026-01-04 | Owner: Product Team*
