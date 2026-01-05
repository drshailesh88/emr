# Prescription PDF Viewing and Sharing - Usage Guide

## Overview

The prescription PDF viewing and sharing functionality allows users to:
- View prescription details in a beautiful, mobile-optimized interface
- Share prescriptions via native share sheet (WhatsApp, email, etc.)
- Download/save prescriptions to device storage
- Browse prescription history with quick access cards

## Components Created

### 1. **MobilePDFService** (`src/services/pdf_service.py`)

Service for generating and managing prescription PDFs.

**Key Methods:**
```python
from src.services.pdf_service import MobilePDFService

# Initialize service
pdf_service = MobilePDFService(cache_dir="data/prescriptions")

# Generate PDF from visit data
pdf_bytes = pdf_service.generate_prescription_pdf(
    visit_data={'id': 123, 'prescription_json': {...}, ...},
    patient_data={'name': 'Ram Lal', 'age': 65, ...}
)

# Get cached PDF
cached_pdf = pdf_service.get_prescription_pdf(visit_id=123)

# Get prescription summary for card display
summary = pdf_service.get_prescription_summary(prescription_json)
# Returns: {'diagnosis': str, 'medication_count': int, ...}

# Share prescription (triggers native share)
pdf_service.share_prescription(pdf_bytes, patient_name="Ram Lal", page=page)

# Save prescription to device
filepath = pdf_service.save_prescription(pdf_bytes, filename="Rx_Ram_Lal.pdf")
```

**Configuration:**

Set environment variables to customize PDF headers:
```bash
export DOCTOR_NAME="Dr. Rajesh Kumar"
export DOCTOR_QUALIFICATIONS="MBBS, MD (Medicine)"
export DOCTOR_REGISTRATION="MCI12345"
export CLINIC_NAME="City Heart Clinic"
export CLINIC_ADDRESS="123 MG Road, Mumbai 400001"
export CLINIC_PHONE="+91-22-1234-5678"
export CLINIC_EMAIL="care@cityheart.in"
```

### 2. **PrescriptionCard** (`src/ui/components/prescription_card.py`)

Card component displaying prescription summary in lists.

**Usage:**
```python
from src.ui.components.prescription_card import PrescriptionCard

card = PrescriptionCard(
    visit_id=123,
    visit_date="2024-01-15",
    diagnosis="Hypertension, Type 2 Diabetes",
    medication_count=3,
    has_investigations=True,
    has_follow_up=True,
    on_view_pdf=handle_view_prescription,  # Callback when tapped
)
```

**Features:**
- Shows visit date with calendar icon
- Displays truncated diagnosis (max 60 chars)
- Shows medication count badge
- Shows investigation and follow-up indicators
- Tap anywhere to open full prescription viewer
- PDF icon indicates it's a prescription

### 3. **PrescriptionViewer** (`src/ui/screens/prescription_viewer.py`)

Full-screen prescription viewer with share/download capabilities.

**Usage:**
```python
from src.ui.screens.prescription_viewer import PrescriptionViewer

viewer = PrescriptionViewer(
    visit_data={
        'id': 123,
        'visit_date': '2024-01-15',
        'chief_complaint': 'Chest pain x 2 days',
        'prescription_json': {...}
    },
    patient_data={
        'name': 'Ram Lal',
        'age': 65,
        'gender': 'M',
        'uhid': 'EMR-2024-0001'
    },
    on_back=handle_back,
    on_share=handle_share,
    on_download=handle_download,
    haptic_feedback=haptics,
)
```

**Screen Features:**
- Header with patient name and date
- Back button (top-left)
- Share button (top-right)
- Download button (top-right)
- Scrollable prescription details:
  - Patient information
  - Chief complaint
  - Diagnosis
  - Medications (Rx section)
  - Investigations
  - Advice
  - Follow-up
  - Red flags (warning section)
- Loading state while parsing
- Error state for missing prescriptions

### 4. **Updated PatientDetailScreen**

Added "Rx" tab to patient detail screen.

**New Features:**
- New `set_prescriptions(visits)` method
- New `on_view_prescription` callback
- Prescriptions tab shows all visits with prescriptions
- Each prescription displayed as PrescriptionCard
- Tapping card opens PrescriptionViewer

## Integration Example

Here's a complete example of integrating prescription viewing into your mobile app:

