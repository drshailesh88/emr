# Lab Trend Charts - Code Samples from Implementation

This document shows actual code snippets from the implemented lab trend charts feature.

---

## 1. LabTrendChart Component

**File**: `/home/user/emr/src/ui/components/lab_trend_chart.py`

### Class Definition

```python
class LabTrendChart(ft.UserControl):
    """
    A line chart component showing lab values over time.
    Highlights abnormal values and shows normal range as reference.
    """

    def __init__(
        self,
        test_name: str,
        data_points: List[Dict],  # [{date, value, is_abnormal}]
        normal_min: Optional[float] = None,
        normal_max: Optional[float] = None,
        unit: str = "",
        width: int = 600,
        height: int = 300,
    ):
```

### Chart Rendering

```python
# Create line chart data series
line_series = ft.LineChartData(
    data_points=chart_data_points,
    color=ft.Colors.BLUE_700,
    stroke_width=3,
    curved=True,
    stroke_cap_round=True,
    below_line_bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_700),
    below_line_fill=True,
)
```

### Data Points with Abnormal Highlighting

```python
for i, point in enumerate(self.data_points):
    value = point["value"]
    chart_data_points.append(
        ft.LineChartDataPoint(
            x=i,
            y=value,
            tooltip=self._format_tooltip(point),
            selected_point_color=ft.Colors.RED if point.get("is_abnormal") else ft.Colors.BLUE,
        )
    )
```

### Interactive Tooltips

```python
def _format_tooltip(self, point: Dict) -> str:
    """Format tooltip text for a data point."""
    date_val = point["date"]
    if isinstance(date_val, str):
        try:
            date_val = datetime.strptime(date_val, "%Y-%m-%d").date()
        except:
            pass

    date_str = date_val.strftime("%d %b %Y") if hasattr(date_val, 'strftime') else str(date_val)
    value_str = f"{point['value']:.2f} {self.unit}"

    tooltip = f"{date_str}\n{value_str}"
    if point.get("is_abnormal"):
        tooltip += "\n(ABNORMAL)"

    return tooltip
```

---

## 2. Reference Ranges Service

**File**: `/home/user/emr/src/services/reference_ranges.py`

### Reference Ranges Database

```python
REFERENCE_RANGES: Dict[str, Tuple[Optional[float], Optional[float], str]] = {
    # Renal Panel
    "Creatinine": (0.7, 1.3, "mg/dL"),
    "BUN": (7, 20, "mg/dL"),
    "eGFR": (90, None, "mL/min"),
    "Urea": (15, 40, "mg/dL"),
    "Potassium": (3.5, 5.0, "mEq/L"),
    "Sodium": (135, 145, "mEq/L"),
    "Chloride": (98, 107, "mEq/L"),

    # Diabetic Panel
    "FBS": (70, 100, "mg/dL"),
    "PPBS": (None, 140, "mg/dL"),
    "HbA1c": (4.0, 6.5, "%"),
    "Random Blood Sugar": (None, 140, "mg/dL"),

    # Lipid Panel
    "Total Cholesterol": (None, 200, "mg/dL"),
    "LDL": (None, 100, "mg/dL"),
    "HDL": (40, None, "mg/dL"),
    "Triglycerides": (None, 150, "mg/dL"),
    "VLDL": (None, 30, "mg/dL"),

    # CBC
    "Hemoglobin": (13.0, 17.0, "g/dL"),
    "WBC": (4000, 11000, "cells/μL"),
    "Platelets": (150000, 450000, "cells/μL"),
    # ... 50+ more tests
}
```

### Trend Panels Configuration

```python
TREND_PANELS = {
    "Renal": ["Creatinine", "BUN", "eGFR", "Potassium"],
    "Diabetic": ["FBS", "PPBS", "HbA1c"],
    "Lipid": ["Total Cholesterol", "LDL", "HDL", "Triglycerides"],
    "Thyroid": ["TSH", "T3", "T4"],
    "Liver": ["ALT", "AST", "ALP", "Bilirubin Total"],
    "Cardiac": ["Troponin I", "BNP", "CK-MB"],
    "CBC": ["Hemoglobin", "WBC", "Platelets"],
}
```

### Get Reference Range Function

