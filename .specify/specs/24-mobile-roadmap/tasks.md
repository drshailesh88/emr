# DocAssist Mobile - Implementation Tasks

> Actionable task breakdown for all phases

## Immediate Priority: Complete Phase 1 (This Week)

### Task 1.1: Wire Add Visit Screen
**Effort**: 2 hours | **Priority**: P0

```
Files to modify:
- docassist_mobile/src/ui/mobile_app.py

Steps:
1. Add ADD_VISIT to Screen enum
2. Import AddVisitScreen from screens
3. In _handle_new_visit(), replace snackbar with:
   - Create AddVisitScreen with patient selector
   - Set on_save callback to save_visit_handler
   - Set on_back callback
   - Navigate to screen
4. Implement save_visit_handler():
   - Call local_db.add_visit_queued()
   - Show success snackbar
   - Navigate back to home/patient detail
5. Update _go_back() to handle ADD_VISIT screen
6. Update _update_fab_visibility() to hide FAB on ADD_VISIT
```

### Task 1.2: Wire Add Lab Screen
**Effort**: 2 hours | **Priority**: P0

```
Files to modify:
- docassist_mobile/src/ui/mobile_app.py

Steps:
1. Add ADD_LAB to Screen enum
2. Import AddLabScreen from screens
3. In _handle_add_lab(), replace snackbar with:
   - Create AddLabScreen with patient selector
   - Set on_save callback
   - Set on_save_and_add_another callback for batch entry
   - Navigate to screen
4. Implement save_lab_handler():
   - Call local_db.add_investigation_queued()
   - If "add another", clear form
   - Else navigate back
5. Add add_investigation_queued() to local_db if missing
```

### Task 1.3: Wire Add Appointment Screen
**Effort**: 2 hours | **Priority**: P0

```
Files to modify:
- docassist_mobile/src/ui/mobile_app.py
- docassist_mobile/src/services/local_db.py

Steps:
1. Add ADD_APPOINTMENT to Screen enum
2. Import AddAppointmentScreen from screens
3. In _handle_schedule_appointment(), navigate to screen
4. Implement save_appointment_handler():
   - Add appointments table to local_db if missing
   - Call local_db.add_appointment_queued()
   - Navigate back, refresh home screen
5. Update home_screen.py to show newly added appointments
```

### Task 1.4: Add Edit Button to Patient Detail
**Effort**: 2 hours | **Priority**: P0

```
Files to modify:
- docassist_mobile/src/ui/screens/patient_detail.py
- docassist_mobile/src/ui/mobile_app.py

Steps:
1. In patient_detail.py header, add Edit button (pencil icon)
2. Add on_edit callback parameter
3. In mobile_app.py, pass on_edit to PatientDetailScreen
4. Implement edit handler:
   - Navigate to EditPatientScreen with current patient data
   - On save, update local_db and refresh detail screen
5. Add update_patient_queued() to local_db
```

### Task 1.5: Create Visit Detail Screen
**Effort**: 4 hours | **Priority**: P1

```
Files to create:
- docassist_mobile/src/ui/screens/visit_detail_screen.py

Features:
1. Full-screen view of single visit
2. Header: Date, chief complaint
3. Section: Clinical Notes (full text, scrollable)
4. Section: Diagnosis
5. Section: Prescription
   - List all medications with details
   - Investigations advised
   - Advice
   - Follow-up
   - Red flags
6. "View PDF" button → Opens PrescriptionViewer
7. "Share" button → Share prescription
8. Back navigation

Integration:
- In patient_detail.py, make VisitCard tappable
- Pass on_visit_tap callback
- Navigate to VisitDetailScreen
```

### Task 1.6: Test on Real Devices
**Effort**: 8 hours | **Priority**: P0

```
Android Testing:
1. Build APK: flet build apk
2. Install on test device (Android 8+)
3. Test checklist:
   [ ] App launches in < 3 seconds
   [ ] Login works with cloud credentials
   [ ] Initial sync completes
   [ ] Patient list scrolls smoothly (60fps)
   [ ] Search returns results in < 500ms
   [ ] Patient detail loads correctly
   [ ] Tabs switch smoothly
   [ ] FAB expands/collapses correctly
   [ ] Add patient works
   [ ] Biometric prompt appears
   [ ] Dark mode toggles
   [ ] Pull-to-refresh works
   [ ] Offline mode works
   [ ] Background sync works

iOS Testing:
1. Build IPA: flet build ipa
2. Deploy via TestFlight or direct install
3. Same test checklist as Android
4. Additional: Haptics feel correct
```

