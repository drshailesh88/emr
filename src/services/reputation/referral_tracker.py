"""
Referral tracking service for DocAssist EMR.
Tracks patient and doctor referrals, calculates ROI, and manages thank you messages.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
import sqlite3
import logging

logger = logging.getLogger(__name__)


class ReferralType(Enum):
    """Type of referral source"""
    PATIENT_REFERRAL = "patient_referral"  # Referred by existing patient
    DOCTOR_REFERRAL = "doctor_referral"    # Referred by another doctor
    GOOGLE_SEARCH = "google_search"        # Found via Google
    SOCIAL_MEDIA = "social_media"          # Facebook, Instagram
    PRACTO = "practo"                      # Practo platform
    JUSTDIAL = "justdial"                  # JustDial listing
    WALK_IN = "walk_in"                    # Walk-in without referral
    WHATSAPP = "whatsapp"                  # WhatsApp contact
    NEWSPAPER = "newspaper"                # Newspaper ad
    WORD_OF_MOUTH = "word_of_mouth"       # General word of mouth
    OTHER = "other"


@dataclass
class ReferralSource:
    """Patient's referral source"""
    type: ReferralType
    referrer_id: Optional[int] = None  # Patient or doctor ID who referred
    referrer_name: Optional[str] = None
    referrer_type: Optional[str] = None  # 'patient' or 'doctor'
    date: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'type': self.type.value,
            'referrer_id': self.referrer_id,
            'referrer_name': self.referrer_name,
            'referrer_type': self.referrer_type,
            'date': self.date.isoformat(),
            'notes': self.notes
        }


@dataclass
class Referrer:
    """Top referrer details"""
    id: int
    name: str
    type: str  # 'patient' or 'doctor'
    referral_count: int
    successful_conversions: int  # How many became patients
    total_value: float  # Lifetime value of referred patients
    last_referral_date: datetime
    phone: Optional[str] = None
    thank_you_sent: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'referral_count': self.referral_count,
            'successful_conversions': self.successful_conversions,
            'total_value': round(self.total_value, 2),
            'last_referral_date': self.last_referral_date.isoformat(),
            'phone': self.phone,
            'thank_you_sent': self.thank_you_sent
        }


@dataclass
class ReferralStats:
    """Referral statistics for a period"""
    period_start: datetime
    period_end: datetime
    total_referrals: int = 0
    by_source: Dict[str, int] = field(default_factory=dict)  # {type: count}
    conversion_rate: float = 0.0  # % who became patients
    trend: float = 0.0  # Change from previous period
    top_referrers: List[Referrer] = field(default_factory=list)
    avg_value_per_referral: float = 0.0
    referral_revenue: float = 0.0  # Total revenue from referrals

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_referrals': self.total_referrals,
            'by_source': self.by_source,
            'conversion_rate': round(self.conversion_rate, 2),
            'trend': round(self.trend, 2),
            'top_referrers': [r.to_dict() for r in self.top_referrers],
            'avg_value_per_referral': round(self.avg_value_per_referral, 2),
            'referral_revenue': round(self.referral_revenue, 2)
        }


