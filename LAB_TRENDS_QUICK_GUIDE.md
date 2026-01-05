# Lab Trend Charts - Quick User Guide

## How to Use Lab Trend Charts in DocAssist EMR

### Method 1: From Investigations Tab

1. **Select a patient** from the patient panel
2. **Click "Investigations" tab** in the central panel
3. **Find any investigation** (e.g., "Creatinine: 1.4 mg/dL")
4. **Click the chart icon** (📊) next to the investigation
5. **View the trend chart** in the popup dialog

**Features in the dialog**:
- Current value and status
- Normal range
- Trend direction (↑ rising / ↓ falling / → stable)
- AI-generated summary
- Time range filters: [6M] [1Y] [All]
- Interactive chart with tooltips

### Method 2: From Trends Tab

1. **Select a patient** from the patient panel
2. **Click "Trends" tab** in the central panel
3. **View all trend panels**:
   - Renal Panel (Creatinine, BUN, eGFR, Potassium)
   - Diabetic Panel (FBS, PPBS, HbA1c)
   - Lipid Panel (Cholesterol, LDL, HDL, Triglycerides)
   - Thyroid Panel (TSH, T3, T4)
   - Liver Panel (ALT, AST, ALP, Bilirubin)
   - Cardiac Panel (Troponin, BNP, CK-MB)
   - CBC Panel (Hemoglobin, WBC, Platelets)
4. **Each panel shows**:
   - Latest value for each test
   - Trend arrow with color
   - Chart icon to expand
5. **Click any chart icon** to view detailed trend

### Understanding the Charts

#### Chart Elements

```
┌────────────────────────────────────────────────┐
│ Lab Trends: Creatinine                     [X] │
├────────────────────────────────────────────────┤
│ Current: 1.4 mg/dL  │  Normal: 0.7-1.3 mg/dL  │
│ Trend: ↑ Rising                                │
├────────────────────────────────────────────────┤
│                                                │
│    1.5 ┤                              ● 1.4   │ ← Latest value (red if abnormal)
│        │                    ● 1.3             │
│    1.2 ┤          ● 1.2                       │
│        │                                      │
│    1.0 ┤ ● 1.0   ═══════ (normal) ═══════    │ ← Normal range (green)
│        │                                      │
│    0.7 ┤                                      │
│        └──────────────────────────────────    │
│         Jan    Apr    Jul    Oct    Jan      │ ← Dates on X-axis
│         2025   2025   2025   2025   2026     │
│                                               │
├────────────────────────────────────────────────┤
│ Time Range: [6M] [1Y] [All]                   │ ← Filter by time period
└────────────────────────────────────────────────┘
```

#### Trend Indicators

| Symbol | Meaning | Color |
|--------|---------|-------|
| **↑** | Rising (worsening for most tests) | Orange |
| **↓** | Falling (improving for most tests) | Blue |
| **→** | Stable (no significant change) | Gray |

**Note**: For some tests, rising is good (e.g., HDL cholesterol, Hemoglobin). The trend arrow shows direction, not clinical interpretation.

#### Color Coding

- **Red dots**: Abnormal values (outside reference range)
- **Blue line**: Your values over time
- **Green dashed lines**: Normal range boundaries
- **Light blue area**: Below the trend line

### Clinical Interpretation Guide

#### Renal Function

**Creatinine Trend**:
- **Rising ↑**: Possible kidney function decline → Consider causes (dehydration, nephrotoxic drugs, progression of CKD)
- **Falling ↓**: Improving kidney function or muscle wasting
- **Stable →**: Kidney function steady

**eGFR Trend**:
- **Falling ↓**: Declining kidney function (more sensitive than creatinine)
- **Rising ↑**: Improving kidney function
- **Stable →**: CKD stable

#### Diabetic Control

**HbA1c Trend**:
- **Rising ↑**: Worsening diabetic control → Adjust medications/lifestyle
- **Falling ↓**: Improving control
- **Target**: Keep trending toward <6.5%

**FBS/PPBS Trend**:
- Complements HbA1c
- More variable day-to-day
- Useful for short-term adjustments

#### Lipid Profile

**LDL Cholesterol**:
- **Falling ↓**: Good! Target <100 mg/dL
- **Rising ↑**: Consider statin adjustment
- **Stable →**: Maintain current therapy if at goal

**HDL Cholesterol**:
- **Rising ↑**: Good! Higher is better (>40 mg/dL)
- **Falling ↓**: Consider lifestyle modifications

### Common Workflow Examples

#### Example 1: Diabetic Patient Follow-up