```python
def get_reference_range(test_name: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Get reference range for a test.

    Args:
        test_name: Name of the test

    Returns:
        Tuple of (min, max, unit). min/max can be None if unbounded.
    """
    # Try exact match first
    if test_name in REFERENCE_RANGES:
        return REFERENCE_RANGES[test_name]

    # Try case-insensitive match
    test_lower = test_name.lower()
    for key, value in REFERENCE_RANGES.items():
        if key.lower() == test_lower:
            return value

    # Try partial match
    for key, value in REFERENCE_RANGES.items():
        if test_lower in key.lower() or key.lower() in test_lower:
            return value

    # No match found
    return (None, None, "")
```

---

## 3. Trend Calculator Service

**File**: `/home/user/emr/src/services/trend_calculator.py`

### Calculate Trend Direction

```python
def calculate_trend(values: List[float], dates: List[date] = None) -> str:
    """
    Calculate trend direction from a series of values.

    Args:
        values: List of numeric values
        dates: Optional list of dates corresponding to values

    Returns:
        "↑" for rising, "↓" for falling, "→" for stable/mixed
    """
    if len(values) < 2:
        return "→"

    # Use last 3 values for trend calculation
    recent = values[-3:]

    # Check if consistently rising
    if len(recent) >= 2:
        rising_count = 0
        falling_count = 0

        for i in range(1, len(recent)):
            if recent[i] > recent[i-1]:
                rising_count += 1
            elif recent[i] < recent[i-1]:
                falling_count += 1

        # If all comparisons show same direction
        if rising_count > 0 and falling_count == 0:
            return "↑"
        elif falling_count > 0 and rising_count == 0:
            return "↓"

    return "→"
```

### Prepare Chart Data

```python
def prepare_chart_data(
    investigations: List,
    test_name: str,
    time_range: str = "All"
) -> Tuple[List[Dict], float, float]:
    """
    Prepare data for charting from investigations.

    Args:
        investigations: List of Investigation objects
        test_name: Name of test to filter
        time_range: Time range filter ("6M", "1Y", "All")

    Returns:
        Tuple of (data_points, min_value, max_value)
        data_points is list of {date, value, is_abnormal}
    """
    # Filter investigations for this test
    test_data = [
        inv for inv in investigations
        if inv.test_name.lower() == test_name.lower()
    ]

    if not test_data:
        return [], 0, 0

    # Convert to data points
    data_points = []
    for inv in test_data:
        if inv.result and inv.test_date:
            try:
                # Try to parse result as float
                value = float(inv.result)
                data_points.append({
                    "date": inv.test_date,
                    "value": value,
                    "is_abnormal": inv.is_abnormal,
                    "unit": inv.unit or "",
                    "reference_range": inv.reference_range or ""
                })
            except ValueError:
                # Skip non-numeric results
                continue

    # Sort by date
    data_points.sort(key=lambda x: x["date"])

    # Filter by time range
    data_points = filter_by_time_range(data_points, time_range)

    # Calculate min/max for chart scaling
    if data_points:
        values = [p["value"] for p in data_points]
        min_val = min(values)
        max_val = max(values)
        # Add 10% padding
        padding = (max_val - min_val) * 0.1
        min_val -= padding
        max_val += padding
    else:
        min_val = 0
        max_val = 0

    return data_points, min_val, max_val
```

### Generate Trend Summary

```python
def get_trend_summary(
    test_name: str,
    values: List[float],
    dates: List[date],
    normal_min: float = None,
    normal_max: float = None
) -> str:
    """
    Generate a human-readable summary of the trend.

    Returns:
        Summary string like "Creatinine is above normal (16.7% increase) and trending upward"
    """
    if not values:
        return f"No data available for {test_name}"

    current = values[-1]
    trend = calculate_trend(values, dates)

    # Determine if current value is abnormal
    abnormal = False
    if normal_min is not None and current < normal_min:
        abnormal = True
        status = "below normal"
    elif normal_max is not None and current > normal_max:
        abnormal = True
        status = "above normal"
    else:
        status = "normal"

    # Calculate change if we have previous value
    if len(values) >= 2:
        prev = values[-2]
        pct_change = calculate_percentage_change(prev, current)
        change_str = f"{abs(pct_change):.1f}% {'increase' if pct_change > 0 else 'decrease'}"
    else:
        change_str = "no previous data"

    summary = f"{test_name} is {status} ({change_str})"

    if trend == "↑":
        summary += " and trending upward"
    elif trend == "↓":
        summary += " and trending downward"
    else:
        summary += " and stable"

    return summary
```

