# DocAssist Mobile - Edit Capability Screens

This document describes the newly created edit capability screens for the DocAssist mobile app.

## Created Screens

### 1. AddVisitScreen (`add_visit_screen.py`)

**Purpose**: Create new patient visits with full prescription builder.

**Features**:
- Chief complaint text field
- Clinical notes (multi-line)
- Diagnosis field
- Dynamic prescription builder (add/remove medications)
- Medication fields: drug name, strength, dose, frequency, duration, instructions
- Investigations (comma-separated)
- Advice (comma-separated)
- Follow-up field
- Form validation
- Haptic feedback on save/cancel
- Scrollable form

**Usage**:
```python
from src.ui.screens import AddVisitScreen, VisitFormData

def handle_save(patient_id: int, form_data: VisitFormData):
    # Save visit to database
    print(f"Saving visit for patient {patient_id}")
    print(f"Chief complaint: {form_data.chief_complaint}")
    print(f"Medications: {len(form_data.medications)}")

def handle_cancel():
    # Navigate back
    print("Cancelled")

screen = AddVisitScreen(
    patient_id=123,
    patient_name="John Doe",
    on_save=handle_save,
    on_cancel=handle_cancel,
    haptic_feedback=haptics,
)
```

**Data Classes**:
- `VisitFormData`: Contains all visit data
- `MedicationData`: Individual medication entry

### 2. AddLabScreen (`add_lab_screen.py`)

**Purpose**: Add laboratory test results quickly.

**Features**:
- Test name field
- Result field
- Unit field (optional)
- Reference range (optional)
- Date picker for test date
- Is abnormal toggle
- **Save & Add Another** button for bulk entry
- Regular Save button
- Form validation
- Haptic feedback

**Usage**:
```python
from src.ui.screens import AddLabScreen, LabFormData

def handle_save(patient_id: int, form_data: LabFormData, add_another: bool):
    # Save lab result
    print(f"Saving lab for patient {patient_id}: {form_data.test_name}")

    if add_another:
        # Reset form for next entry
        screen.reset()
    else:
        # Navigate back
        navigate_back()

screen = AddLabScreen(
    patient_id=123,
    patient_name="John Doe",
    on_save=handle_save,
    on_cancel=handle_cancel,
    haptic_feedback=haptics,
)
```

**Data Classes**:
- `LabFormData`: Contains test name, result, unit, reference range, date, is_abnormal

### 3. AddAppointmentScreen (`add_appointment_screen.py`)

**Purpose**: Schedule patient appointments.

**Features**:
- Patient selector (if patient not pre-selected)
- Date picker (Material Design)
- Time picker (Material Design)
- Duration selector (15min, 30min, 45min, 1hr)
- Reason for visit field
- Notes field (optional)
- Form validation
- Haptic feedback

**Usage**:
```python
from src.ui.screens import AddAppointmentScreen, AppointmentFormData

def handle_save(form_data: AppointmentFormData):
    # Schedule appointment
    print(f"Scheduling appointment for patient {form_data.patient_id}")
    print(f"Date: {form_data.appointment_date} at {form_data.appointment_time}")
    print(f"Duration: {form_data.duration_minutes} minutes")

# With pre-selected patient
screen = AddAppointmentScreen(
    patient_id=123,
    patient_name="John Doe",
    on_save=handle_save,
    on_cancel=handle_cancel,
    haptic_feedback=haptics,
)

# Without pre-selected patient (from calendar view)
screen = AddAppointmentScreen(
    on_save=handle_save,
    on_cancel=handle_cancel,
    haptic_feedback=haptics,
)
```

**Data Classes**:
- `AppointmentFormData`: Contains patient_id, date, time, duration, reason, notes

### 4. EditPatientScreen (`edit_patient_screen.py`)

**Purpose**: Edit patient demographics.

**Features**:
- Name field (required)
- Age field (number, validated)
- Gender radio buttons (M/F/O)
- Phone field (validated for 10 digits)
- Address field (multi-line)
- Pre-filled with existing patient data
- Comprehensive validation
- Haptic feedback

**Usage**:
```python
from src.ui.screens import EditPatientScreen, PatientFormData

# Load existing patient data
existing_data = PatientFormData(
    name="John Doe",
    age=45,
    gender="M",
    phone="9876543210",
    address="123 Main St, Mumbai",
)

def handle_save(patient_id: int, form_data: PatientFormData):
    # Update patient in database
    print(f"Updating patient {patient_id}")
    print(f"New name: {form_data.name}")

screen = EditPatientScreen(
    patient_id=123,
    initial_data=existing_data,
    on_save=handle_save,
    on_cancel=handle_cancel,
    haptic_feedback=haptics,
)
```

