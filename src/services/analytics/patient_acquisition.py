"""Track patient acquisition sources and growth."""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from enum import Enum


class AcquisitionSource(Enum):
    """Patient acquisition sources."""
    GOOGLE_MAPS = "google_maps"
    REFERRAL = "referral"
    WHATSAPP = "whatsapp"
    WALK_IN = "walk_in"
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    INSURANCE_PANEL = "insurance_panel"
    OTHER = "other"


@dataclass
class AcquisitionMetrics:
    """Patient acquisition metrics."""
    period_start: date
    period_end: date
    total_new_patients: int
    source_breakdown: Dict[str, int]
    source_percentages: Dict[str, float]
    top_source: str
    referral_patients: List[Dict]
    growth_rate: float  # compared to previous period
    cost_per_acquisition: Dict[str, float]


@dataclass
class ReferralNetwork:
    """Referral network analysis."""
    top_referrers: List[Dict]  # patient_id, name, referral_count
    total_referrals: int
    referral_conversion_rate: float
    average_referrals_per_referrer: float


class PatientAcquisition:
    """Track and analyze patient acquisition."""

    def __init__(self, db_service):
        """Initialize acquisition tracker."""
        self.db = db_service

    def track_new_patient(
        self,
        patient_id: int,
        source: AcquisitionSource,
        referrer_id: Optional[int] = None,
        acquisition_date: date = None,
        campaign: Optional[str] = None
    ) -> bool:
        """
        Track a new patient acquisition.

        Args:
            patient_id: ID of the new patient
            source: How they found the clinic
            referrer_id: ID of referring patient (if referral)
            acquisition_date: Date of acquisition (defaults to today)
            campaign: Marketing campaign if applicable
        """
        if acquisition_date is None:
            acquisition_date = date.today()

        # Store in database
        if self.db:
            return self.db.track_patient_acquisition(
                patient_id=patient_id,
                source=source.value,
                referrer_id=referrer_id,
                acquisition_date=acquisition_date,
                campaign=campaign,
            )
        return True

    def get_acquisition_metrics(
        self,
        period_start: date,
        period_end: date
    ) -> AcquisitionMetrics:
        """Get acquisition metrics for a period."""
        # Get new patients in period
        new_patients = self._get_new_patients(period_start, period_end)

        # Count by source
        source_counts = {}
        for patient in new_patients:
            source = patient.get('acquisition_source', 'other')
            source_counts[source] = source_counts.get(source, 0) + 1

        total = len(new_patients)

        # Calculate percentages
        source_percentages = {
            source: round(count / total * 100, 1) if total > 0 else 0
            for source, count in source_counts.items()
        }

        # Find top source
        top_source = max(source_counts, key=source_counts.get) if source_counts else "none"

        # Get referral details
        referral_patients = [p for p in new_patients if p.get('acquisition_source') == 'referral']

        # Calculate growth rate vs previous period
        period_length = (period_end - period_start).days
        prev_start = period_start - timedelta(days=period_length)
        prev_end = period_start - timedelta(days=1)
        prev_patients = self._get_new_patients(prev_start, prev_end)
        prev_count = len(prev_patients)

        growth_rate = ((total - prev_count) / prev_count * 100) if prev_count > 0 else 100

        # Get cost per acquisition (if marketing spend is tracked)
        cost_per_acquisition = self._calculate_acquisition_costs(period_start, period_end, source_counts)

        return AcquisitionMetrics(
            period_start=period_start,
            period_end=period_end,
            total_new_patients=total,
            source_breakdown=source_counts,
            source_percentages=source_percentages,
            top_source=top_source,
            referral_patients=referral_patients,
            growth_rate=round(growth_rate, 1),
            cost_per_acquisition=cost_per_acquisition,
        )

    def get_referral_network(self, period_days: int = 90) -> ReferralNetwork:
        """Analyze referral network."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        referrals = self._get_referrals(start_date, end_date)

        # Count referrals by referrer
        referrer_counts = {}
        for ref in referrals:
            referrer_id = ref.get('referrer_id')
            if referrer_id:
                if referrer_id not in referrer_counts:
                    referrer_counts[referrer_id] = {
                        'patient_id': referrer_id,
                        'name': ref.get('referrer_name', 'Unknown'),
                        'referral_count': 0,
                    }
                referrer_counts[referrer_id]['referral_count'] += 1

        # Sort by count
        top_referrers = sorted(
            referrer_counts.values(),
            key=lambda x: x['referral_count'],
            reverse=True
        )[:10]

        total_referrals = len(referrals)
        unique_referrers = len(referrer_counts)

        return ReferralNetwork(
            top_referrers=top_referrers,
            total_referrals=total_referrals,
            referral_conversion_rate=100.0,  # All referrals counted as converted
            average_referrals_per_referrer=(
                total_referrals / unique_referrers if unique_referrers > 0 else 0
            ),
        )

    def get_source_performance(
        self,
        source: AcquisitionSource,
        period_days: int = 90
    ) -> Dict:
        """Get detailed performance for a specific source."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        patients = self._get_patients_by_source(source.value, start_date, end_date)

        # Calculate retention and value metrics
        total_patients = len(patients)
        returning_patients = sum(1 for p in patients if p.get('visit_count', 0) > 1)
        total_revenue = sum(p.get('total_revenue', 0) for p in patients)

        return {
            "source": source.value,
            "total_patients": total_patients,
            "returning_patients": returning_patients,
            "retention_rate": round(returning_patients / total_patients * 100, 1) if total_patients > 0 else 0,
            "total_revenue": total_revenue,
            "average_patient_value": round(total_revenue / total_patients, 2) if total_patients > 0 else 0,
            "trend": self._calculate_source_trend(source.value, start_date, end_date),
        }

    def send_thank_you_to_referrer(self, referrer_id: int, new_patient_name: str) -> bool:
        """Send thank you message to referring patient."""
        # This would integrate with WhatsApp service
        # For now, just log the action
        return True

    def get_new_patients_by_month(self, months: int = 12) -> List[Tuple[str, int]]:
        """Get new patients grouped by month."""
        return self.db.get_new_patients_by_month(months) if self.db else []

    def get_growth_rate(self) -> float:
        """Calculate patient growth rate (this month vs last month)."""
        if not self.db:
            return 0.0

        # Get this month's count
        this_month = self.db.get_patients_this_month()

        # Get last month's count
        today = date.today()
        if today.month > 1:
            last_month_year = today.year
            last_month_month = today.month - 1
        else:
            last_month_year = today.year - 1
            last_month_month = 12

        last_month_start = date(last_month_year, last_month_month, 1)
        # Get last day of last month
        if last_month_month == 12:
            last_month_end = date(last_month_year, 12, 31)
        else:
            last_month_end = date(last_month_year, last_month_month + 1, 1) - timedelta(days=1)

        # Count patients created in last month
        all_patients = self.db.get_all_patients()
        last_month = sum(1 for p in all_patients
                        if p.created_at and
                        last_month_start <= p.created_at.date() <= last_month_end)

        if last_month == 0:
            return 100.0 if this_month > 0 else 0.0

        return round(((this_month - last_month) / last_month) * 100, 1)

    def _get_new_patients(self, start: date, end: date) -> List[Dict]:
        """Get new patients in date range."""
        if not self.db:
            return []

        # Get all patients and filter by created_at date
        all_patients = self.db.get_all_patients()
        return [
            {
                'id': p.id,
                'name': p.name,
                'phone': p.phone,
                'created_at': p.created_at,
                'acquisition_source': 'walk_in',  # Default, as we don't track this yet
            }
            for p in all_patients
            if p.created_at and start <= p.created_at.date() <= end
        ]

    def _get_referrals(self, start: date, end: date) -> List[Dict]:
        """Get referral records in date range."""
        # Referral tracking not yet implemented
        # For now, return empty list
        return []

    def _get_patients_by_source(self, source: str, start: date, end: date) -> List[Dict]:
        """Get patients acquired from a specific source."""
        # Source tracking not yet implemented
        # Return all new patients for now
        patients = self._get_new_patients(start, end)

        # Get visit counts for each patient
        if self.db:
            for patient in patients:
                visits = self.db.get_patient_visits(patient['id'])
                patient['visit_count'] = len(visits)
                patient['total_revenue'] = 0  # Revenue tracking not yet implemented

        return patients

    def _calculate_acquisition_costs(
        self,
        start: date,
        end: date,
        source_counts: Dict[str, int]
    ) -> Dict[str, float]:
        """Calculate cost per acquisition by source."""
        # This would integrate with marketing spend tracking
        # For now, return placeholder values
        costs = {}
        spend_by_source = {
            "google_maps": 0,  # Free
            "referral": 0,     # Free (but maybe incentivize)
            "social_media": 5000,  # Monthly ad spend
            "website": 2000,   # SEO/maintenance
        }

        for source, count in source_counts.items():
            if count > 0 and source in spend_by_source:
                costs[source] = round(spend_by_source[source] / count, 2)
            else:
                costs[source] = 0

        return costs

    def _calculate_source_trend(self, source: str, start: date, end: date) -> str:
        """Calculate trend for a source."""
        # Compare to previous period
        period_length = (end - start).days
        prev_start = start - timedelta(days=period_length)

        current_patients = len(self._get_patients_by_source(source, start, end))
        prev_patients = len(self._get_patients_by_source(source, prev_start, start))

        if current_patients > prev_patients * 1.1:
            return "increasing"
        elif current_patients < prev_patients * 0.9:
            return "decreasing"
        return "stable"