---

## Phase 2 Tasks: Production Hardening

### Task 2.1: Network Error Recovery
**Effort**: 4 hours

```
Files to modify:
- docassist_mobile/src/services/sync_client.py
- docassist_mobile/src/ui/components/sync_status_bar.py

Implementation:
1. In sync_client.py, wrap API calls with retry logic:
   - Max 3 retries
   - Exponential backoff: 1s, 2s, 4s
   - Track consecutive failures
2. Create offline_banner component:
   - Detect network unavailable
   - Show "You're offline. Changes will sync when connected."
   - Dismiss on network return
3. Add network state listener (connectivity_plus equivalent)
4. Auto-trigger sync when network returns
```

### Task 2.2: Auth Token Refresh
**Effort**: 4 hours

```
Files to modify:
- docassist_mobile/src/services/auth_service.py
- cloud-api/src/auth/router.py

Implementation:
1. JWT tokens should have:
   - Access token: 15 min expiry
   - Refresh token: 7 day expiry
2. In auth_service.py:
   - Track token expiry time
   - Before any API call, check if token expires in < 5 min
   - If so, call refresh endpoint
3. Add POST /auth/refresh endpoint to cloud API
4. Handle refresh failure → redirect to login
```

### Task 2.3: Screenshot Prevention
**Effort**: 2 hours

```
Platform-specific implementation:

Android:
- Set FLAG_SECURE on window
- Flet equivalent: page.window_prevent_close or custom platform channel

iOS:
- Use UITextField.isSecureTextEntry trick
- Or use appropriate window security flag

Privacy setting:
- Add toggle in settings: "Allow screenshots"
- Default: OFF for patient screens
- Doctors can enable if needed
```

### Task 2.4: Crash Reporting Setup
**Effort**: 4 hours

```
Using Sentry (privacy-friendly):

1. Add sentry-sdk to requirements.txt
2. Initialize in main.py:
   sentry_sdk.init(
       dsn="...",
       traces_sample_rate=0.1,
       profiles_sample_rate=0.1,
       # CRITICAL: No PII
       before_send=strip_pii,
   )
3. Create strip_pii function:
   - Remove patient names
   - Remove phone numbers
   - Remove any health data
   - Keep: stack traces, device info, app version
4. Add release tracking
5. Set up Sentry dashboard alerts
```

---

## Phase 3 Tasks: On-Device AI

### Task 3.1: LLM Runtime Integration
**Effort**: 16 hours

```
Option A: llama.cpp (recommended)
1. Add llama-cpp-python to requirements
2. Create src/services/mobile_llm.py:
   class MobileLLM:
       def __init__(self, model_path: str):
           self.llm = Llama(
               model_path=model_path,
               n_ctx=2048,
               n_threads=4,
               n_gpu_layers=0,  # CPU only on mobile
           )

       async def generate(self, prompt: str) -> str:
           output = self.llm(prompt, max_tokens=512)
           return output['choices'][0]['text']
3. Model download UI:
   - Show download button
   - Progress bar during download
   - Store in app cache directory
   - Verify checksum
4. RAM detection:
   import psutil
   ram_gb = psutil.virtual_memory().total / (1024**3)
   if ram_gb < 4:
       model = "gemma-2b-q4"  # ~1.5GB
   else:
       model = "gemma-7b-q4"  # ~4GB
```

### Task 3.2: Voice Input (Whisper)
**Effort**: 16 hours

```
Implementation using whisper.cpp:

1. Add pywhispercpp to requirements
2. Create src/services/voice_service.py:
   class VoiceService:
       def __init__(self):
           self.model = Whisper("base.en")  # or multilingual

       async def transcribe(self, audio_path: str) -> str:
           result = self.model.transcribe(audio_path)
           return result["text"]
3. Recording UI component:
   - Microphone button (red when recording)
   - Animated waveform
   - Max recording time: 60 seconds
   - Save to temp file
4. Integration in AddVisitScreen:
   - Add mic button next to notes field
   - On tap: start recording
   - On stop: transcribe and append to notes
5. Hindi support: Use multilingual model (slightly larger)
```

### Task 3.3: AI-Powered Patient Search
**Effort**: 16 hours