```python
import flet as ft
from src.services.local_db import LocalDatabase
from src.services.pdf_service import MobilePDFService
from src.ui.screens.patient_detail import PatientDetailScreen, PatientInfo, VisitData
from src.ui.screens.prescription_viewer import PrescriptionViewer
from src.ui.haptics import HapticFeedback

class MobileApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = LocalDatabase("data/clinic.db")
        self.pdf_service = MobilePDFService()
        self.haptics = HapticFeedback(page)

        # Navigation state
        self.current_screen = None
        self.current_patient = None

    def show_patient_detail(self, patient_id: int):
        """Show patient detail screen with prescription tab."""
        # Get patient data
        patient_db = self.db.get_patient(patient_id)
        patient = PatientInfo(
            id=patient_db.id,
            name=patient_db.name,
            uhid=patient_db.uhid,
            age=patient_db.age,
            gender=patient_db.gender,
            phone=patient_db.phone,
            address=patient_db.address,
        )

        # Create patient detail screen
        detail_screen = PatientDetailScreen(
            patient=patient,
            on_back=self.show_home,
            on_call=self.handle_call,
            on_share=self.handle_share_latest_prescription,
            on_add_appointment=self.show_add_appointment,
            on_view_prescription=self.show_prescription_viewer,
            haptic_feedback=self.haptics,
        )

        # Load visits and prescriptions
        visits_db = self.db.get_patient_visits(patient_id)
        visits = [
            VisitData(
                id=v.id,
                date=v.visit_date.strftime('%d %b %Y'),
                chief_complaint=v.chief_complaint,
                diagnosis=v.diagnosis,
                prescription=v.prescription_json,
            )
            for v in visits_db
        ]

        detail_screen.set_visits(visits)
        detail_screen.set_prescriptions(visits)  # Populates Rx tab

        # Show screen
        self.current_screen = detail_screen
        self.current_patient = patient
        self.page.clean()
        self.page.add(detail_screen)
        self.page.update()

    def show_prescription_viewer(self, visit_id: int):
        """Show prescription viewer for a specific visit."""
        # Get visit and patient data
        visit_db = self.db.get_visit(visit_id)
        patient_db = self.db.get_patient(visit_db.patient_id)

        visit_data = {
            'id': visit_db.id,
            'visit_date': visit_db.visit_date.strftime('%d %b %Y'),
            'chief_complaint': visit_db.chief_complaint,
            'clinical_notes': visit_db.clinical_notes,
            'diagnosis': visit_db.diagnosis,
            'prescription_json': visit_db.prescription_json,
        }

        patient_data = {
            'name': patient_db.name,
            'age': patient_db.age,
            'gender': patient_db.gender,
            'uhid': patient_db.uhid,
        }

        # Create prescription viewer
        viewer = PrescriptionViewer(
            visit_data=visit_data,
            patient_data=patient_data,
            on_back=lambda: self.show_patient_detail(patient_db.id),
            on_share=self.handle_share_prescription,
            on_download=self.handle_download_prescription,
            haptic_feedback=self.haptics,
        )

        # Show screen
        self.current_screen = viewer
        self.page.clean()
        self.page.add(viewer)
        self.page.update()

    def handle_share_prescription(self, visit_data: dict, patient_name: str):
        """Handle prescription share action."""
        # Generate PDF
        patient_data = self.db.get_patient(visit_data.get('patient_id'))
        patient_dict = {
            'name': patient_data.name,
            'age': patient_data.age,
            'gender': patient_data.gender,
            'uhid': patient_data.uhid,
        }

        pdf_bytes = self.pdf_service.generate_prescription_pdf(
            visit_data=visit_data,
            patient_data=patient_dict,
        )

        if pdf_bytes:
            # Trigger native share
            success = self.pdf_service.share_prescription(
                pdf_bytes,
                patient_name,
                self.page,
            )

            if success:
                self.haptics.success()
                self.show_snackbar("Prescription ready to share")
            else:
                self.haptics.error()
                self.show_snackbar("Failed to share prescription", error=True)
        else:
            self.haptics.error()
            self.show_snackbar("Failed to generate PDF", error=True)

    def handle_download_prescription(self, visit_data: dict, patient_name: str):
        """Handle prescription download action."""
        # Similar to share, but saves to device
        patient_data = self.db.get_patient(visit_data.get('patient_id'))
        patient_dict = {
            'name': patient_data.name,
            'age': patient_data.age,
            'gender': patient_data.gender,
            'uhid': patient_data.uhid,
        }

        pdf_bytes = self.pdf_service.generate_prescription_pdf(
            visit_data=visit_data,
            patient_data=patient_dict,
        )

        if pdf_bytes:
            from datetime import date
            safe_name = "".join(c for c in patient_name if c.isalnum() or c in " -_")[:30]
            filename = f"Rx_{safe_name}_{date.today().strftime('%Y%m%d')}.pdf"

            filepath = self.pdf_service.save_prescription(pdf_bytes, filename)

            if filepath:
                self.haptics.success()
                self.show_snackbar(f"Saved to {filepath}")
            else:
                self.haptics.error()
                self.show_snackbar("Failed to save prescription", error=True)
        else:
            self.haptics.error()
            self.show_snackbar("Failed to generate PDF", error=True)

    def show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar notification."""
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.colors.ERROR_CONTAINER if error else ft.colors.PRIMARY,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
```

