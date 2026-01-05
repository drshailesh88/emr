"""
NPS (Net Promoter Score) tracking service for DocAssist EMR.
Manages patient satisfaction surveys and tracks loyalty metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
import sqlite3
import logging

logger = logging.getLogger(__name__)


class NPSCategory(Enum):
    """NPS score category"""
    PROMOTER = "promoter"      # 9-10
    PASSIVE = "passive"        # 7-8
    DETRACTOR = "detractor"    # 0-6


class SurveyStatus(Enum):
    """Survey status"""
    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class Survey:
    """NPS survey"""
    id: Optional[int] = None
    patient_id: int = 0
    visit_id: Optional[int] = None
    status: SurveyStatus = SurveyStatus.PENDING
    created_date: datetime = field(default_factory=datetime.now)
    sent_date: Optional[datetime] = None
    viewed_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    expiry_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    message_id: Optional[str] = None  # WhatsApp message ID
    survey_link: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'visit_id': self.visit_id,
            'status': self.status.value,
            'created_date': self.created_date.isoformat(),
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'viewed_date': self.viewed_date.isoformat() if self.viewed_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'expiry_date': self.expiry_date.isoformat(),
            'message_id': self.message_id,
            'survey_link': self.survey_link
        }


@dataclass
class NPSResponse:
    """Patient's NPS response"""
    id: Optional[int] = None
    survey_id: int = 0
    patient_id: int = 0
    score: int = 0  # 0-10
    category: NPSCategory = NPSCategory.PASSIVE
    feedback: Optional[str] = None
    response_date: datetime = field(default_factory=datetime.now)
    follow_up_completed: bool = False
    follow_up_notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'patient_id': self.patient_id,
            'score': self.score,
            'category': self.category.value,
            'feedback': self.feedback,
            'response_date': self.response_date.isoformat(),
            'follow_up_completed': self.follow_up_completed,
            'follow_up_notes': self.follow_up_notes
        }


@dataclass
class NPSScore:
    """NPS score for a period"""
    period_start: datetime
    period_end: datetime
    score: float = 0.0  # NPS = %Promoters - %Detractors
    promoters: int = 0
    passives: int = 0
    detractors: int = 0
    total_responses: int = 0
    trend: float = 0.0  # Change from previous period
    response_rate: float = 0.0  # % of surveys completed

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'score': round(self.score, 1),
            'promoters': self.promoters,
            'passives': self.passives,
            'detractors': self.detractors,
            'total_responses': self.total_responses,
            'trend': round(self.trend, 1),
            'response_rate': round(self.response_rate, 2)
        }


@dataclass
class DetractorAlert:
    """Alert for detractor response"""
    id: int
    patient_id: int
    patient_name: str
    score: int
    feedback: Optional[str]
    response_date: datetime
    follow_up_completed: bool
    patient_phone: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'score': self.score,
            'feedback': self.feedback,
            'response_date': self.response_date.isoformat(),
            'follow_up_completed': self.follow_up_completed,
            'patient_phone': self.patient_phone
        }


