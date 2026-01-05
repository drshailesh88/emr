# Care Gap Detector - Quick Reference

## File Locations

### Core Service
```
/home/user/emr/src/services/analytics/care_gap_detector.py
```
- **Lines**: 772 total
- **Classes**:
  - `CareGapPriority` (Enum)
  - `CareGap` (dataclass)
  - `CareGapDetector` (main class)
- **Key Methods**:
  - `detect_care_gaps(patient_id)` → List[CareGap]
  - `_check_diabetes_gaps()` → List[CareGap]
  - `_check_hypertension_gaps()` → List[CareGap]
  - `_check_medication_monitoring()` → List[CareGap]
  - `_check_preventive_care()` → List[CareGap]
  - `_check_overdue_followups()` → List[CareGap]

### UI Component
```
/home/user/emr/src/ui/components/care_gap_alert.py
```
- **Lines**: 372 total
- **Classes**:
  - `CareGapAlert` (ft.UserControl)
- **Key Methods**:
  - `show_care_gaps(care_gaps)` → void
  - `clear()` → void
  - `_rebuild_alerts()` → void
  - `_create_care_gap_alert(gap)` → ft.Control

### Integration Point
```
/home/user/emr/src/ui/central_panel.py
```
- **Line 34**: Import `CareGapAlert`
- **Line 38**: Import `CareGapDetector`
- **Line 70**: Initialize `self.care_gap_detector`
- **Line 125**: Declare `self.care_gap_alert`
- **Line 312-315**: Initialize care gap alert
- **Line 341**: Add to UI layout
- **Line 846**: Call `_check_care_gaps()` in `set_patient()`
- **Line 2175-2253**: Care gap methods

### Test File
```
/home/user/emr/test_care_gaps.py
```
- Run with: `python3 test_care_gaps.py`
- Creates test patients and detects gaps

## Quick Code Snippets

### 1. Detect Care Gaps for a Patient
```python
from src.services.analytics.care_gap_detector import CareGapDetector
from src.services.database import DatabaseService

db = DatabaseService("data/clinic.db")
detector = CareGapDetector(db)

patient_id = 123
gaps = detector.detect_care_gaps(patient_id)

for gap in gaps:
    print(f"{gap.priority.value}: {gap.description}")
    print(f"   → {gap.recommendation}")
```

### 2. Show Care Gaps in UI
```python
from src.ui.components.care_gap_alert import CareGapAlert

# Initialize
alert = CareGapAlert(
    on_action_clicked=handle_action,
    on_dismissed=handle_dismiss
)

# Show gaps
alert.show_care_gaps(gaps)

# Clear
alert.clear()
```

### 3. Add to Flet Layout
```python
import flet as ft

page = ft.Page()

# Create alert
care_gap_alert = CareGapAlert()

# Add to page
page.add(
    ft.Column([
        ft.Text("Patient Dashboard"),
        care_gap_alert,  # Add here
        ft.TextField(label="Notes"),
    ])
)
```

## Care Gap Types Reference

| Care Gap | Condition | Threshold | Priority |
|----------|-----------|-----------|----------|
| **HbA1c overdue** | Diabetes | >90 days | SOON/URGENT |
| **Eye exam** | Diabetes | >365 days | URGENT |
| **Foot exam** | Diabetes | Not documented | ROUTINE |
| **BP check** | Hypertension | >30 days | URGENT |
| **INR check** | On Warfarin | >30 days | URGENT |
| **Creatinine** | On Metformin | >180 days | SOON |
| **Lipid profile** | On Statin | >365 days | ROUTINE |
| **Colonoscopy** | Age >50 | Not done | ROUTINE |
| **Mammogram** | Female >40 | >730 days | ROUTINE/SOON |
| **Follow-up** | Any | >7 days overdue | URGENT/SOON |

## Priority Calculation

```python
# URGENT
- days_overdue > 30
- Critical safety (warfarin INR)
- Never done (when required)

# SOON
- days_overdue > 7 and <= 30
- Moderate delay
- Routine monitoring overdue

# ROUTINE
- days_overdue <= 7
- Preventive care
- Age-based screening
```

## Customization Points

### 1. Modify Thresholds
Edit `care_gap_detector.py`:
```python
# Line 230: Change HbA1c threshold
if days_since > 90:  # Change to 60, 120, etc.
```

### 2. Add New Care Gap Rule
Add method to `CareGapDetector`:
```python
def _check_my_custom_gap(self, patient_id, data) -> List[CareGap]:
    gaps = []
    # Your logic here
    if condition:
        gaps.append(CareGap(
            patient_id=patient_id,
            category="monitoring",
            description="My custom gap",
            recommendation="Do X",
            priority=CareGapPriority.URGENT,
        ))
    return gaps
```