**Scenario**: Patient with Type 2 Diabetes, on Metformin 1000mg BD

**Steps**:
1. Open patient "Ramesh Kumar"
2. Go to **Trends** tab
3. Look at **Diabetic Panel**:
   - FBS: 110 mg/dL ↑ (rising)
   - HbA1c: 7.8% ↑ (rising)
4. Click chart icon next to HbA1c
5. **View chart**: Shows increase from 7.2% → 7.5% → 7.8% over 3 months
6. **AI Summary**: "HbA1c is above normal (8.3% increase) and trending upward"
7. **Clinical Decision**: Add SGLT2 inhibitor, increase Metformin dose

#### Example 2: CKD Monitoring

**Scenario**: Patient with hypertension, concern for kidney disease

**Steps**:
1. Open patient "Sita Devi"
2. Go to **Investigations** tab
3. Find latest Creatinine: 1.6 mg/dL
4. Click trend chart icon
5. **View chart**: Shows progression:
   - 6 months ago: 1.2 mg/dL (normal)
   - 3 months ago: 1.4 mg/dL (borderline)
   - Today: 1.6 mg/dL (abnormal)
6. **Trend**: ↑ Consistently rising
7. Click **[All]** to see full history (2 years)
8. **Clinical Decision**: Order eGFR, urine protein, consider nephrology referral

#### Example 3: Anemia Treatment Monitoring

**Scenario**: Patient on iron supplementation for anemia

**Steps**:
1. Open patient "Lakshmi Rao"
2. Go to **Trends** tab
3. Look at **CBC Panel**:
   - Hemoglobin: 11.8 g/dL ↑ (rising - good!)
4. Click chart icon
5. **View chart**: Shows improvement:
   - 2 months ago: 9.2 g/dL (severe anemia)
   - 1 month ago: 10.5 g/dL
   - Today: 11.8 g/dL (mild anemia)
6. **Trend**: ↑ Steady improvement
7. **Clinical Decision**: Continue iron for 3 more months, repeat in 1 month

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Tab → Ctrl+5** | Switch to Trends tab (if available in shortcuts) |
| **Esc** | Close trend chart dialog |
| **Ctrl+P** | Print current view (if needed) |

### Tips & Best Practices

1. **Regular Data Entry**: Update investigations promptly for accurate trends
2. **Consistent Units**: Ensure lab results use standard units (mg/dL, g/dL, etc.)
3. **Date Accuracy**: Always enter correct test dates
4. **Abnormal Flags**: Check "is abnormal" checkbox for out-of-range values
5. **Time Range**: Use 6M for acute changes, 1Y for chronic diseases, All for long-term trends
6. **Reference Ranges**: System uses standard Indian lab ranges (can be customized)

### Troubleshooting

**Q: Chart shows "No data available"**
- **A**: No investigations recorded for this test. Add investigations first.

**Q: Trend arrow not showing**
- **A**: Need at least 2 data points for trend calculation. Add more investigations.

**Q: Reference range looks wrong**
- **A**: Range is auto-detected by test name. Check spelling (e.g., "Creatinine" not "Serum Creatinine"). Reference ranges can be customized in settings.

**Q: Chart is cluttered with too many points**
- **A**: Use time range filters: [6M] or [1Y] to zoom in on recent data.

**Q: Want to compare FBS and HbA1c together**
- **A**: Use the Diabetic Panel in Trends tab. Both show side-by-side with individual chart icons.

### Advanced Features

#### Auto-Calculation of Trends
- System automatically calculates trend direction based on last 3 values
- **All rising**: ↑
- **All falling**: ↓
- **Mixed**: →

#### Percentage Change
- Shows in AI summary
- Example: "15.0% increase from last value"
- Helps quantify the change magnitude

#### Abnormal Detection
- Auto-flags values outside reference range
- Uses gender/age-specific ranges where applicable
- Highlights in red on chart

#### Hover Tooltips
- **Hover over any data point** to see:
  - Exact date (DD MMM YYYY)
  - Exact value with unit
  - Abnormal status

### Reference Ranges (Standard Values)

See `/home/user/emr/src/services/reference_ranges.py` for complete list.

**Most Common**:
- Creatinine: 0.7-1.3 mg/dL
- FBS: 70-100 mg/dL
- HbA1c: 4.0-6.5%
- Hemoglobin: 13-17 g/dL (male), 12-15 g/dL (female)
- Total Cholesterol: <200 mg/dL
- LDL: <100 mg/dL
- TSH: 0.4-4.0 mIU/L

---

**For detailed technical information, see**: `/home/user/emr/LAB_TRENDS_IMPLEMENTATION.md`
