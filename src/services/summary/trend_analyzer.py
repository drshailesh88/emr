"""Analyze trends in patient data over time."""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from datetime import date, datetime, timedelta
from enum import Enum
import statistics


class TrendDirection(Enum):
    """Direction of a clinical parameter trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class Trend:
    """Represents a trend in a clinical parameter."""
    parameter: str
    display_name: str
    direction: TrendDirection
    values: List[Tuple[date, float]]
    first_value: float
    last_value: float
    change_absolute: float
    change_percent: float
    interpretation: str
    action_needed: bool
    suggested_action: Optional[str]
    target_value: Optional[float]
    unit: str
    is_concerning: bool = False


class TrendAnalyzer:
    """Analyze trends in patient clinical data."""

    PARAMETER_DEFINITIONS = {
        "hba1c": {
            "display_name": "HbA1c",
            "unit": "%",
            "target": 7.0,
            "improving_direction": "decreasing",
            "concerning_threshold": 8.0,
            "critical_threshold": 10.0,
            "min_change_significant": 0.3,
        },
        "fasting_glucose": {
            "display_name": "Fasting Glucose",
            "unit": "mg/dL",
            "target": 100,
            "improving_direction": "decreasing",
            "concerning_threshold": 126,
            "critical_threshold": 200,
            "min_change_significant": 10,
        },
        "creatinine": {
            "display_name": "Creatinine",
            "unit": "mg/dL",
            "target": 1.2,
            "improving_direction": "stable_or_decreasing",
            "concerning_threshold": 1.5,
            "critical_threshold": 3.0,
            "min_change_significant": 0.2,
        },
        "egfr": {
            "display_name": "eGFR",
            "unit": "mL/min/1.73m²",
            "target": 90,
            "improving_direction": "stable_or_increasing",
            "concerning_threshold": 60,
            "critical_threshold": 30,
            "min_change_significant": 5,
        },
        "systolic_bp": {
            "display_name": "Systolic BP",
            "unit": "mmHg",
            "target": 130,
            "improving_direction": "decreasing",
            "concerning_threshold": 140,
            "critical_threshold": 180,
            "min_change_significant": 5,
        },
        "diastolic_bp": {
            "display_name": "Diastolic BP",
            "unit": "mmHg",
            "target": 80,
            "improving_direction": "decreasing",
            "concerning_threshold": 90,
            "critical_threshold": 120,
            "min_change_significant": 5,
        },
        "ldl": {
            "display_name": "LDL Cholesterol",
            "unit": "mg/dL",
            "target": 100,
            "improving_direction": "decreasing",
            "concerning_threshold": 130,
            "critical_threshold": 190,
            "min_change_significant": 10,
        },
        "hdl": {
            "display_name": "HDL Cholesterol",
            "unit": "mg/dL",
            "target": 50,
            "improving_direction": "increasing",
            "concerning_threshold": 40,
            "critical_threshold": 30,
            "min_change_significant": 5,
        },
        "triglycerides": {
            "display_name": "Triglycerides",
            "unit": "mg/dL",
            "target": 150,
            "improving_direction": "decreasing",
            "concerning_threshold": 200,
            "critical_threshold": 500,
            "min_change_significant": 20,
        },
        "weight": {
            "display_name": "Weight",
            "unit": "kg",
            "target": None,
            "improving_direction": "context_dependent",
            "min_change_significant": 2,
        },
        "bmi": {
            "display_name": "BMI",
            "unit": "kg/m²",
            "target": 25,
            "improving_direction": "decreasing_if_high",
            "concerning_threshold": 30,
            "critical_threshold": 40,
            "min_change_significant": 0.5,
        },
        "hemoglobin": {
            "display_name": "Hemoglobin",
            "unit": "g/dL",
            "target": 13,
            "improving_direction": "increasing_if_low",
            "concerning_threshold": 10,
            "critical_threshold": 7,
            "min_change_significant": 0.5,
        },
        "potassium": {
            "display_name": "Potassium",
            "unit": "mEq/L",
            "target": 4.0,
            "improving_direction": "normalize",
            "concerning_threshold_low": 3.5,
            "concerning_threshold_high": 5.0,
            "critical_threshold_low": 3.0,
            "critical_threshold_high": 5.5,
            "min_change_significant": 0.3,
        },
        "sodium": {
            "display_name": "Sodium",
            "unit": "mEq/L",
            "target": 140,
            "improving_direction": "normalize",
            "concerning_threshold_low": 135,
            "concerning_threshold_high": 145,
            "min_change_significant": 2,
        },
    }

    def __init__(self):
        """Initialize the trend analyzer."""
        pass

    def analyze_trend(
        self,
        parameter: str,
        values: List[Tuple[date, float]]
    ) -> Trend:
        """
        Analyze trend for a single parameter.

        Args:
            parameter: Parameter name (e.g., 'hba1c', 'creatinine')
            values: List of (date, value) tuples

        Returns:
            Trend object with analysis results
        """
        definition = self.PARAMETER_DEFINITIONS.get(
            parameter.lower(),
            {"display_name": parameter, "unit": "", "improving_direction": "unknown"}
        )

        if len(values) < 2:
            return Trend(
                parameter=parameter,
                display_name=definition.get("display_name", parameter),
                direction=TrendDirection.INSUFFICIENT_DATA,
                values=values,
                first_value=values[0][1] if values else 0,
                last_value=values[-1][1] if values else 0,
                change_absolute=0,
                change_percent=0,
                interpretation="Not enough data points to determine trend",
                action_needed=False,
                suggested_action=None,
                target_value=definition.get("target"),
                unit=definition.get("unit", ""),
            )

        # Sort by date
        sorted_values = sorted(values, key=lambda x: x[0])
        first_value = sorted_values[0][1]
        last_value = sorted_values[-1][1]

        # Calculate changes
        change_absolute = last_value - first_value
        change_percent = (change_absolute / first_value * 100) if first_value != 0 else 0

        # Determine direction
        direction = self._determine_direction(
            parameter, change_absolute, definition
        )

        # Check if concerning
        is_concerning = self._is_concerning(last_value, definition)

        # Generate interpretation
        interpretation = self._generate_interpretation(
            parameter, direction, first_value, last_value, definition
        )

        # Determine if action needed
        action_needed = (
            direction == TrendDirection.WORSENING or
            is_concerning
        )

        # Suggest action if needed
        suggested_action = None
        if action_needed:
            suggested_action = self._suggest_action(
                parameter, direction, last_value, definition
            )

        return Trend(
            parameter=parameter,
            display_name=definition.get("display_name", parameter),
            direction=direction,
            values=sorted_values,
            first_value=first_value,
            last_value=last_value,
            change_absolute=round(change_absolute, 2),
            change_percent=round(change_percent, 1),
            interpretation=interpretation,
            action_needed=action_needed,
            suggested_action=suggested_action,
            target_value=definition.get("target"),
            unit=definition.get("unit", ""),
            is_concerning=is_concerning,
        )

    def _determine_direction(
        self,
        parameter: str,
        change: float,
        definition: Dict
    ) -> TrendDirection:
        """Determine trend direction based on change and expected direction."""
        improving_direction = definition.get("improving_direction", "unknown")
        min_change = definition.get("min_change_significant", 0)

        # Check if change is significant
        if abs(change) < min_change:
            return TrendDirection.STABLE

        if improving_direction == "decreasing":
            return TrendDirection.IMPROVING if change < 0 else TrendDirection.WORSENING
        elif improving_direction == "increasing":
            return TrendDirection.IMPROVING if change > 0 else TrendDirection.WORSENING
        elif improving_direction == "stable_or_decreasing":
            return TrendDirection.WORSENING if change > min_change else TrendDirection.STABLE
        elif improving_direction == "stable_or_increasing":
            return TrendDirection.WORSENING if change < -min_change else TrendDirection.STABLE
        else:
            # For context-dependent or unknown, just report direction
            return TrendDirection.STABLE

    def _is_concerning(self, value: float, definition: Dict) -> bool:
        """Check if current value is concerning."""
        concerning = definition.get("concerning_threshold")
        critical = definition.get("critical_threshold")
        improving = definition.get("improving_direction", "")

        if concerning is None:
            return False

        if "decreasing" in improving:
            # Higher is worse
            return value >= concerning
        elif "increasing" in improving:
            # Lower is worse
            return value <= concerning
        elif improving == "normalize":
            # Both directions can be concerning
            low = definition.get("concerning_threshold_low", 0)
            high = definition.get("concerning_threshold_high", float('inf'))
            return value < low or value > high

        return False

    def _generate_interpretation(
        self,
        parameter: str,
        direction: TrendDirection,
        first_value: float,
        last_value: float,
        definition: Dict
    ) -> str:
        """Generate natural language interpretation of trend."""
        display_name = definition.get("display_name", parameter)
        unit = definition.get("unit", "")
        target = definition.get("target")

        if direction == TrendDirection.INSUFFICIENT_DATA:
            return "Not enough data to assess trend"

        direction_word = {
            TrendDirection.IMPROVING: "improving",
            TrendDirection.WORSENING: "worsening",
            TrendDirection.STABLE: "stable",
        }.get(direction, "unchanged")

        base = f"{display_name} {direction_word}: {first_value}{unit} → {last_value}{unit}"

        if target and direction == TrendDirection.IMPROVING:
            if self._at_target(last_value, target, definition):
                return f"{base}. Now at target."
            else:
                return f"{base}. Getting closer to target of {target}{unit}."
        elif direction == TrendDirection.WORSENING:
            return f"{base}. Needs attention."
        else:
            return f"{base}."

    def _at_target(
        self,
        value: float,
        target: float,
        definition: Dict
    ) -> bool:
        """Check if value is at target."""
        improving = definition.get("improving_direction", "")
        tolerance = definition.get("min_change_significant", 0)

        if "decreasing" in improving:
            return value <= target + tolerance
        elif "increasing" in improving:
            return value >= target - tolerance
        else:
            return abs(value - target) <= tolerance

    def _suggest_action(
        self,
        parameter: str,
        direction: TrendDirection,
        value: float,
        definition: Dict
    ) -> str:
        """Suggest action for concerning trend."""
        actions = {
            "hba1c": "Review diabetes management. Consider intensifying therapy.",
            "creatinine": "Monitor renal function closely. Check for nephrotoxic drugs.",
            "egfr": "Assess for CKD progression. Consider nephrology referral.",
            "systolic_bp": "Review antihypertensive regimen. Check compliance.",
            "diastolic_bp": "Review antihypertensive regimen. Check compliance.",
            "ldl": "Review statin therapy. Reinforce lifestyle measures.",
            "fasting_glucose": "Check HbA1c. Review diabetes medications.",
            "hemoglobin": "Investigate cause of anemia. Consider iron studies.",
            "potassium": "Check medications affecting potassium. Repeat test.",
        }

        return actions.get(
            parameter.lower(),
            "Review recent changes and consider intervention."
        )

    def analyze_all_trends(
        self,
        patient_data: Dict[str, List[Tuple[date, float]]]
    ) -> List[Trend]:
        """
        Analyze all available trends for a patient.

        Args:
            patient_data: Dict mapping parameter names to value lists

        Returns:
            List of Trend objects
        """
        trends = []
        for parameter, values in patient_data.items():
            if values:
                trend = self.analyze_trend(parameter, values)
                trends.append(trend)
        return trends

    def get_concerning_trends(self, trends: List[Trend]) -> List[Trend]:
        """Filter to only concerning or worsening trends."""
        return [
            t for t in trends
            if t.direction == TrendDirection.WORSENING or t.is_concerning
        ]

    def get_improving_trends(self, trends: List[Trend]) -> List[Trend]:
        """Filter to improving trends."""
        return [t for t in trends if t.direction == TrendDirection.IMPROVING]

    def predict_trajectory(
        self,
        trend: Trend,
        months_ahead: int = 3
    ) -> Dict:
        """
        Predict where a parameter is heading.

        Uses simple linear extrapolation.
        """
        if len(trend.values) < 2:
            return {
                "can_predict": False,
                "reason": "Insufficient data points",
            }

        # Calculate average change per month
        sorted_values = sorted(trend.values, key=lambda x: x[0])
        first_date = sorted_values[0][0]
        last_date = sorted_values[-1][0]
        days_elapsed = (last_date - first_date).days

        if days_elapsed < 30:
            return {
                "can_predict": False,
                "reason": "Time span too short for prediction",
            }

        months_elapsed = days_elapsed / 30.0
        change_per_month = trend.change_absolute / months_elapsed

        # Predict future value
        predicted_value = trend.last_value + (change_per_month * months_ahead)

        # Determine if trajectory is concerning
        definition = self.PARAMETER_DEFINITIONS.get(trend.parameter.lower(), {})
        target = definition.get("target")

        return {
            "can_predict": True,
            "predicted_value": round(predicted_value, 2),
            "months_ahead": months_ahead,
            "change_per_month": round(change_per_month, 2),
            "will_reach_target": self._will_reach_target(
                trend.last_value, predicted_value, target, definition
            ) if target else None,
            "will_be_concerning": self._is_concerning(predicted_value, definition),
        }

    def _will_reach_target(
        self,
        current: float,
        predicted: float,
        target: float,
        definition: Dict
    ) -> bool:
        """Check if trajectory will reach target."""
        improving = definition.get("improving_direction", "")

        if "decreasing" in improving:
            # Need to go down to target
            return predicted <= target and current > target
        elif "increasing" in improving:
            # Need to go up to target
            return predicted >= target and current < target
        return False

    def get_intervention_suggestions(
        self,
        worsening_trends: List[Trend]
    ) -> List[str]:
        """Suggest interventions for worsening trends."""
        suggestions = []

        for trend in worsening_trends:
            if trend.suggested_action:
                suggestions.append(
                    f"{trend.display_name}: {trend.suggested_action}"
                )

        return suggestions