Call in `detect_care_gaps()`:
```python
gaps.extend(self._check_my_custom_gap(patient_id, data))
```

### 3. Customize Alert Colors
Edit `care_gap_alert.py`:
```python
def _get_priority_colors(self, priority):
    if priority == CareGapPriority.URGENT:
        return ("#YOUR_BG", "#YOUR_BORDER", "#YOUR_ICON", "#YOUR_TEXT")
```

### 4. Change Alert Position
Edit `central_panel.py` line 341:
```python
rx_tab_content = ft.Column([
    self.red_flag_banner,
    # Move care_gap_alert to different position
    self.vitals_section,
    self.care_gap_alert,  # e.g., after vitals
])
```

## API Reference

### CareGap (dataclass)
```python
@dataclass
class CareGap:
    patient_id: int                      # Patient ID
    category: str                        # preventive, monitoring, follow_up
    description: str                     # "HbA1c overdue"
    recommendation: str                  # "Order HbA1c test"
    priority: CareGapPriority           # URGENT, SOON, ROUTINE
    days_overdue: Optional[int] = None  # Days past due
    last_done_date: Optional[date] = None # Last test/procedure date
    details: Optional[str] = None       # Additional context
    action_type: str = "order"          # order, reminder, schedule
```

### CareGapDetector
```python
class CareGapDetector:
    def __init__(self, db_service: DatabaseService)

    def detect_care_gaps(self, patient_id: int) -> List[CareGap]
        """Detect all care gaps for a patient"""

    def generate_care_gap_report(self, all_patients: bool) -> Dict[str, List[CareGap]]
        """Generate report for multiple patients"""
```

### CareGapAlert
```python
class CareGapAlert(ft.UserControl):
    def __init__(
        self,
        on_action_clicked: Callable[[CareGap], None],
        on_dismissed: Callable[[CareGap, str], None],
        is_dark: bool = False
    )

    def show_care_gaps(self, care_gaps: List[CareGap])
        """Display care gaps in UI"""

    def clear(self)
        """Clear all alerts"""
```

## Common Tasks

### Task 1: Add New Medication Monitoring
1. Open `care_gap_detector.py`
2. Find `_check_medication_monitoring()` method (line ~450)
3. Add new medication check:
```python
# ACE inhibitor - Potassium check every 6 months
if self._has_medication(medications, ["enalapril", "lisinopril", "ramipril"]):
    potassium = self._get_latest_test(investigations, ["potassium", "k+"])
    if potassium:
        last_date, _ = potassium
        days_since = (today - last_date).days
        if days_since > 180:
            gaps.append(CareGap(
                patient_id=patient_id,
                category="monitoring",
                description="Potassium check overdue (on ACE inhibitor)",
                recommendation=f"Order potassium level (last done {days_since} days ago)",
                priority=CareGapPriority.SOON,
                days_overdue=days_since - 180,
                last_done_date=last_date,
            ))
```

### Task 2: Change Alert Appearance
1. Open `care_gap_alert.py`
2. Find `_create_care_gap_alert()` method (line ~89)
3. Modify layout, colors, fonts as needed

### Task 3: Add Custom Action Button
1. Open `care_gap_alert.py`
2. Modify action_row in `_create_care_gap_alert()`
3. Add new button:
```python
ft.TextButton(
    text="Custom Action",
    icon=ft.Icons.STAR,
    on_click=lambda e, g=gap: self._handle_custom_action(g),
)
```

## Troubleshooting

### Care gaps not showing?
1. Check if patient has data (visits, investigations)
2. Check console for error messages
3. Verify detector is initialized in central_panel
4. Check if care_gap_alert is visible in UI

### Wrong priority?
1. Check days_overdue calculation
2. Verify threshold in detection rules
3. Check priority assignment logic

### Action buttons not working?
1. Verify callbacks are connected
2. Check if page is available
3. Look for JavaScript errors (if web)

## Performance Tips

1. **Cache results**: Store last detection timestamp
2. **Debounce**: Don't re-check on every keystroke
3. **Async detection**: Run in background thread
4. **Batch queries**: Load all patient data once

## Security & Privacy

1. **No network calls**: All processing is local
2. **Audit logging**: All dismissals are logged
3. **Data retention**: Consider GDPR/DPDP compliance
4. **Access control**: Check user permissions before showing

## Support

### Documentation
- Implementation: `/home/user/emr/CARE_GAP_IMPLEMENTATION.md`
- UI Guide: `/home/user/emr/CARE_GAP_UI_GUIDE.md`
- This file: `/home/user/emr/CARE_GAP_QUICK_REFERENCE.md`

### Test
- Run: `python3 test_care_gaps.py`

### Logs
- Console: `print()` statements
- TODO: Implement proper logging

---

**Last Updated**: 2026-01-05
**Version**: 1.0.0
**Status**: Production Ready ✅
