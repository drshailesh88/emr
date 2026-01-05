"""
Growth recommendations service for DocAssist EMR.
Analyzes practice data and provides actionable growth insights.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Type of recommendation"""
    REPUTATION = "reputation"          # Review/rating improvements
    RETENTION = "retention"            # Patient retention
    REFERRAL = "referral"              # Referral growth
    OPERATIONS = "operations"          # Operational efficiency
    REVENUE = "revenue"                # Revenue optimization
    PATIENT_CARE = "patient_care"      # Care quality


class Priority(Enum):
    """Recommendation priority"""
    CRITICAL = "critical"    # Immediate action needed
    HIGH = "high"            # Act within a week
    MEDIUM = "medium"        # Act within a month
    LOW = "low"              # Nice to have


class ImpactLevel(Enum):
    """Expected impact"""
    HIGH = "high"       # Significant impact on practice
    MEDIUM = "medium"   # Moderate impact
    LOW = "low"         # Small but positive impact


@dataclass
class Recommendation:
    """Growth recommendation"""
    type: RecommendationType
    title: str
    description: str
    impact: ImpactLevel
    action: str  # What to do
    priority: Priority
    metric_value: Optional[float] = None  # Current metric value
    metric_name: Optional[str] = None     # e.g., "Rating", "NPS"
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'type': self.type.value,
            'title': self.title,
            'description': self.description,
            'impact': self.impact.value,
            'action': self.action,
            'priority': self.priority.value,
            'metric_value': self.metric_value,
            'metric_name': self.metric_name,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class Benchmark:
    """Practice benchmark comparison"""
    metric_name: str
    your_value: float
    benchmark_value: float
    percentile: int  # Your percentile (0-100)
    status: str      # 'above', 'at', 'below'
    specialty: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'metric_name': self.metric_name,
            'your_value': round(self.your_value, 2),
            'benchmark_value': round(self.benchmark_value, 2),
            'percentile': self.percentile,
            'status': self.status,
            'specialty': self.specialty
        }