```
Implementation:

1. Create src/services/mobile_rag.py:
   class MobileRAG:
       def __init__(self, db_path: str, llm: MobileLLM):
           self.db = LocalDatabase(db_path)
           self.llm = llm
           self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

       def embed_patients(self):
           # Create patient summaries
           for patient in self.db.get_all_patients():
               summary = f"{patient.name}, {patient.age}{patient.gender}..."
               embedding = self.embedder.encode(summary)
               self.store_embedding(patient.id, embedding)

       async def search(self, query: str) -> List[Patient]:
           query_embedding = self.embedder.encode(query)
           similar_ids = self.find_similar(query_embedding, top_k=10)
           return [self.db.get_patient(id) for id in similar_ids]

2. UI changes in patient_list.py:
   - Detect if AI search enabled
   - If query is natural language (> 3 words, not a name):
     - Use MobileRAG.search()
     - Show "AI-powered results" badge
   - Else: use simple SQLite search

3. Model management:
   - Embed all patients on first sync
   - Re-embed on subsequent syncs (delta only)
   - Store embeddings in SQLite (BLOB column)
```

---

## Phase 4 Tasks: Cloud AI

### Task 4.1: Anonymization Pipeline
**Effort**: 12 hours

```
Create src/services/anonymizer.py:

class Anonymizer:
    def __init__(self):
        self.name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        self.phone_pattern = r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        self.uhid_pattern = r'EMR-\d{4}-\d{4}'
        self.mappings = {}

    def anonymize(self, text: str) -> tuple[str, dict]:
        # Replace names
        names = re.findall(self.name_pattern, text)
        for i, name in enumerate(names):
            placeholder = f"[Patient{i+1}]"
            self.mappings[placeholder] = name
            text = text.replace(name, placeholder)

        # Replace phones
        phones = re.findall(self.phone_pattern, text)
        for phone in phones:
            text = text.replace(phone, "[PHONE]")

        # Replace UHIDs
        text = re.sub(self.uhid_pattern, "[UHID]", text)

        return text, self.mappings

    def deanonymize(self, text: str, mappings: dict) -> str:
        for placeholder, original in mappings.items():
            text = text.replace(placeholder, original)
        return text
```

### Task 4.2: Cloud AI Consent Flow
**Effort**: 4 hours

```
Create consent_dialog.py component:

def CloudAIConsentDialog(on_accept, on_decline):
    return ft.AlertDialog(
        title=ft.Text("Enable Cloud AI?"),
        content=ft.Column([
            ft.Icon(ft.Icons.CLOUD_OUTLINED, size=48),
            ft.Text(
                "Cloud AI provides faster, more accurate responses "
                "but requires sending anonymized data to our servers.",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=16),
            ft.Text("What we send:", weight=ft.FontWeight.BOLD),
            ft.Text("• Clinical context (symptoms, diagnoses)"),
            ft.Text("• Your questions"),
            ft.Container(height=8),
            ft.Text("What we DON'T send:", weight=ft.FontWeight.BOLD),
            ft.Text("• Patient names (replaced with [Patient])"),
            ft.Text("• Phone numbers"),
            ft.Text("• Addresses"),
            ft.Text("• UHID numbers"),
            ft.Container(height=16),
            ft.Text(
                "You can disable this anytime in Settings.",
                color=ft.Colors.GREY,
            ),
        ]),
        actions=[
            ft.TextButton("No, Stay Offline", on_click=on_decline),
            ft.ElevatedButton("Yes, Enable", on_click=on_accept),
        ],
    )

Store consent in preferences:
- preferences.set_cloud_ai_enabled(True)
- preferences.set_cloud_ai_consent_date(datetime.now())
```

---

## Phase 5 Tasks: Advanced Features

### Task 5.1: Push Notifications Setup
**Effort**: 16 hours

```
Android (FCM):
1. Create Firebase project
2. Add google-services.json to android/app/
3. Add firebase-messaging to pubspec.yaml
4. Create notification handler in main.py:
   async def on_notification(message):
       if message['type'] == 'appointment_reminder':
           show_notification(
               title="Appointment in 1 hour",
               body=f"Patient: {message['patient_name']}",
           )

iOS (APNs):
1. Enable Push Notifications capability
2. Create APNs key in Apple Developer
3. Upload key to Firebase (or direct APNs)
4. Request notification permission on first launch

Backend:
1. Add notification service to cloud-api:
   - Store FCM/APNs tokens per device
   - Queue notifications (appointment reminders)
   - Send via Firebase Admin SDK
```