---

## 4. Integration in Central Panel

**File**: `/home/user/emr/src/ui/central_panel.py`

### Trends Tab Definition

```python
# Trends tab content (dynamically built when patient is selected)
self.trends_container = ft.Container(
    content=ft.Text(
        "Select a patient to view trends",
        size=14,
        color=ft.Colors.GREY_600,
        italic=True
    ),
    padding=20,
    alignment=ft.alignment.center,
    expand=True,
)

# ... in tabs definition ...
ft.Tab(
    text="Trends",
    icon=ft.Icons.TRENDING_UP,
    content=self.trends_container,
),
```

### Building Trend Panels

```python
def _build_trends_tab(self) -> ft.Control:
    """Build the trends tab with pre-built trend panels."""
    panels = []

    for panel_name, test_names in TREND_PANELS.items():
        panel_items = []

        for test_name in test_names:
            # Get all investigations for this test
            test_invs = [
                inv for inv in self.investigations
                if inv.test_name.lower() == test_name.lower() and inv.result
            ]

            if not test_invs:
                continue

            # Get latest value
            latest = test_invs[-1]
            try:
                latest_value = float(latest.result)
                value_str = f"{latest_value:.1f} {latest.unit}"
            except ValueError:
                value_str = latest.result

            # Calculate trend
            trend_arrow = "→"
            if len(test_invs) >= 2:
                try:
                    values = [float(inv.result) for inv in test_invs[-3:]]
                    trend_arrow = calculate_trend(values)
                except ValueError:
                    pass

            # Get reference range
            normal_min, normal_max, _ = get_reference_range(test_name)

            # Determine if abnormal
            is_abnormal = latest.is_abnormal

            # Create panel item
            panel_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(test_name, size=12, weight=ft.FontWeight.W_500),
                            ft.Text(value_str, size=11, color=ft.Colors.GREY_700),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.Text(
                                trend_arrow,
                                size=16,
                                color=ft.Colors.ORANGE_700 if trend_arrow == "↑" else
                                      ft.Colors.BLUE_700 if trend_arrow == "↓" else
                                      ft.Colors.GREY_600
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SHOW_CHART,
                                icon_size=14,
                                tooltip="View trend",
                                icon_color=ft.Colors.BLUE_700,
                                on_click=lambda e, tn=test_name: self._show_trend_from_panel(e, tn),
                            ),
                        ], spacing=0),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=8,
                    bgcolor=ft.Colors.RED_50 if is_abnormal else ft.Colors.WHITE,
                    border_radius=5,
                )
            )

        if panel_items:
            panels.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"{panel_name.upper()} PANEL",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_700
                        ),
                        ft.Column(panel_items, spacing=5),
                    ], spacing=10),
                    padding=15,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    width=250,
                )
            )

    # Arrange panels in a grid (3 columns)
    rows = []
    for i in range(0, len(panels), 3):
        row_panels = panels[i:i+3]
        rows.append(ft.Row(row_panels, spacing=15, wrap=True))

    return ft.Container(
        content=ft.Column(
            rows,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=20,
        expand=True,
    )
```

### Show Trend Chart from Investigation

```python
def _show_trend_chart(self, e, inv: Investigation):
    """Show trend chart dialog for an investigation."""
    if not e.page or not self.current_patient:
        return

    # Get all investigations for this test
    test_investigations = [
        i for i in self.investigations
        if i.test_name.lower() == inv.test_name.lower()
    ]

    # Show dialog
    dialog = LabTrendsDialog(
        test_name=inv.test_name,
        investigations=test_investigations,
        all_investigations=self.investigations
    )
    dialog.show(e.page)
```

### Investigation Card with Trend Icon

```python
# In _create_investigation_card method
ft.Row([
    ft.Text(inv.test_name, size=14, weight=ft.FontWeight.W_500),
    ft.Text(trend_arrow, size=14) if trend_arrow != "→" else ft.Container(),
    ft.IconButton(
        icon=ft.Icons.SHOW_CHART,
        icon_size=16,
        tooltip="View trend chart",
        icon_color=ft.Colors.BLUE_700,
        on_click=lambda e, i=inv: self._show_trend_chart(e, i),
    ),
], spacing=5)
```

