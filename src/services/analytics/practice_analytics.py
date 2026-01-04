"""Practice performance analytics engine."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta
from enum import Enum
import statistics


@dataclass
class DailySummary:
    """Daily practice summary."""
    date: date
    patients_seen: int
    new_patients: int
    returning_patients: int
    total_revenue: float
    average_per_patient: float
    appointments_scheduled: int
    appointments_completed: int
    no_shows: int
    cancellations: int
    peak_hour: int  # 0-23
    busiest_slot: str


@dataclass
class WeeklySummary:
    """Weekly practice summary."""
    week_start: date
    week_end: date
    total_patients: int
    total_revenue: float
    daily_average_patients: float
    daily_average_revenue: float
    new_patient_count: int
    new_patient_percentage: float
    no_show_rate: float
    busiest_day: str
    comparison_to_last_week: Dict[str, float]


@dataclass
class RevenueAnalysis:
    """Revenue analysis breakdown."""
    period_start: date
    period_end: date
    total_revenue: float
    revenue_by_service: Dict[str, float]
    revenue_by_day: Dict[str, float]
    average_revenue_per_day: float
    average_revenue_per_patient: float
    trend: str  # 'increasing', 'stable', 'decreasing'
    projected_monthly: float


@dataclass
class PeakHoursAnalysis:
    """Analysis of peak hours."""
    hourly_distribution: Dict[int, int]  # hour -> patient count
    peak_hours: List[int]
    slow_hours: List[int]
    recommendations: List[str]


class PracticeAnalytics:
    """Practice performance analytics engine."""

    def __init__(self, db_service):
        """Initialize analytics engine."""
        self.db = db_service

    def get_daily_summary(self, target_date: date = None) -> DailySummary:
        """
        Get summary for a specific day.

        Args:
            target_date: Date to analyze (defaults to today)

        Returns:
            DailySummary object
        """
        if target_date is None:
            target_date = date.today()

        # Get visits for the day
        visits = self._get_visits_for_date(target_date)
        appointments = self._get_appointments_for_date(target_date)

        patients_seen = len(visits)
        new_patients = sum(1 for v in visits if v.get('is_new_patient', False))
        returning_patients = patients_seen - new_patients

        # Revenue calculation
        total_revenue = sum(v.get('amount', 0) for v in visits)
        avg_per_patient = total_revenue / patients_seen if patients_seen > 0 else 0

        # Appointment analysis
        completed = sum(1 for a in appointments if a.get('status') == 'completed')
        no_shows = sum(1 for a in appointments if a.get('status') == 'no_show')
        cancellations = sum(1 for a in appointments if a.get('status') == 'cancelled')

        # Peak hour analysis
        hour_counts = {}
        for v in visits:
            hour = v.get('visit_time', datetime.now()).hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 10
        busiest_slot = f"{peak_hour}:00 - {peak_hour + 1}:00"

        return DailySummary(
            date=target_date,
            patients_seen=patients_seen,
            new_patients=new_patients,
            returning_patients=returning_patients,
            total_revenue=total_revenue,
            average_per_patient=round(avg_per_patient, 2),
            appointments_scheduled=len(appointments),
            appointments_completed=completed,
            no_shows=no_shows,
            cancellations=cancellations,
            peak_hour=peak_hour,
            busiest_slot=busiest_slot,
        )

    def get_weekly_summary(self, week_start: date = None) -> WeeklySummary:
        """Get summary for a week."""
        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # Get daily summaries for the week
        daily_summaries = []
        current_date = week_start
        while current_date <= week_end:
            summary = self.get_daily_summary(current_date)
            daily_summaries.append(summary)
            current_date += timedelta(days=1)

        total_patients = sum(d.patients_seen for d in daily_summaries)
        total_revenue = sum(d.total_revenue for d in daily_summaries)
        new_patients = sum(d.new_patients for d in daily_summaries)

        # Find busiest day
        busiest_summary = max(daily_summaries, key=lambda d: d.patients_seen)
        busiest_day = busiest_summary.date.strftime("%A")

        # No-show rate
        total_scheduled = sum(d.appointments_scheduled for d in daily_summaries)
        total_no_shows = sum(d.no_shows for d in daily_summaries)
        no_show_rate = (total_no_shows / total_scheduled * 100) if total_scheduled > 0 else 0

        # Compare to last week
        last_week_start = week_start - timedelta(days=7)
        last_week_summary = self._get_week_totals(last_week_start)

        comparison = {
            "patients_change": self._calculate_change(
                total_patients, last_week_summary.get("patients", 0)
            ),
            "revenue_change": self._calculate_change(
                total_revenue, last_week_summary.get("revenue", 0)
            ),
        }

        return WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            total_patients=total_patients,
            total_revenue=total_revenue,
            daily_average_patients=total_patients / 7,
            daily_average_revenue=total_revenue / 7,
            new_patient_count=new_patients,
            new_patient_percentage=(new_patients / total_patients * 100) if total_patients > 0 else 0,
            no_show_rate=round(no_show_rate, 1),
            busiest_day=busiest_day,
            comparison_to_last_week=comparison,
        )

    def get_revenue_analysis(
        self,
        period_start: date,
        period_end: date
    ) -> RevenueAnalysis:
        """Analyze revenue for a period."""
        visits = self._get_visits_for_period(period_start, period_end)

        total_revenue = sum(v.get('amount', 0) for v in visits)

        # Revenue by service type
        revenue_by_service = {}
        for v in visits:
            service = v.get('service_type', 'Consultation')
            revenue_by_service[service] = revenue_by_service.get(service, 0) + v.get('amount', 0)

        # Revenue by day of week
        revenue_by_day = {}
        for v in visits:
            day_name = v.get('visit_date', date.today()).strftime("%A")
            revenue_by_day[day_name] = revenue_by_day.get(day_name, 0) + v.get('amount', 0)

        # Calculate averages and trend
        days_in_period = (period_end - period_start).days + 1
        avg_per_day = total_revenue / days_in_period if days_in_period > 0 else 0
        avg_per_patient = total_revenue / len(visits) if visits else 0

        # Determine trend by comparing first and second half
        mid_point = period_start + timedelta(days=days_in_period // 2)
        first_half = sum(v.get('amount', 0) for v in visits if v.get('visit_date', date.today()) < mid_point)
        second_half = total_revenue - first_half

        if second_half > first_half * 1.1:
            trend = "increasing"
        elif second_half < first_half * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        # Project monthly revenue
        projected_monthly = avg_per_day * 30

        return RevenueAnalysis(
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
            revenue_by_service=revenue_by_service,
            revenue_by_day=revenue_by_day,
            average_revenue_per_day=round(avg_per_day, 2),
            average_revenue_per_patient=round(avg_per_patient, 2),
            trend=trend,
            projected_monthly=round(projected_monthly, 2),
        )

    def get_peak_hours_analysis(self, period_days: int = 30) -> PeakHoursAnalysis:
        """Analyze peak hours over a period."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        visits = self._get_visits_for_period(start_date, end_date)

        # Count patients by hour
        hourly_distribution = {h: 0 for h in range(8, 21)}  # 8 AM to 8 PM
        for v in visits:
            hour = v.get('visit_time', datetime.now()).hour
            if 8 <= hour <= 20:
                hourly_distribution[hour] += 1

        # Identify peak and slow hours
        avg_count = statistics.mean(hourly_distribution.values()) if hourly_distribution else 0
        peak_hours = [h for h, c in hourly_distribution.items() if c > avg_count * 1.3]
        slow_hours = [h for h, c in hourly_distribution.items() if c < avg_count * 0.7]

        # Generate recommendations
        recommendations = []
        if slow_hours:
            slow_times = ", ".join(f"{h}:00" for h in sorted(slow_hours))
            recommendations.append(f"Consider offering discounts during slow hours: {slow_times}")
        if len(peak_hours) <= 2:
            recommendations.append("High concentration of patients - consider expanding peak hour capacity")
        if hourly_distribution.get(9, 0) > avg_count * 1.5:
            recommendations.append("9 AM is very busy - open early appointments to distribute load")

        return PeakHoursAnalysis(
            hourly_distribution=hourly_distribution,
            peak_hours=peak_hours,
            slow_hours=slow_hours,
            recommendations=recommendations,
        )

    def get_patient_flow_efficiency(self, period_days: int = 30) -> Dict:
        """Analyze patient flow efficiency."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        appointments = self._get_appointments_for_period(start_date, end_date)

        completed = [a for a in appointments if a.get('status') == 'completed']
        no_shows = [a for a in appointments if a.get('status') == 'no_show']
        cancellations = [a for a in appointments if a.get('status') == 'cancelled']
        rescheduled = [a for a in appointments if a.get('status') == 'rescheduled']

        total = len(appointments)

        return {
            "total_appointments": total,
            "completed": len(completed),
            "completion_rate": round(len(completed) / total * 100, 1) if total > 0 else 0,
            "no_show_count": len(no_shows),
            "no_show_rate": round(len(no_shows) / total * 100, 1) if total > 0 else 0,
            "cancellation_count": len(cancellations),
            "cancellation_rate": round(len(cancellations) / total * 100, 1) if total > 0 else 0,
            "rescheduled_count": len(rescheduled),
            "recommendations": self._get_efficiency_recommendations(no_shows, cancellations, total),
        }

    def _get_visits_for_date(self, target_date: date) -> List[Dict]:
        """Get visits for a specific date."""
        if self.db:
            return self.db.get_visits_by_date(target_date)
        return []

    def _get_visits_for_period(self, start: date, end: date) -> List[Dict]:
        """Get visits for a date range."""
        if self.db:
            return self.db.get_visits_by_date_range(start, end)
        return []

    def _get_appointments_for_date(self, target_date: date) -> List[Dict]:
        """Get appointments for a specific date."""
        if self.db:
            return self.db.get_appointments_by_date(target_date)
        return []

    def _get_appointments_for_period(self, start: date, end: date) -> List[Dict]:
        """Get appointments for a date range."""
        if self.db:
            return self.db.get_appointments_by_date_range(start, end)
        return []

    def _get_week_totals(self, week_start: date) -> Dict:
        """Get totals for a week."""
        week_end = week_start + timedelta(days=6)
        visits = self._get_visits_for_period(week_start, week_end)
        return {
            "patients": len(visits),
            "revenue": sum(v.get('amount', 0) for v in visits),
        }

    def _calculate_change(self, current: float, previous: float) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)

    def _get_efficiency_recommendations(
        self,
        no_shows: List,
        cancellations: List,
        total: int
    ) -> List[str]:
        """Generate recommendations for improving efficiency."""
        recommendations = []

        no_show_rate = len(no_shows) / total * 100 if total > 0 else 0
        cancel_rate = len(cancellations) / total * 100 if total > 0 else 0

        if no_show_rate > 10:
            recommendations.append(
                "High no-show rate (>10%). Consider implementing SMS reminders 24 hours before appointments."
            )
        if no_show_rate > 20:
            recommendations.append(
                "Very high no-show rate. Consider requiring confirmation or implementing a cancellation policy."
            )
        if cancel_rate > 15:
            recommendations.append(
                "High cancellation rate. Survey patients to understand reasons and reduce friction."
            )

        return recommendations