## Data Flow

1. **Patient Detail Screen** → User taps "Rx" tab
2. **set_prescriptions()** called → Filters visits with prescriptions → Creates PrescriptionCards
3. **User taps PrescriptionCard** → `on_view_prescription(visit_id)` callback
4. **App** → Fetches visit and patient data → Creates PrescriptionViewer
5. **PrescriptionViewer** → Parses prescription_json → Renders formatted view
6. **User taps Share** → `on_share()` callback → MobilePDFService generates PDF
7. **MobilePDFService** → Triggers native share sheet → User shares via WhatsApp/email/etc.

## Testing

To test the prescription functionality:

```python
# 1. Create test data
test_visit = {
    'id': 1,
    'visit_date': '2024-01-15',
    'chief_complaint': 'Hypertension follow-up',
    'prescription_json': json.dumps({
        'diagnosis': ['Essential Hypertension', 'Type 2 Diabetes'],
        'medications': [
            {
                'drug_name': 'Amlodipine',
                'strength': '5mg',
                'form': 'tablet',
                'dose': '1',
                'frequency': 'OD',
                'duration': '30 days',
                'instructions': 'after breakfast'
            }
        ],
        'investigations': ['BP monitoring', 'HbA1c'],
        'advice': ['Low salt diet', 'Regular exercise'],
        'follow_up': '1 month',
        'red_flags': ['Severe headache', 'Chest pain']
    })
}

test_patient = {
    'name': 'Test Patient',
    'age': 65,
    'gender': 'M',
    'uhid': 'TEST-001'
}

# 2. Generate PDF
pdf_service = MobilePDFService()
pdf_bytes = pdf_service.generate_prescription_pdf(test_visit, test_patient)

# 3. Verify PDF was created
assert pdf_bytes is not None
assert len(pdf_bytes) > 0

# 4. Test prescription summary
summary = pdf_service.get_prescription_summary(test_visit['prescription_json'])
assert summary['medication_count'] == 1
assert summary['diagnosis'] == 'Essential Hypertension'
```

## Future Enhancements

1. **PDF Rendering**: Use platform-specific PDF viewers or convert PDF to images for in-app viewing
2. **Offline Queue**: Queue prescription shares when offline, sync when online
3. **Templates**: Allow doctors to customize prescription templates
4. **Multi-language**: Support Hindi, Tamil, Telugu prescription formats
5. **Digital Signature**: Add doctor's digital signature to PDFs
6. **Print**: Direct print to Bluetooth printers

## Troubleshooting

**Issue**: PDF generation fails
- Check that fpdf2 is installed: `pip install fpdf2>=2.7.0`
- Verify prescription_json is valid JSON
- Check doctor/clinic environment variables are set

**Issue**: Share sheet doesn't open
- Verify page.share() API is available in your Flet version
- Check platform-specific share capabilities

**Issue**: Prescriptions tab is empty
- Ensure visits have prescription_json field populated
- Check that set_prescriptions() is called after loading visits
- Verify prescription_json is not null/empty

**Issue**: Red flags section not showing
- Verify prescription_json includes 'red_flags' array
- Check that red_flags is a non-empty list

## Related Files

- `/home/user/emr/docassist_mobile/src/services/pdf_service.py` - PDF generation service
- `/home/user/emr/docassist_mobile/src/ui/components/prescription_card.py` - Prescription card component
- `/home/user/emr/docassist_mobile/src/ui/screens/prescription_viewer.py` - Full-screen viewer
- `/home/user/emr/docassist_mobile/src/ui/screens/patient_detail.py` - Updated patient detail with Rx tab
- `/home/user/emr/src/services/pdf.py` - Desktop PDF service (reference)

## License

Part of DocAssist EMR - Local-First AI-Powered EMR