class ReferralTracker:
    """Tracks and analyzes patient referrals"""

    def __init__(self, db_path: str):
        """
        Initialize referral tracker.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    referral_type TEXT NOT NULL,
                    referrer_id INTEGER,  -- ID of referring patient/doctor
                    referrer_type TEXT,   -- 'patient' or 'doctor'
                    referrer_name TEXT,
                    referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    converted_to_patient BOOLEAN DEFAULT 1,  -- Did they become a patient?
                    first_visit_date TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS referral_thank_you (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referrer_type TEXT NOT NULL,
                    referred_patient_id INTEGER NOT NULL,
                    referred_patient_name TEXT,
                    message_sent BOOLEAN DEFAULT 0,
                    sent_date TIMESTAMP,
                    message_id TEXT,  -- WhatsApp message ID
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referred_patient_id) REFERENCES patients(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_referrals_patient
                ON referrals(patient_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_referrals_referrer
                ON referrals(referrer_id, referrer_type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_referrals_date
                ON referrals(referral_date DESC)
            """)

            conn.commit()

    def track_referral(
        self,
        patient_id: int,
        referral_type: ReferralType,
        referrer_id: Optional[int] = None,
        referrer_type: Optional[str] = None,
        referrer_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Track a new referral.

        Args:
            patient_id: ID of the new patient
            referral_type: Type of referral
            referrer_id: ID of referring patient/doctor (if applicable)
            referrer_type: 'patient' or 'doctor'
            referrer_name: Name of referrer
            notes: Additional notes

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if referral already tracked for this patient
            cursor = conn.execute("""
                SELECT id FROM referrals WHERE patient_id = ?
            """, (patient_id,))

            if cursor.fetchone():
                logger.warning(f"Referral already tracked for patient {patient_id}")
                return False

            # Get patient's first visit date
            cursor = conn.execute("""
                SELECT MIN(visit_date) FROM visits WHERE patient_id = ?
            """, (patient_id,))

            first_visit = cursor.fetchone()[0]

            # Insert referral
            conn.execute("""
                INSERT INTO referrals
                (patient_id, referral_type, referrer_id, referrer_type,
                 referrer_name, first_visit_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                referral_type.value,
                referrer_id,
                referrer_type,
                referrer_name,
                first_visit,
                notes
            ))

            conn.commit()

            logger.info(f"Referral tracked for patient {patient_id} from {referral_type.value}")
            return True

    def get_referral_source(self, patient_id: int) -> Optional[ReferralSource]:
        """
        Get how a patient found the clinic.

        Args:
            patient_id: Patient ID

        Returns:
            ReferralSource object or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT referral_type, referrer_id, referrer_name, referrer_type,
                       referral_date, notes
                FROM referrals
                WHERE patient_id = ?
            """, (patient_id,))

            row = cursor.fetchone()
            if not row:
                return None

            source = ReferralSource(
                type=ReferralType(row[0]),
                referrer_id=row[1],
                referrer_name=row[2],
                referrer_type=row[3],
                date=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                notes=row[5]
            )

            return source

    def get_top_referrers(
        self,
        period_days: int = 365,
        limit: int = 10,
        referrer_type: Optional[str] = None
    ) -> List[Referrer]:
        """
        Get top referrers.

        Args:
            period_days: Period to analyze
            limit: Number of top referrers to return
            referrer_type: Filter by 'patient' or 'doctor'

        Returns:
            List of Referrer objects
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Build query based on referrer type filter
            query = """
                SELECT
                    r.referrer_id,
                    r.referrer_name,
                    r.referrer_type,
                    COUNT(*) as referral_count,
                    SUM(CASE WHEN r.converted_to_patient = 1 THEN 1 ELSE 0 END) as conversions,
                    MAX(r.referral_date) as last_referral
                FROM referrals r
                WHERE r.referrer_id IS NOT NULL
                    AND r.referral_date BETWEEN ? AND ?
            """

            params = [start_date, end_date]

            if referrer_type:
                query += " AND r.referrer_type = ?"
                params.append(referrer_type)

            query += """
                GROUP BY r.referrer_id, r.referrer_name, r.referrer_type
                ORDER BY referral_count DESC
                LIMIT ?
            """
            params.append(limit)

            cursor = conn.execute(query, params)

            referrers = []
            for row in cursor.fetchall():
                referrer_id = row[0]
                referrer_name = row[1]
                ref_type = row[2]
                referral_count = row[3]
                conversions = row[4]
                last_referral = datetime.fromisoformat(row[5]) if row[5] else datetime.now()

                # Calculate total value of referred patients
                total_value = self._calculate_referral_value(referrer_id, ref_type)

                # Get phone number
                phone = None
                if ref_type == 'patient':
                    cursor2 = conn.execute("""
                        SELECT phone FROM patients WHERE id = ?
                    """, (referrer_id,))
                    phone_row = cursor2.fetchone()
                    if phone_row:
                        phone = phone_row[0]

                # Check if thank you sent recently
                cursor2 = conn.execute("""
                    SELECT COUNT(*) FROM referral_thank_you
                    WHERE referrer_id = ? AND message_sent = 1
                        AND sent_date > ?
                """, (referrer_id, start_date))

                thank_you_sent = cursor2.fetchone()[0] > 0

                referrer = Referrer(
                    id=referrer_id,
                    name=referrer_name,
                    type=ref_type,
                    referral_count=referral_count,
                    successful_conversions=conversions,
                    total_value=total_value,
                    last_referral_date=last_referral,
                    phone=phone,
                    thank_you_sent=thank_you_sent
                )

                referrers.append(referrer)

            return referrers

    def get_referral_stats(self, period_days: int = 30) -> ReferralStats:
        """
        Get referral statistics.

        Args:
            period_days: Period to analyze

        Returns:
            ReferralStats object
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Previous period for trend
        prev_start = start_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Total referrals
            cursor = conn.execute("""
                SELECT COUNT(*) FROM referrals
                WHERE referral_date BETWEEN ? AND ?
            """, (start_date, end_date))

            total_referrals = cursor.fetchone()[0]

            # By source
            cursor = conn.execute("""
                SELECT referral_type, COUNT(*) FROM referrals
                WHERE referral_date BETWEEN ? AND ?
                GROUP BY referral_type
            """, (start_date, end_date))

            by_source = {row[0]: row[1] for row in cursor.fetchall()}

            # Conversion rate
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN converted_to_patient = 1 THEN 1 ELSE 0 END) as converted
                FROM referrals
                WHERE referral_date BETWEEN ? AND ?
            """, (start_date, end_date))

            row = cursor.fetchone()
            total = row[0] or 0
            converted = row[1] or 0
            conversion_rate = (converted / total * 100) if total > 0 else 0.0

            # Trend (compare to previous period)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM referrals
                WHERE referral_date BETWEEN ? AND ?
            """, (prev_start, start_date))

            prev_total = cursor.fetchone()[0] or 0
            trend = ((total_referrals - prev_total) / prev_total * 100) if prev_total > 0 else 0.0

            # Top referrers
            top_referrers = self.get_top_referrers(period_days=period_days, limit=5)

            # Calculate revenue from referrals
            cursor = conn.execute("""
                SELECT SUM(v.total_amount)
                FROM visits v
                INNER JOIN referrals r ON v.patient_id = r.patient_id
                WHERE r.referral_date BETWEEN ? AND ?
            """, (start_date, end_date))

            referral_revenue = cursor.fetchone()[0] or 0.0

            # Average value per referral
            avg_value = (referral_revenue / total_referrals) if total_referrals > 0 else 0.0

            stats = ReferralStats(
                period_start=start_date,
                period_end=end_date,
                total_referrals=total_referrals,
                by_source=by_source,
                conversion_rate=conversion_rate,
                trend=trend,
                top_referrers=top_referrers,
                avg_value_per_referral=avg_value,
                referral_revenue=referral_revenue
            )

            return stats

    def send_thank_you(
        self,
        referrer_id: int,
        referrer_type: str,
        new_patient_id: int,
        new_patient_name: str
    ) -> bool:
        """
        Record thank you message to referrer.

        Args:
            referrer_id: ID of referrer
            referrer_type: 'patient' or 'doctor'
            new_patient_id: ID of new patient who was referred
            new_patient_name: Name of new patient

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if thank you already sent for this referral
            cursor = conn.execute("""
                SELECT id FROM referral_thank_you
                WHERE referrer_id = ? AND referred_patient_id = ?
            """, (referrer_id, new_patient_id))

            if cursor.fetchone():
                logger.warning(f"Thank you already sent for referral {referrer_id} -> {new_patient_id}")
                return False

            # Create thank you record
            conn.execute("""
                INSERT INTO referral_thank_you
                (referrer_id, referrer_type, referred_patient_id, referred_patient_name)
                VALUES (?, ?, ?, ?)
            """, (referrer_id, referrer_type, new_patient_id, new_patient_name))

            conn.commit()

            logger.info(f"Thank you message queued for referrer {referrer_id}")
            return True

    def mark_thank_you_sent(self, thank_you_id: int, message_id: str) -> bool:
        """
        Mark thank you message as sent.

        Args:
            thank_you_id: Thank you record ID
            message_id: WhatsApp message ID

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE referral_thank_you
                SET message_sent = 1, sent_date = ?, message_id = ?
                WHERE id = ?
            """, (datetime.now(), message_id, thank_you_id))

            conn.commit()
            return True

    def get_pending_thank_you_messages(self) -> List[Dict]:
        """
        Get pending thank you messages to send.

        Returns:
            List of thank you message details
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    rt.id,
                    rt.referrer_id,
                    rt.referrer_type,
                    rt.referred_patient_name,
                    p.name as referrer_name,
                    p.phone as referrer_phone
                FROM referral_thank_you rt
                LEFT JOIN patients p ON rt.referrer_id = p.id
                WHERE rt.message_sent = 0
                ORDER BY rt.created_at
            """)

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row[0],
                    'referrer_id': row[1],
                    'referrer_type': row[2],
                    'referred_patient_name': row[3],
                    'referrer_name': row[4],
                    'referrer_phone': row[5]
                })

            return messages

    def get_referral_value(self, referrer_id: int, referrer_type: str) -> float:
        """
        Calculate total lifetime value of patients referred by this referrer.

        Args:
            referrer_id: Referrer ID
            referrer_type: 'patient' or 'doctor'

        Returns:
            Total value in rupees
        """
        return self._calculate_referral_value(referrer_id, referrer_type)

    def _calculate_referral_value(self, referrer_id: int, referrer_type: str) -> float:
        """
        Internal method to calculate referral value.

        Args:
            referrer_id: Referrer ID
            referrer_type: 'patient' or 'doctor'

        Returns:
            Total value
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get all patients referred by this person
            cursor = conn.execute("""
                SELECT patient_id FROM referrals
                WHERE referrer_id = ? AND referrer_type = ?
            """, (referrer_id, referrer_type))

            patient_ids = [row[0] for row in cursor.fetchall()]

            if not patient_ids:
                return 0.0

            # Calculate total revenue from these patients
            placeholders = ','.join('?' * len(patient_ids))
            cursor = conn.execute(f"""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM visits
                WHERE patient_id IN ({placeholders})
            """, patient_ids)

            total_value = cursor.fetchone()[0] or 0.0

            return total_value

    def get_referral_growth_trend(self, months: int = 6) -> List[Tuple[str, int]]:
        """
        Get monthly referral trend.

        Args:
            months: Number of months to analyze

        Returns:
            List of (month, count) tuples
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    strftime('%Y-%m', referral_date) as month,
                    COUNT(*) as count
                FROM referrals
                WHERE referral_date BETWEEN ? AND ?
                GROUP BY month
                ORDER BY month
            """, (start_date, end_date))

            trend = [(row[0], row[1]) for row in cursor.fetchall()]
            return trend

    def get_referral_conversion_funnel(self, period_days: int = 30) -> Dict[str, int]:
        """
        Get referral conversion funnel.

        Args:
            period_days: Period to analyze

        Returns:
            Funnel stages with counts
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Total referrals
            cursor = conn.execute("""
                SELECT COUNT(*) FROM referrals
                WHERE referral_date BETWEEN ? AND ?
            """, (start_date, end_date))
            total_referrals = cursor.fetchone()[0]

            # Converted to patient
            cursor = conn.execute("""
                SELECT COUNT(*) FROM referrals
                WHERE referral_date BETWEEN ? AND ?
                    AND converted_to_patient = 1
            """, (start_date, end_date))
            converted = cursor.fetchone()[0]

            # Had multiple visits
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT r.patient_id)
                FROM referrals r
                INNER JOIN visits v ON r.patient_id = v.patient_id
                WHERE r.referral_date BETWEEN ? AND ?
                GROUP BY r.patient_id
                HAVING COUNT(v.id) > 1
            """, (start_date, end_date))
            multiple_visits = len(cursor.fetchall())

            funnel = {
                'total_referrals': total_referrals,
                'became_patients': converted,
                'repeat_visits': multiple_visits
            }

            return funnel
