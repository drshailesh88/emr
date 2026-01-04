# Feature: Lab Trends Visualization

> Show investigation results over time as charts for better clinical insight

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Currently, lab results are shown as a list. Doctors must mentally track trends. A creatinine of 1.4 means nothing without context - was it 1.0 last month (worsening) or 2.0 (improving)? Visual trends would enable faster, better clinical decisions.

## User Stories

### Primary User Story
**As a** doctor
**I want to** see lab values charted over time
**So that** I can quickly understand if a patient is improving or worsening

### Additional Stories
- As a doctor, I want to see when values crossed normal ranges
- As a doctor, I want to compare multiple labs on one chart (e.g., BUN and Creatinine)
- As a doctor, I want to see the trend with a single click

## Requirements

### Functional Requirements

**Trend Charts:**
1. **FR-1**: Line chart for any numeric investigation over time
2. **FR-2**: Show normal range as shaded region
3. **FR-3**: Highlight values outside normal range
4. **FR-4**: Show data points with hover for exact values
5. **FR-5**: Zoom/pan for long time ranges

**Multi-Lab Comparison:**
6. **FR-6**: Overlay multiple related labs (e.g., FBS + PPBS + HbA1c)
7. **FR-7**: Dual Y-axis for different scales

**Quick Access:**
8. **FR-8**: Click any investigation to see trend
9. **FR-9**: "Trends" tab in patient view
10. **FR-10**: Pre-built trend panels for common combinations

**Smart Insights:**
11. **FR-11**: Calculate trend direction (improving/worsening/stable)
12. **FR-12**: Show percentage change from last value
13. **FR-13**: AI summary of trends (via RAG)

### Non-Functional Requirements
1. **NFR-1**: Charts render in < 500ms
2. **NFR-2**: Works with 5+ years of data
3. **NFR-3**: Offline (no external charting services)

## Acceptance Criteria

- [ ] Clicking any lab value opens trend chart
- [ ] Chart shows all values for that test over time
- [ ] Normal range shown as green shaded area
- [ ] Abnormal points highlighted in red
- [ ] Hover shows date and exact value
- [ ] "Trends" tab shows common panels
- [ ] Can select multiple tests for comparison
- [ ] Trend direction shown (↑ worsening / ↓ improving / → stable)

## Chart Library

Using Flet's built-in charting or matplotlib-based rendering:

```python
import flet as ft

# Example: Line chart for creatinine
chart = ft.LineChart(
    data_series=[
        ft.LineChartData(
            data_points=[
                ft.LineChartDataPoint(x=1, y=1.0),
                ft.LineChartDataPoint(x=2, y=1.2),
                ft.LineChartDataPoint(x=3, y=1.4),
            ],
            color=ft.colors.BLUE
        )
    ],
    # Normal range overlay
    horizontal_grid_lines=ft.ChartGridLines(
        interval=0.3, color=ft.colors.GREEN_100
    )
)
```

## UI Design

### Trend Chart View
```
┌──────────────────────────────────────────────────────────────────┐
│ Lab Trends: Creatinine                                       [X] │
├──────────────────────────────────────────────────────────────────┤
│ Current: 1.4 mg/dL  │  Normal: 0.7-1.3  │  Trend: ↑ Worsening   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  2.0 ┤                                                           │
│      │                                            ● 1.4         │
│  1.5 ┤                              ● 1.3                        │
│      │              ● 1.2                                        │
│  1.0 ┤  ● 1.0  ● 1.1   ═══════════════════════════════ (normal) │
│      │                                                           │
│  0.5 ┤                                                           │
│      └──────────────────────────────────────────────────────────│
│       Jan    Mar    May    Jul    Sep    Nov    Jan             │
│       2025   2025   2025   2025   2025   2025   2026            │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ [+ Add BUN] [+ Add eGFR]                   [6M] [1Y] [All]      │
└──────────────────────────────────────────────────────────────────┘
```

### Trends Tab
```
┌──────────────────────────────────────────────────────────────────┐
│ [Prescription] [History] [Labs] [Trends]                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ RENAL PANEL           DIABETIC PANEL         LIPID PANEL        │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│ │ Creatinine ↑     │  │ FBS →            │  │ LDL ↓            │ │
│ │ BUN →            │  │ PPBS ↑           │  │ HDL →            │ │
│ │ eGFR ↓           │  │ HbA1c ↑          │  │ TG ↓             │ │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                  │
│ CARDIAC PANEL         THYROID PANEL         LIVER PANEL         │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│ │ Troponin →       │  │ TSH →            │  │ ALT ↑            │ │
│ │ BNP →            │  │ T3 →             │  │ AST →            │ │
│ │ CK-MB →          │  │ T4 →             │  │ ALP →            │ │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Pre-built Trend Panels

| Panel | Labs Included |
|-------|---------------|
| Renal | Creatinine, BUN, eGFR, Potassium |
| Diabetic | FBS, PPBS, HbA1c |
| Lipid | Total Cholesterol, LDL, HDL, Triglycerides |
| Thyroid | TSH, T3, T4 |
| Liver | ALT, AST, ALP, Bilirubin |
| Cardiac | Troponin, BNP, CK-MB |
| CBC | Hemoglobin, WBC, Platelets |

## Trend Calculation

```python
def calculate_trend(values: list[float], dates: list[date]) -> str:
    if len(values) < 2:
        return "→"  # Not enough data

    recent = values[-3:]  # Last 3 values
    if all(recent[i] > recent[i-1] for i in range(1, len(recent))):
        return "↑"  # Rising
    elif all(recent[i] < recent[i-1] for i in range(1, len(recent))):
        return "↓"  # Falling
    else:
        return "→"  # Stable/mixed
```

## Out of Scope

- Predictive analytics
- Trend alerts/notifications
- Export charts as images

## Dependencies

- Flet charts or matplotlib
- Investigation data in database

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Too many data points | Chart cluttered | Aggregate, allow zoom |
| Different units for same test | Incorrect trends | Standardize units on entry |
| Chart rendering slow | UX lag | Cache, lazy load |

## Open Questions

- [x] Charting library? **Decision: Flet built-in charts**
- [x] Default time range? **Decision: 1 year, adjustable**

---
*Spec created: 2026-01-02*
