"""Trend calculation utilities for lab results."""

from typing import List, Dict, Tuple
from datetime import date, datetime, timedelta


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


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.

    Args:
        old_value: Previous value
        new_value: Current value

    Returns:
        Percentage change (positive for increase, negative for decrease)
    """
    if old_value == 0:
        return 0.0

    return ((new_value - old_value) / old_value) * 100


def filter_by_time_range(
    data_points: List[Dict],
    time_range: str
) -> List[Dict]:
    """
    Filter data points by time range.

    Args:
        data_points: List of data points with 'date' field
        time_range: One of "6M", "1Y", "All"

    Returns:
        Filtered list of data points
    """
    if time_range == "All" or not data_points:
        return data_points

    today = date.today()

    if time_range == "6M":
        cutoff = today - timedelta(days=180)
    elif time_range == "1Y":
        cutoff = today - timedelta(days=365)
    else:
        return data_points

    filtered = []
    for point in data_points:
        point_date = point.get("date")
        if isinstance(point_date, str):
            try:
                point_date = datetime.strptime(point_date, "%Y-%m-%d").date()
            except ValueError:
                continue
        if point_date and point_date >= cutoff:
            filtered.append(point)

    return filtered


def get_trend_summary(
    test_name: str,
    values: List[float],
    dates: List[date],
    normal_min: float = None,
    normal_max: float = None
) -> str:
    """
    Generate a human-readable summary of the trend.

    Args:
        test_name: Name of the test
        values: List of values
        dates: List of corresponding dates
        normal_min: Lower bound of normal range
        normal_max: Upper bound of normal range

    Returns:
        Summary string
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