---

## 5. Lab Trends Dialog

**File**: `/home/user/emr/src/ui/lab_trends_dialog.py`

### Dialog Class

```python
class LabTrendsDialog:
    """Dialog for viewing lab trends with time range controls."""

    def __init__(
        self,
        test_name: str,
        investigations: List[Investigation],
        all_investigations: List[Investigation] = None,
    ):
        """
        Initialize lab trends dialog.

        Args:
            test_name: Name of the test to show
            investigations: List of investigations for this test
            all_investigations: All investigations for the patient (for comparison)
        """
        self.test_name = test_name
        self.investigations = investigations
        self.all_investigations = all_investigations or investigations
        self.time_range = "All"
        self.dialog: Optional[ft.AlertDialog] = None
        self.chart_container: Optional[ft.Container] = None
```

### Show Dialog Method

```python
def show(self, page: ft.Page):
    """Show the dialog."""
    # Get reference range
    normal_min, normal_max, unit = get_reference_range(self.test_name)

    # Prepare initial data
    data_points, min_val, max_val = prepare_chart_data(
        self.investigations,
        self.test_name,
        self.time_range
    )

    # Calculate trend
    values = [p["value"] for p in data_points]
    dates = [p["date"] for p in data_points]
    trend_arrow = calculate_trend(values, dates)

    # Get current value
    current_value = values[-1] if values else None
    current_str = f"{current_value:.2f} {unit}" if current_value is not None else "N/A"

    # Create trend summary
    trend_summary = ""
    if values:
        trend_summary = get_trend_summary(
            self.test_name,
            values,
            dates,
            normal_min,
            normal_max
        )

    # Create chart
    chart = LabTrendChart(
        test_name=self.test_name,
        data_points=data_points,
        normal_min=normal_min,
        normal_max=normal_max,
        unit=unit,
        width=700,
        height=350,
    )

    # ... rest of dialog UI construction ...
```

---

## Files Created/Modified Summary

### Existing Implementation Files (All Created Before Task)
1. `/home/user/emr/src/ui/components/lab_trend_chart.py` - 262 lines
2. `/home/user/emr/src/services/reference_ranges.py` - 151 lines
3. `/home/user/emr/src/services/trend_calculator.py` - 221 lines
4. `/home/user/emr/src/ui/lab_trends_dialog.py` - 244 lines
5. `/home/user/emr/src/ui/central_panel.py` - Trends tab integration

**Total Implementation**: 878 lines (excluding central_panel integration)

### Documentation Files (Created During Verification)
1. `/home/user/emr/LAB_TRENDS_IMPLEMENTATION.md` - Comprehensive technical documentation
2. `/home/user/emr/LAB_TRENDS_QUICK_GUIDE.md` - User guide and workflows
3. `/home/user/emr/TASK_COMPLETION_SUMMARY.md` - Task status and verification
4. `/home/user/emr/LAB_TRENDS_CODE_SAMPLES.md` - This file

---

## Usage Example

```python
# Example: Create a trend chart for Creatinine

from src.services.database import DatabaseService
from src.services.reference_ranges import get_reference_range
from src.services.trend_calculator import prepare_chart_data
from src.ui.components.lab_trend_chart import LabTrendChart

# Initialize database
db = DatabaseService()

# Get patient's investigations
patient_id = 123
investigations = db.get_patient_investigations(patient_id)

# Prepare chart data for Creatinine
data_points, min_val, max_val = prepare_chart_data(
    investigations,
    test_name="Creatinine",
    time_range="1Y"  # Last 1 year
)

# Get reference range
normal_min, normal_max, unit = get_reference_range("Creatinine")
# Returns: (0.7, 1.3, "mg/dL")

# Create chart component
chart = LabTrendChart(
    test_name="Creatinine",
    data_points=data_points,
    normal_min=normal_min,
    normal_max=normal_max,
    unit=unit,
    width=700,
    height=350
)

# Add to page (in Flet app)
page.add(chart)
```

---

**Verification Status**: ✅ COMPLETE
**All Code Samples**: Extracted from actual implementation files
**Last Verified**: January 5, 2026
