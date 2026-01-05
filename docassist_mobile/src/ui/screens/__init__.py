"""DocAssist Mobile - Screen components."""

from .home_screen import HomeScreen, AppointmentData
from .patient_list import PatientListScreen, PatientData
from .patient_detail import PatientDetailScreen, PatientInfo, VisitData, LabData, ProcedureData
from .prescription_viewer import PrescriptionViewer
from .login_screen import LoginScreen
from .settings_screen import SettingsScreen
from .add_patient_screen import AddPatientScreen, QuickAddPatientDialog
from .biometric_prompt import BiometricPrompt, BiometricPromptDialog
from .onboarding_screen import OnboardingScreen
from .welcome_back_screen import WelcomeBackScreen
from .quick_note_screen import QuickNoteScreen, QuickNoteData

# Optional screens (may not exist yet)
try:
    from .add_visit_screen import AddVisitScreen, VisitFormData, MedicationData
except ImportError:
    AddVisitScreen = None
    VisitFormData = None
    MedicationData = None

try:
    from .add_lab_screen import AddLabScreen, LabFormData
except ImportError:
    AddLabScreen = None
    LabFormData = None

try:
    from .add_appointment_screen import AddAppointmentScreen, AppointmentFormData
except ImportError:
    AddAppointmentScreen = None
    AppointmentFormData = None

try:
    from .edit_patient_screen import EditPatientScreen, PatientFormData
except ImportError:
    EditPatientScreen = None
    PatientFormData = None

__all__ = [
    # Screens
    'HomeScreen',
    'PatientListScreen',
    'PatientDetailScreen',
    'PrescriptionViewer',
    'LoginScreen',
    'SettingsScreen',
    'AddPatientScreen',
    'QuickAddPatientDialog',
    'BiometricPrompt',
    'BiometricPromptDialog',
    'OnboardingScreen',
    'WelcomeBackScreen',
    'QuickNoteScreen',
    'AddVisitScreen',
    'AddLabScreen',
    'AddAppointmentScreen',
    'EditPatientScreen',
    # Data classes
    'AppointmentData',
    'PatientData',
    'PatientInfo',
    'VisitData',
    'LabData',
    'ProcedureData',
    'QuickNoteData',
    'VisitFormData',
    'MedicationData',
    'LabFormData',
    'AppointmentFormData',
    'PatientFormData',
]