### Task 5.2: SMS Integration
**Effort**: 12 hours

```
SMS Gateway (MSG91 - India optimized):

1. Create src/services/sms_service.py:
   class SMSService:
       def __init__(self, api_key: str):
           self.base_url = "https://api.msg91.com/api/v5"
           self.api_key = api_key

       async def send(self, phone: str, message: str):
           response = await requests.post(
               f"{self.base_url}/flow/",
               json={
                   "flow_id": "...",
                   "recipients": [{"mobile": phone, "message": message}],
               },
               headers={"authkey": self.api_key}
           )
           return response.json()

       async def send_appointment_reminder(self, patient: Patient, appointment: Appointment):
           message = f"Reminder: Your appointment with Dr. {doctor_name} is on {date} at {time}. Reply CONFIRM or call {clinic_phone}."
           await self.send(patient.phone, message)

2. Quota tracking:
   - Store SMS count in database
   - Check against plan limit before sending
   - Show warning when nearing limit

3. Templates in settings:
   - Appointment reminder template
   - Follow-up reminder template
   - Custom template option
```

### Task 5.3: Android Home Screen Widget
**Effort**: 12 hours

```
Create Flutter widget (since Flet compiles to Flutter):

1. Create android/app/src/main/java/.../AppointmentsWidget.kt:
   class AppointmentsWidget : GlanceAppWidget() {
       override suspend fun provideGlance(context: Context, id: GlanceId) {
           provideContent {
               Column(modifier = GlanceModifier.fillMaxSize()) {
                   Text("Today's Appointments")
                   LazyColumn {
                       items(appointments) { apt ->
                           Row {
                               Text(apt.time)
                               Text(apt.patientName)
                           }
                       }
                   }
               }
           }
       }
   }

2. Create bridge to share data with widget:
   - Write appointments to SharedPreferences
   - Widget reads from SharedPreferences
   - Trigger widget update after sync

3. Widget configuration:
   - Size: 4x2 grid cells
   - Show up to 5 appointments
   - Tap to open app
```

---

## Testing Checklist

### Unit Tests
```
- [ ] auth_service.py: login, logout, token refresh
- [ ] sync_client.py: download, decrypt, merge
- [ ] local_db.py: all CRUD operations
- [ ] offline_queue.py: add, get, mark synced
- [ ] anonymizer.py: name, phone, UHID replacement
```

### Integration Tests
```
- [ ] Full sync flow: login → download → decrypt → store
- [ ] Offline edit → queue → sync → verify on server
- [ ] Conflict resolution: edit on both devices
- [ ] Biometric flow: enable → lock → unlock
```

### UI Tests
```
- [ ] Onboarding flow: swipe through all pages
- [ ] Login flow: enter credentials, handle errors
- [ ] Patient search: type, see results, tap to open
- [ ] FAB actions: expand, tap action, navigate
- [ ] Pull-to-refresh: pull, see loading, complete
```

### Performance Tests
```
- [ ] App launch time: < 3 seconds cold start
- [ ] Patient list scroll: 60fps with 1000 patients
- [ ] Search latency: < 500ms for results
- [ ] LLM inference: < 5 seconds for response
- [ ] Voice transcription: < 2 seconds for 10s audio
```

---

## Deployment Checklist

### Pre-Release
```
- [ ] All P0 tasks complete
- [ ] All unit tests passing
- [ ] Tested on 3+ Android devices
- [ ] Tested on 2+ iOS devices
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Store listings created
- [ ] Screenshots prepared (all sizes)
- [ ] App icons in all sizes
- [ ] Crash reporting enabled
- [ ] Analytics enabled (privacy-preserving)
```

### Android Release
```
- [ ] Generate signed APK/AAB
- [ ] Upload to internal testing
- [ ] Test on internal track
- [ ] Promote to closed beta (100 users)
- [ ] Gather feedback for 1 week
- [ ] Fix critical issues
- [ ] Promote to production (staged 10%)
- [ ] Monitor crash rate
- [ ] Full rollout if stable
```

### iOS Release
```
- [ ] Build with production certificate
- [ ] Upload to App Store Connect
- [ ] Fill out App Privacy labels
- [ ] Submit for TestFlight review
- [ ] Distribute to beta testers
- [ ] Gather feedback for 1 week
- [ ] Submit for App Store review
- [ ] Respond to any review feedback
- [ ] Release once approved
```

---

*Tasks last updated: 2026-01-04*