class GrowthRecommendations:
    """Analyzes practice and generates growth recommendations"""

    def __init__(self, db_path: str):
        """
        Initialize growth recommendations.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

        # Benchmark data (anonymized averages from similar clinics)
        # In production, fetch from central analytics server
        self.benchmarks = {
            'avg_rating': 4.5,
            'nps_score': 45.0,
            'review_count_per_month': 10,
            'referral_rate': 25.0,  # % of new patients from referrals
            'retention_rate': 70.0,  # % of patients with 2+ visits
            'avg_wait_time': 20,     # minutes
            'follow_up_compliance': 65.0  # % who come for follow-up
        }

    def analyze_practice(self, period_days: int = 30) -> List[Recommendation]:
        """
        Analyze practice and generate recommendations.

        Args:
            period_days: Period to analyze

        Returns:
            List of Recommendation objects
        """
        recommendations = []

        # Analyze reviews and ratings
        recommendations.extend(self._analyze_reviews(period_days))

        # Analyze referrals
        recommendations.extend(self._analyze_referrals(period_days))

        # Analyze patient retention
        recommendations.extend(self._analyze_retention(period_days))

        # Analyze operations
        recommendations.extend(self._analyze_operations(period_days))

        # Analyze follow-up compliance
        recommendations.extend(self._analyze_follow_ups(period_days))

        # Sort by priority
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }

        recommendations.sort(key=lambda r: priority_order[r.priority])

        return recommendations

    def _analyze_reviews(self, period_days: int) -> List[Recommendation]:
        """Analyze review metrics"""
        recommendations = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Previous period for comparison
        prev_start = start_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Current period average rating
            cursor = conn.execute("""
                SELECT AVG(rating), COUNT(*) FROM reviews
                WHERE review_date BETWEEN ? AND ?
            """, (start_date, end_date))

            row = cursor.fetchone()
            current_rating = row[0] or 0.0
            current_count = row[1] or 0

            # Previous period rating
            cursor = conn.execute("""
                SELECT AVG(rating) FROM reviews
                WHERE review_date BETWEEN ? AND ?
            """, (prev_start, start_date))

            prev_rating = cursor.fetchone()[0] or 0.0

            # Rating drop alert
            if prev_rating > 0 and (prev_rating - current_rating) > 0.3:
                recommendations.append(Recommendation(
                    type=RecommendationType.REPUTATION,
                    title="Rating Declined",
                    description=f"Your rating dropped {prev_rating - current_rating:.1f} stars from {prev_rating:.1f} to {current_rating:.1f}",
                    impact=ImpactLevel.HIGH,
                    action="Check recent negative reviews and address concerns promptly",
                    priority=Priority.CRITICAL,
                    metric_value=current_rating,
                    metric_name="Average Rating"
                ))

            # Low review count
            if current_count < self.benchmarks['review_count_per_month']:
                recommendations.append(Recommendation(
                    type=RecommendationType.REPUTATION,
                    title="Low Review Volume",
                    description=f"Only {current_count} reviews this month (benchmark: {self.benchmarks['review_count_per_month']})",
                    impact=ImpactLevel.MEDIUM,
                    action="Enable automatic review requests after positive visits",
                    priority=Priority.MEDIUM,
                    metric_value=current_count,
                    metric_name="Monthly Reviews"
                ))

            # Unanswered reviews
            cursor = conn.execute("""
                SELECT COUNT(*) FROM reviews
                WHERE review_date BETWEEN ? AND ?
                    AND response IS NULL
            """, (start_date, end_date))

            unanswered = cursor.fetchone()[0]

            if unanswered > 0:
                recommendations.append(Recommendation(
                    type=RecommendationType.REPUTATION,
                    title="Unanswered Reviews",
                    description=f"{unanswered} reviews without response",
                    impact=ImpactLevel.MEDIUM,
                    action="Respond to all reviews to show engagement and care",
                    priority=Priority.HIGH,
                    metric_value=unanswered,
                    metric_name="Unanswered Reviews"
                ))

        return recommendations

    def _analyze_referrals(self, period_days: int) -> List[Recommendation]:
        """Analyze referral metrics"""
        recommendations = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Total new patients
            cursor = conn.execute("""
                SELECT COUNT(*) FROM patients
                WHERE created_at BETWEEN ? AND ?
            """, (start_date, end_date))

            total_new = cursor.fetchone()[0] or 0

            # Referral patients
            cursor = conn.execute("""
                SELECT COUNT(*) FROM referrals
                WHERE referral_date BETWEEN ? AND ?
                    AND referral_type IN ('patient_referral', 'doctor_referral')
            """, (start_date, end_date))

            referral_new = cursor.fetchone()[0] or 0

            # Referral rate
            referral_rate = (referral_new / total_new * 100) if total_new > 0 else 0.0

            # High referral rate (good!)
            if referral_rate > self.benchmarks['referral_rate']:
                recommendations.append(Recommendation(
                    type=RecommendationType.REFERRAL,
                    title="Strong Referral Network",
                    description=f"{referral_rate:.0f}% of new patients from referrals (above {self.benchmarks['referral_rate']:.0f}% benchmark)",
                    impact=ImpactLevel.HIGH,
                    action="Consider a referral rewards program to sustain growth",
                    priority=Priority.MEDIUM,
                    metric_value=referral_rate,
                    metric_name="Referral Rate"
                ))
            elif referral_rate < self.benchmarks['referral_rate'] * 0.7:
                recommendations.append(Recommendation(
                    type=RecommendationType.REFERRAL,
                    title="Low Referral Rate",
                    description=f"Only {referral_rate:.0f}% from referrals (benchmark: {self.benchmarks['referral_rate']:.0f}%)",
                    impact=ImpactLevel.HIGH,
                    action="Ask satisfied patients to refer friends and family",
                    priority=Priority.HIGH,
                    metric_value=referral_rate,
                    metric_name="Referral Rate"
                ))

            # Unthanked referrers
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT r.referrer_id)
                FROM referrals r
                LEFT JOIN referral_thank_you rt
                    ON r.referrer_id = rt.referrer_id
                    AND r.patient_id = rt.referred_patient_id
                WHERE r.referral_date BETWEEN ? AND ?
                    AND r.referrer_id IS NOT NULL
                    AND rt.id IS NULL
            """, (start_date, end_date))

            unthanked = cursor.fetchone()[0] or 0

            if unthanked > 0:
                recommendations.append(Recommendation(
                    type=RecommendationType.REFERRAL,
                    title="Unthanked Referrers",
                    description=f"{unthanked} referrers not thanked yet",
                    impact=ImpactLevel.MEDIUM,
                    action="Send thank you messages to maintain goodwill",
                    priority=Priority.MEDIUM,
                    metric_value=unthanked,
                    metric_name="Unthanked Referrers"
                ))

        return recommendations

    def _analyze_retention(self, period_days: int) -> List[Recommendation]:
        """Analyze patient retention"""
        recommendations = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Patients with only 1 visit
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT p.id)
                FROM patients p
                INNER JOIN visits v ON p.id = v.patient_id
                WHERE p.created_at BETWEEN ? AND ?
                GROUP BY p.id
                HAVING COUNT(v.id) = 1
            """, (start_date, end_date))

            one_visit = len(cursor.fetchall())

            # Total patients
            cursor = conn.execute("""
                SELECT COUNT(*) FROM patients
                WHERE created_at BETWEEN ? AND ?
            """, (start_date, end_date))

            total_patients = cursor.fetchone()[0] or 0

            # Retention rate
            retention_rate = ((total_patients - one_visit) / total_patients * 100) if total_patients > 0 else 0.0

            if retention_rate < self.benchmarks['retention_rate']:
                recommendations.append(Recommendation(
                    type=RecommendationType.RETENTION,
                    title="Low Patient Retention",
                    description=f"Only {retention_rate:.0f}% return for follow-up (benchmark: {self.benchmarks['retention_rate']:.0f}%)",
                    impact=ImpactLevel.HIGH,
                    action="Enable automated follow-up reminders via WhatsApp",
                    priority=Priority.HIGH,
                    metric_value=retention_rate,
                    metric_name="Retention Rate"
                ))

        return recommendations

    def _analyze_operations(self, period_days: int) -> List[Recommendation]:
        """Analyze operational efficiency"""
        recommendations = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Check for peak hours
            cursor = conn.execute("""
                SELECT strftime('%H', visit_date) as hour, COUNT(*) as count
                FROM visits
                WHERE visit_date BETWEEN ? AND ?
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 3
            """, (start_date, end_date))

            peak_hours = cursor.fetchall()

            if peak_hours:
                peak_hour = int(peak_hours[0][0])
                peak_count = peak_hours[0][1]

                # Format hour
                hour_display = f"{peak_hour}:00-{peak_hour+1}:00"

                recommendations.append(Recommendation(
                    type=RecommendationType.OPERATIONS,
                    title="Peak Hour Identified",
                    description=f"Most visits during {hour_display} ({peak_count} visits)",
                    impact=ImpactLevel.MEDIUM,
                    action="Consider extending hours or adding staff during peak times",
                    priority=Priority.LOW,
                    metric_value=peak_count,
                    metric_name="Peak Hour Visits"
                ))

            # Check for negative reviews mentioning wait time
            cursor = conn.execute("""
                SELECT COUNT(*) FROM reviews
                WHERE review_date BETWEEN ? AND ?
                    AND (text LIKE '%wait%' OR text LIKE '%delay%')
                    AND rating < 4
            """, (start_date, end_date))

            wait_complaints = cursor.fetchone()[0] or 0

            if wait_complaints > 2:
                recommendations.append(Recommendation(
                    type=RecommendationType.OPERATIONS,
                    title="Wait Time Complaints",
                    description=f"{wait_complaints} negative reviews mention waiting",
                    impact=ImpactLevel.HIGH,
                    action="Improve appointment scheduling or reduce wait times",
                    priority=Priority.HIGH,
                    metric_value=wait_complaints,
                    metric_name="Wait Complaints"
                ))

        return recommendations

    def _analyze_follow_ups(self, period_days: int) -> List[Recommendation]:
        """Analyze follow-up compliance"""
        recommendations = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Patients overdue for annual checkup
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT p.id)
                FROM patients p
                INNER JOIN visits v ON p.id = v.patient_id
                WHERE v.visit_date < ?
                    AND NOT EXISTS (
                        SELECT 1 FROM visits v2
                        WHERE v2.patient_id = p.id
                            AND v2.visit_date > ?
                    )
            """, (
                datetime.now() - timedelta(days=365),
                datetime.now() - timedelta(days=365)
            ))

            overdue_checkup = cursor.fetchone()[0] or 0

            if overdue_checkup > 10:
                recommendations.append(Recommendation(
                    type=RecommendationType.PATIENT_CARE,
                    title="Overdue Annual Checkups",
                    description=f"{overdue_checkup} patients overdue for annual checkup",
                    impact=ImpactLevel.MEDIUM,
                    action="Send automated checkup reminders via WhatsApp",
                    priority=Priority.MEDIUM,
                    metric_value=overdue_checkup,
                    metric_name="Overdue Checkups"
                ))

            # Missed follow-up appointments
            cursor = conn.execute("""
                SELECT COUNT(*) FROM visits
                WHERE visit_date BETWEEN ? AND ?
                    AND prescription_json LIKE '%follow_up%'
                    AND prescription_json NOT LIKE '%completed%'
            """, (start_date, end_date))

            missed_followups = cursor.fetchone()[0] or 0

            if missed_followups > 5:
                recommendations.append(Recommendation(
                    type=RecommendationType.PATIENT_CARE,
                    title="Low Follow-up Compliance",
                    description=f"{missed_followups} patients didn't return for follow-up",
                    impact=ImpactLevel.MEDIUM,
                    action="Enable follow-up reminders and tracking",
                    priority=Priority.MEDIUM,
                    metric_value=missed_followups,
                    metric_name="Missed Follow-ups"
                ))

        return recommendations

    def get_competitor_benchmark(self, specialty: Optional[str] = None) -> List[Benchmark]:
        """
        Compare practice to similar clinics.

        Args:
            specialty: Medical specialty (optional)

        Returns:
            List of Benchmark objects
        """
        benchmarks = []

        with sqlite3.connect(self.db_path) as conn:
            # Average rating
            cursor = conn.execute("""
                SELECT AVG(rating) FROM reviews
                WHERE review_date > ?
            """, (datetime.now() - timedelta(days=90),))

            your_rating = cursor.fetchone()[0] or 0.0

            benchmarks.append(Benchmark(
                metric_name="Average Rating",
                your_value=your_rating,
                benchmark_value=self.benchmarks['avg_rating'],
                percentile=self._calculate_percentile(your_rating, self.benchmarks['avg_rating']),
                status='above' if your_rating > self.benchmarks['avg_rating'] else 'below',
                specialty=specialty
            ))

            # NPS Score (if available)
            cursor = conn.execute("""
                SELECT
                    SUM(CASE WHEN category = 'promoter' THEN 1 ELSE 0 END) as promoters,
                    SUM(CASE WHEN category = 'detractor' THEN 1 ELSE 0 END) as detractors,
                    COUNT(*) as total
                FROM nps_responses
                WHERE response_date > ?
            """, (datetime.now() - timedelta(days=90),))

            row = cursor.fetchone()
            if row and row[2] > 0:
                promoters = row[0] or 0
                detractors = row[1] or 0
                total = row[2]

                your_nps = ((promoters / total) * 100) - ((detractors / total) * 100)

                benchmarks.append(Benchmark(
                    metric_name="NPS Score",
                    your_value=your_nps,
                    benchmark_value=self.benchmarks['nps_score'],
                    percentile=self._calculate_percentile(your_nps, self.benchmarks['nps_score']),
                    status='above' if your_nps > self.benchmarks['nps_score'] else 'below',
                    specialty=specialty
                ))

            # Referral rate
            cursor = conn.execute("""
                SELECT COUNT(*) FROM patients
                WHERE created_at > ?
            """, (datetime.now() - timedelta(days=90),))

            total_new = cursor.fetchone()[0] or 0

            cursor = conn.execute("""
                SELECT COUNT(*) FROM referrals
                WHERE referral_date > ?
                    AND referral_type IN ('patient_referral', 'doctor_referral')
            """, (datetime.now() - timedelta(days=90),))

            referral_new = cursor.fetchone()[0] or 0

            your_referral_rate = (referral_new / total_new * 100) if total_new > 0 else 0.0

            benchmarks.append(Benchmark(
                metric_name="Referral Rate",
                your_value=your_referral_rate,
                benchmark_value=self.benchmarks['referral_rate'],
                percentile=self._calculate_percentile(your_referral_rate, self.benchmarks['referral_rate']),
                status='above' if your_referral_rate > self.benchmarks['referral_rate'] else 'below',
                specialty=specialty
            ))

        return benchmarks

    def _calculate_percentile(self, your_value: float, benchmark: float) -> int:
        """
        Calculate approximate percentile.

        Args:
            your_value: Your metric value
            benchmark: Benchmark (50th percentile)

        Returns:
            Percentile (0-100)
        """
        # Simple linear approximation
        # In production, use actual distribution data

        if your_value >= benchmark:
            # Above benchmark
            # Map [benchmark, benchmark*1.2] to [50, 90]
            if your_value >= benchmark * 1.2:
                return 90
            else:
                ratio = (your_value - benchmark) / (benchmark * 0.2)
                return int(50 + (ratio * 40))
        else:
            # Below benchmark
            # Map [benchmark*0.8, benchmark] to [10, 50]
            if your_value <= benchmark * 0.8:
                return 10
            else:
                ratio = (your_value - benchmark * 0.8) / (benchmark * 0.2)
                return int(10 + (ratio * 40))

    def get_quick_wins(self, period_days: int = 30) -> List[Recommendation]:
        """
        Get recommendations that are easy to implement and high impact.

        Args:
            period_days: Period to analyze

        Returns:
            List of quick win recommendations
        """
        all_recommendations = self.analyze_practice(period_days)

        # Filter for high impact, high/medium priority
        quick_wins = [
            rec for rec in all_recommendations
            if rec.impact in [ImpactLevel.HIGH, ImpactLevel.MEDIUM]
            and rec.priority in [Priority.HIGH, Priority.CRITICAL]
        ]

        return quick_wins[:5]  # Top 5 quick wins