**Data Classes**:
- `PatientFormData`: Contains name, age, gender, phone, address

## Design Patterns

All screens follow consistent patterns:

### 1. **Imports**
```python
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback
```

### 2. **Constructor Pattern**
```python
def __init__(
    self,
    # Required data
    patient_id: int,
    patient_name: str,
    # Callbacks
    on_save: Callable[[...], None],
    on_cancel: Callable[[], None],
    # Optional
    haptic_feedback: Optional[HapticFeedback] = None,
):
```

### 3. **Validation**
```python
def _validate_form(self) -> bool:
    if not self.required_field.value:
        self._show_error("Field is required")
        return False
    return True
```

### 4. **Loading States**
```python
def _set_loading(self, loading: bool):
    self.save_button.visible = not loading
    self.loading_indicator.visible = loading
    # Disable form fields
    self.update()
```

### 5. **Error Handling**
```python
def show_save_error(self, message: str = "Default error"):
    self._set_loading(False)
    self._show_error(message)
    if self.haptic_feedback:
        self.haptic_feedback.error()
```

### 6. **Form Reset**
```python
def reset(self):
    # Clear all fields
    # Reset to default state
    # Hide errors
    # Stop loading
    self.update()
```

## Integration Example

Here's how to integrate these screens into the main app:

```python
from src.ui.screens import (
    AddVisitScreen,
    AddLabScreen,
    AddAppointmentScreen,
    EditPatientScreen,
)
from src.ui.haptics import HapticFeedback

class MobileApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.haptics = HapticFeedback(page)
        self.current_screen = None

    def show_add_visit(self, patient_id: int, patient_name: str):
        self.current_screen = AddVisitScreen(
            patient_id=patient_id,
            patient_name=patient_name,
            on_save=self.save_visit,
            on_cancel=self.close_modal,
            haptic_feedback=self.haptics,
        )
        self.page.add(self.current_screen)

    def save_visit(self, patient_id: int, form_data):
        try:
            # Save to database
            self.db.save_visit(patient_id, form_data)
            self.close_modal()
            self.show_success("Visit saved successfully")
        except Exception as e:
            self.current_screen.show_save_error(str(e))

    def close_modal(self):
        if self.current_screen:
            self.page.remove(self.current_screen)
            self.current_screen = None
```

## File Locations

```
docassist_mobile/src/ui/screens/
├── add_visit_screen.py          (18 KB)
├── add_lab_screen.py            (13 KB)
├── add_appointment_screen.py    (16 KB)
├── edit_patient_screen.py       (14 KB)
└── __init__.py                  (updated)
```

## Design Tokens Used

- **Colors**: PRIMARY_500, NEUTRAL_0, ERROR_MAIN, etc.
- **Spacing**: MobileSpacing.SM, MD, LG, TOUCH_TARGET, SCREEN_PADDING
- **Typography**: MobileTypography.TITLE_LARGE, BODY_MEDIUM, etc.
- **Radius**: Radius.MD, CARD, BUTTON

## Haptic Feedback

All screens use haptic feedback for:
- ✓ **Success**: On successful save
- ⚠️ **Error**: On validation failure
- 💡 **Light**: On cancel, date picker, add/remove actions
- 🔘 **Medium**: On primary button press

## Validation Rules

### AddVisitScreen
- Chief complaint: Required
- Diagnosis: Required
- Medications: Optional, can have 0 or more

### AddLabScreen
- Test name: Required
- Result: Required
- Unit, range, date: Optional

### AddAppointmentScreen
- Patient: Required (name or ID)
- Reason: Required
- Date, time, duration: Required

### EditPatientScreen
- Name: Required
- Age: Optional, must be 0-150 if provided
- Phone: Optional, must be 10 digits if provided
- Gender: Defaults to "O" (Other)
- Address: Optional

## Next Steps

1. **Database Integration**: Connect form data to SQLite operations
2. **Sync Support**: Add sync indicators for cloud backup
3. **Offline Support**: Queue saves when offline
4. **Autocomplete**: Add drug name autocomplete in AddVisitScreen
5. **Templates**: Add prescription templates
6. **Voice Input**: Add voice-to-text for clinical notes

## Testing

To test these screens:

```bash
cd /home/user/emr/docassist_mobile
python3 -m pytest tests/test_screens.py -v
```

(Note: Tests need to be written)