class NPSTracker:
    """Tracks Net Promoter Score and patient satisfaction"""

    def __init__(self, db_path: str):
        """
        Initialize NPS tracker.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nps_surveys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    visit_id INTEGER,
                    status TEXT NOT NULL,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_date TIMESTAMP,
                    viewed_date TIMESTAMP,
                    completed_date TIMESTAMP,
                    expiry_date TIMESTAMP,
                    message_id TEXT,
                    survey_link TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    FOREIGN KEY (visit_id) REFERENCES visits(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS nps_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    patient_id INTEGER NOT NULL,
                    score INTEGER NOT NULL CHECK(score >= 0 AND score <= 10),
                    category TEXT NOT NULL,
                    feedback TEXT,
                    response_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    follow_up_completed BOOLEAN DEFAULT 0,
                    follow_up_notes TEXT,
                    follow_up_date TIMESTAMP,
                    FOREIGN KEY (survey_id) REFERENCES nps_surveys(id),
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nps_surveys_patient
                ON nps_surveys(patient_id, status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nps_responses_date
                ON nps_responses(response_date DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nps_responses_category
                ON nps_responses(category)
            """)

            conn.commit()

    def send_nps_survey(
        self,
        patient_id: int,
        visit_id: Optional[int] = None,
        survey_link: Optional[str] = None
    ) -> Optional[Survey]:
        """
        Send NPS survey to patient.

        Args:
            patient_id: Patient ID
            visit_id: Recent visit ID (optional)
            survey_link: Custom survey link (optional)

        Returns:
            Survey object or None
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if survey already sent recently (within 30 days)
            cursor = conn.execute("""
                SELECT id FROM nps_surveys
                WHERE patient_id = ?
                    AND created_date > ?
                    AND status != ?
            """, (
                patient_id,
                datetime.now() - timedelta(days=30),
                SurveyStatus.EXPIRED.value
            ))

            if cursor.fetchone():
                logger.warning(f"NPS survey already sent to patient {patient_id} recently")
                return None

            # Create survey
            survey = Survey(
                patient_id=patient_id,
                visit_id=visit_id,
                status=SurveyStatus.PENDING,
                survey_link=survey_link
            )

            cursor = conn.execute("""
                INSERT INTO nps_surveys
                (patient_id, visit_id, status, expiry_date, survey_link)
                VALUES (?, ?, ?, ?, ?)
            """, (
                survey.patient_id,
                survey.visit_id,
                survey.status.value,
                survey.expiry_date,
                survey.survey_link
            ))

            conn.commit()
            survey.id = cursor.lastrowid

            logger.info(f"NPS survey created for patient {patient_id}")
            return survey

    def mark_survey_sent(self, survey_id: int, message_id: str) -> bool:
        """
        Mark survey as sent.

        Args:
            survey_id: Survey ID
            message_id: WhatsApp message ID

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE nps_surveys
                SET status = ?, sent_date = ?, message_id = ?
                WHERE id = ?
            """, (SurveyStatus.SENT.value, datetime.now(), message_id, survey_id))

            conn.commit()
            return True

    def record_response(
        self,
        survey_id: int,
        score: int,
        feedback: Optional[str] = None
    ) -> Optional[NPSResponse]:
        """
        Record patient's NPS response.

        Args:
            survey_id: Survey ID
            score: NPS score (0-10)
            feedback: Optional feedback text

        Returns:
            NPSResponse object or None
        """
        if not (0 <= score <= 10):
            logger.error(f"Invalid NPS score: {score}")
            return None

        # Categorize score
        if score >= 9:
            category = NPSCategory.PROMOTER
        elif score >= 7:
            category = NPSCategory.PASSIVE
        else:
            category = NPSCategory.DETRACTOR

        with sqlite3.connect(self.db_path) as conn:
            # Get survey details
            cursor = conn.execute("""
                SELECT patient_id FROM nps_surveys WHERE id = ?
            """, (survey_id,))

            survey_row = cursor.fetchone()
            if not survey_row:
                logger.error(f"Survey {survey_id} not found")
                return None

            patient_id = survey_row[0]

            # Check if response already exists
            cursor = conn.execute("""
                SELECT id FROM nps_responses WHERE survey_id = ?
            """, (survey_id,))

            if cursor.fetchone():
                logger.warning(f"Response already recorded for survey {survey_id}")
                return None

            # Create response
            response = NPSResponse(
                survey_id=survey_id,
                patient_id=patient_id,
                score=score,
                category=category,
                feedback=feedback
            )

            cursor = conn.execute("""
                INSERT INTO nps_responses
                (survey_id, patient_id, score, category, feedback)
                VALUES (?, ?, ?, ?, ?)
            """, (
                response.survey_id,
                response.patient_id,
                response.score,
                response.category.value,
                response.feedback
            ))

            response.id = cursor.lastrowid

            # Update survey status
            conn.execute("""
                UPDATE nps_surveys
                SET status = ?, completed_date = ?
                WHERE id = ?
            """, (SurveyStatus.COMPLETED.value, datetime.now(), survey_id))

            conn.commit()

            logger.info(f"NPS response recorded: patient {patient_id}, score {score}")
            return response

    def calculate_nps(self, period_days: int = 30) -> NPSScore:
        """
        Calculate NPS for a period.

        Args:
            period_days: Period to analyze

        Returns:
            NPSScore object
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Previous period for trend
        prev_start = start_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Count responses by category
            cursor = conn.execute("""
                SELECT category, COUNT(*) FROM nps_responses
                WHERE response_date BETWEEN ? AND ?
                GROUP BY category
            """, (start_date, end_date))

            counts = {row[0]: row[1] for row in cursor.fetchall()}

            promoters = counts.get(NPSCategory.PROMOTER.value, 0)
            passives = counts.get(NPSCategory.PASSIVE.value, 0)
            detractors = counts.get(NPSCategory.DETRACTOR.value, 0)
            total = promoters + passives + detractors

            # Calculate NPS
            if total > 0:
                promoter_pct = (promoters / total) * 100
                detractor_pct = (detractors / total) * 100
                nps = promoter_pct - detractor_pct
            else:
                nps = 0.0

            # Previous period NPS for trend
            cursor = conn.execute("""
                SELECT category, COUNT(*) FROM nps_responses
                WHERE response_date BETWEEN ? AND ?
                GROUP BY category
            """, (prev_start, start_date))

            prev_counts = {row[0]: row[1] for row in cursor.fetchall()}

            prev_promoters = prev_counts.get(NPSCategory.PROMOTER.value, 0)
            prev_passives = prev_counts.get(NPSCategory.PASSIVE.value, 0)
            prev_detractors = prev_counts.get(NPSCategory.DETRACTOR.value, 0)
            prev_total = prev_promoters + prev_passives + prev_detractors

            if prev_total > 0:
                prev_nps = ((prev_promoters / prev_total) * 100) - ((prev_detractors / prev_total) * 100)
            else:
                prev_nps = 0.0

            trend = nps - prev_nps

            # Response rate
            cursor = conn.execute("""
                SELECT COUNT(*) FROM nps_surveys
                WHERE created_date BETWEEN ? AND ?
            """, (start_date, end_date))

            total_surveys = cursor.fetchone()[0] or 0
            response_rate = (total / total_surveys * 100) if total_surveys > 0 else 0.0

            score = NPSScore(
                period_start=start_date,
                period_end=end_date,
                score=nps,
                promoters=promoters,
                passives=passives,
                detractors=detractors,
                total_responses=total,
                trend=trend,
                response_rate=response_rate
            )

            return score

    def get_detractor_alerts(self, days: int = 7) -> List[DetractorAlert]:
        """
        Get recent detractor responses that need follow-up.

        Args:
            days: Number of days to look back

        Returns:
            List of DetractorAlert objects
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    r.id,
                    r.patient_id,
                    p.name,
                    r.score,
                    r.feedback,
                    r.response_date,
                    r.follow_up_completed,
                    p.phone
                FROM nps_responses r
                INNER JOIN patients p ON r.patient_id = p.id
                WHERE r.category = ?
                    AND r.response_date >= ?
                ORDER BY r.response_date DESC
            """, (NPSCategory.DETRACTOR.value, cutoff_date))

            alerts = []
            for row in cursor.fetchall():
                alert = DetractorAlert(
                    id=row[0],
                    patient_id=row[1],
                    patient_name=row[2],
                    score=row[3],
                    feedback=row[4],
                    response_date=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                    follow_up_completed=bool(row[6]),
                    patient_phone=row[7]
                )
                alerts.append(alert)

            return alerts

    def mark_detractor_follow_up(
        self,
        response_id: int,
        notes: Optional[str] = None
    ) -> bool:
        """
        Mark detractor follow-up as completed.

        Args:
            response_id: Response ID
            notes: Follow-up notes

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE nps_responses
                SET follow_up_completed = 1,
                    follow_up_notes = ?,
                    follow_up_date = ?
                WHERE id = ?
            """, (notes, datetime.now(), response_id))

            conn.commit()

            logger.info(f"Detractor follow-up completed for response {response_id}")
            return True

    def get_nps_trend(self, months: int = 6) -> List[Tuple[str, float]]:
        """
        Get monthly NPS trend.

        Args:
            months: Number of months to analyze

        Returns:
            List of (month, nps_score) tuples
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    strftime('%Y-%m', response_date) as month,
                    category,
                    COUNT(*) as count
                FROM nps_responses
                WHERE response_date BETWEEN ? AND ?
                GROUP BY month, category
                ORDER BY month
            """, (start_date, end_date))

            # Group by month
            by_month = {}
            for row in cursor.fetchall():
                month = row[0]
                category = row[1]
                count = row[2]

                if month not in by_month:
                    by_month[month] = {'promoter': 0, 'passive': 0, 'detractor': 0}

                by_month[month][category] = count

            # Calculate NPS for each month
            trend = []
            for month, counts in sorted(by_month.items()):
                promoters = counts['promoter']
                detractors = counts['detractor']
                total = promoters + counts['passive'] + detractors

                if total > 0:
                    nps = ((promoters / total) * 100) - ((detractors / total) * 100)
                else:
                    nps = 0.0

                trend.append((month, nps))

            return trend

    def get_feedback_themes(self, period_days: int = 30) -> Dict[str, List[str]]:
        """
        Get common themes from feedback.

        Args:
            period_days: Period to analyze

        Returns:
            Dictionary of {category: [feedback_samples]}
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT category, feedback FROM nps_responses
                WHERE response_date BETWEEN ? AND ?
                    AND feedback IS NOT NULL
                ORDER BY response_date DESC
            """, (start_date, end_date))

            themes = {
                'promoter': [],
                'passive': [],
                'detractor': []
            }

            for row in cursor.fetchall():
                category = row[0]
                feedback = row[1]

                if category in themes:
                    themes[category].append(feedback)

            return themes

    def get_pending_surveys(self) -> List[Survey]:
        """
        Get pending surveys that need to be sent.

        Returns:
            List of Survey objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    id, patient_id, visit_id, status, created_date,
                    sent_date, viewed_date, completed_date, expiry_date,
                    message_id, survey_link
                FROM nps_surveys
                WHERE status = ?
                ORDER BY created_date
            """, (SurveyStatus.PENDING.value,))

            surveys = []
            for row in cursor.fetchall():
                survey = Survey(
                    id=row[0],
                    patient_id=row[1],
                    visit_id=row[2],
                    status=SurveyStatus(row[3]),
                    created_date=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                    sent_date=datetime.fromisoformat(row[5]) if row[5] else None,
                    viewed_date=datetime.fromisoformat(row[6]) if row[6] else None,
                    completed_date=datetime.fromisoformat(row[7]) if row[7] else None,
                    expiry_date=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    message_id=row[9],
                    survey_link=row[10]
                )
                surveys.append(survey)

            return surveys

    def expire_old_surveys(self) -> int:
        """
        Mark expired surveys as expired.

        Returns:
            Number of surveys expired
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE nps_surveys
                SET status = ?
                WHERE status IN (?, ?)
                    AND expiry_date < ?
            """, (
                SurveyStatus.EXPIRED.value,
                SurveyStatus.PENDING.value,
                SurveyStatus.SENT.value,
                datetime.now()
            ))

            conn.commit()
            count = cursor.rowcount

            logger.info(f"Expired {count} old surveys")
            return count
