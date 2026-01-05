"""
Loyalty program service for DocAssist EMR.
Tracks patient engagement, rewards, and milestones.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


class Tier(Enum):
    """Loyalty tier"""
    BRONZE = "bronze"    # 1-3 visits
    SILVER = "silver"    # 4-10 visits
    GOLD = "gold"        # 11+ visits or 2+ referrals
    PLATINUM = "platinum"  # VIP patients (special cases)


class RewardType(Enum):
    """Type of reward"""
    DISCOUNT = "discount"
    PRIORITY_BOOKING = "priority_booking"
    FREE_CHECKUP = "free_checkup"
    HEALTH_TIPS = "health_tips"
    BIRTHDAY_GIFT = "birthday_gift"
    MILESTONE = "milestone"


class MilestoneType(Enum):
    """Patient milestone"""
    FIRST_VISIT = "first_visit"
    ONE_YEAR = "one_year"
    TENTH_VISIT = "tenth_visit"
    FIRST_REFERRAL = "first_referral"
    FIVE_REFERRALS = "five_referrals"
    PERFECT_COMPLIANCE = "perfect_compliance"  # All follow-ups completed


@dataclass
class LoyaltyMember:
    """Loyalty program member"""
    id: Optional[int] = None
    patient_id: int = 0
    tier: Tier = Tier.BRONZE
    points: int = 0
    total_visits: int = 0
    total_spend: float = 0.0
    referral_count: int = 0
    enrollment_date: datetime = field(default_factory=datetime.now)
    last_visit_date: Optional[datetime] = None
    tier_since: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'tier': self.tier.value,
            'points': self.points,
            'total_visits': self.total_visits,
            'total_spend': round(self.total_spend, 2),
            'referral_count': self.referral_count,
            'enrollment_date': self.enrollment_date.isoformat(),
            'last_visit_date': self.last_visit_date.isoformat() if self.last_visit_date else None,
            'tier_since': self.tier_since.isoformat()
        }


@dataclass
class Reward:
    """Patient reward"""
    id: Optional[int] = None
    patient_id: int = 0
    type: RewardType = RewardType.DISCOUNT
    title: str = ""
    description: str = ""
    value: Optional[float] = None  # Discount amount or value
    earned_date: datetime = field(default_factory=datetime.now)
    expiry_date: Optional[datetime] = None
    is_redeemed: bool = False
    redeemed_date: Optional[datetime] = None
    visit_id: Optional[int] = None  # Visit where redeemed

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'type': self.type.value,
            'title': self.title,
            'description': self.description,
            'value': self.value,
            'earned_date': self.earned_date.isoformat(),
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_redeemed': self.is_redeemed,
            'redeemed_date': self.redeemed_date.isoformat() if self.redeemed_date else None,
            'visit_id': self.visit_id
        }


@dataclass
class Milestone:
    """Patient milestone"""
    id: Optional[int] = None
    patient_id: int = 0
    type: MilestoneType = MilestoneType.FIRST_VISIT
    title: str = ""
    description: str = ""
    achieved_date: datetime = field(default_factory=datetime.now)
    celebration_sent: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'type': self.type.value,
            'title': self.title,
            'description': self.description,
            'achieved_date': self.achieved_date.isoformat(),
            'celebration_sent': self.celebration_sent
        }


class LoyaltyProgram:
    """Manages patient loyalty program"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize loyalty program.

        Args:
            db_path: Path to SQLite database. If None, operates in memory-only mode.
        """
        self.db_path = db_path
        if db_path:
            self._init_tables()

        # Points earning rules
        self.points_per_visit = 10
        self.points_per_rupee = 0.1  # 10 points per ₹100 spent
        self.points_per_referral = 50

        # Tier thresholds
        self.tier_thresholds = {
            Tier.BRONZE: {'visits': 0, 'referrals': 0},
            Tier.SILVER: {'visits': 4, 'referrals': 0},
            Tier.GOLD: {'visits': 11, 'referrals': 2},
            Tier.PLATINUM: {'visits': 25, 'referrals': 5}
        }

    def _init_tables(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS loyalty_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER UNIQUE NOT NULL,
                    tier TEXT NOT NULL,
                    points INTEGER DEFAULT 0,
                    total_visits INTEGER DEFAULT 0,
                    total_spend REAL DEFAULT 0.0,
                    referral_count INTEGER DEFAULT 0,
                    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_visit_date TIMESTAMP,
                    tier_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS loyalty_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    value REAL,
                    earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expiry_date TIMESTAMP,
                    is_redeemed BOOLEAN DEFAULT 0,
                    redeemed_date TIMESTAMP,
                    visit_id INTEGER,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    FOREIGN KEY (visit_id) REFERENCES visits(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS loyalty_milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    achieved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    celebration_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_loyalty_members_patient
                ON loyalty_members(patient_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_loyalty_rewards_patient
                ON loyalty_rewards(patient_id, is_redeemed)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_loyalty_milestones_patient
                ON loyalty_milestones(patient_id)
            """)

            conn.commit()

    def enroll_patient(self, patient_id: int) -> Optional[LoyaltyMember]:
        """
        Enroll patient in loyalty program.

        Args:
            patient_id: Patient ID

        Returns:
            LoyaltyMember object or None
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if already enrolled
            cursor = conn.execute("""
                SELECT id FROM loyalty_members WHERE patient_id = ?
            """, (patient_id,))

            if cursor.fetchone():
                logger.warning(f"Patient {patient_id} already enrolled in loyalty program")
                return None

            # Create member
            member = LoyaltyMember(
                patient_id=patient_id,
                tier=Tier.BRONZE
            )

            cursor = conn.execute("""
                INSERT INTO loyalty_members
                (patient_id, tier)
                VALUES (?, ?)
            """, (member.patient_id, member.tier.value))

            conn.commit()
            member.id = cursor.lastrowid

            # Record first visit milestone
            self._check_milestone(patient_id, MilestoneType.FIRST_VISIT)

            logger.info(f"Patient {patient_id} enrolled in loyalty program")
            return member

    def record_visit(self, patient_id: int, visit_value: float = 0.0) -> bool:
        """
        Record a visit and update loyalty status.

        Args:
            patient_id: Patient ID
            visit_value: Visit amount in rupees

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get or create member
            cursor = conn.execute("""
                SELECT id FROM loyalty_members WHERE patient_id = ?
            """, (patient_id,))

            member_row = cursor.fetchone()

            if not member_row:
                # Auto-enroll
                member = self.enroll_patient(patient_id)
                if not member:
                    return False

            # Calculate points
            visit_points = self.points_per_visit
            spend_points = int(visit_value * self.points_per_rupee)
            total_points = visit_points + spend_points

            # Update member
            conn.execute("""
                UPDATE loyalty_members
                SET total_visits = total_visits + 1,
                    total_spend = total_spend + ?,
                    points = points + ?,
                    last_visit_date = ?
                WHERE patient_id = ?
            """, (visit_value, total_points, datetime.now(), patient_id))

            conn.commit()

            # Check for tier upgrade
            self._check_tier_upgrade(patient_id)

            # Check for milestones
            self._check_visit_milestones(patient_id)

            logger.info(f"Visit recorded for patient {patient_id}, earned {total_points} points")
            return True

    def calculate_tier(self, patient_id: int) -> Tier:
        """
        Calculate appropriate tier for patient.

        Args:
            patient_id: Patient ID

        Returns:
            Tier enum
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT total_visits, referral_count
                FROM loyalty_members
                WHERE patient_id = ?
            """, (patient_id,))

            row = cursor.fetchone()
            if not row:
                return Tier.BRONZE

            visits = row[0]
            referrals = row[1]

            # Determine tier
            if visits >= self.tier_thresholds[Tier.PLATINUM]['visits'] and \
               referrals >= self.tier_thresholds[Tier.PLATINUM]['referrals']:
                return Tier.PLATINUM
            elif visits >= self.tier_thresholds[Tier.GOLD]['visits'] or \
                 referrals >= self.tier_thresholds[Tier.GOLD]['referrals']:
                return Tier.GOLD
            elif visits >= self.tier_thresholds[Tier.SILVER]['visits']:
                return Tier.SILVER
            else:
                return Tier.BRONZE

    def get_rewards(self, patient_id: int, active_only: bool = True) -> List[Reward]:
        """
        Get patient rewards.

        Args:
            patient_id: Patient ID
            active_only: Only return unredeemed, non-expired rewards

        Returns:
            List of Reward objects
        """
        with sqlite3.connect(self.db_path) as conn:
            if active_only:
                cursor = conn.execute("""
                    SELECT id, type, title, description, value, earned_date,
                           expiry_date, is_redeemed, redeemed_date, visit_id
                    FROM loyalty_rewards
                    WHERE patient_id = ?
                        AND is_redeemed = 0
                        AND (expiry_date IS NULL OR expiry_date > ?)
                    ORDER BY earned_date DESC
                """, (patient_id, datetime.now()))
            else:
                cursor = conn.execute("""
                    SELECT id, type, title, description, value, earned_date,
                           expiry_date, is_redeemed, redeemed_date, visit_id
                    FROM loyalty_rewards
                    WHERE patient_id = ?
                    ORDER BY earned_date DESC
                """, (patient_id,))

            rewards = []
            for row in cursor.fetchall():
                reward = Reward(
                    id=row[0],
                    patient_id=patient_id,
                    type=RewardType(row[1]),
                    title=row[2],
                    description=row[3],
                    value=row[4],
                    earned_date=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                    expiry_date=datetime.fromisoformat(row[6]) if row[6] else None,
                    is_redeemed=bool(row[7]),
                    redeemed_date=datetime.fromisoformat(row[8]) if row[8] else None,
                    visit_id=row[9]
                )
                rewards.append(reward)

            return rewards

    def check_milestone(self, patient_id: int) -> Optional[Milestone]:
        """
        Check if patient achieved any milestone.

        Args:
            patient_id: Patient ID

        Returns:
            Milestone object or None
        """
        # This is called automatically, but can be used manually
        return self._check_visit_milestones(patient_id)

    def _check_tier_upgrade(self, patient_id: int) -> bool:
        """Check and apply tier upgrade"""
        new_tier = self.calculate_tier(patient_id)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT tier FROM loyalty_members WHERE patient_id = ?
            """, (patient_id,))

            row = cursor.fetchone()
            if not row:
                return False

            current_tier = Tier(row[0])

            # Tier upgrade
            tier_order = {Tier.BRONZE: 0, Tier.SILVER: 1, Tier.GOLD: 2, Tier.PLATINUM: 3}

            if tier_order[new_tier] > tier_order[current_tier]:
                conn.execute("""
                    UPDATE loyalty_members
                    SET tier = ?, tier_since = ?
                    WHERE patient_id = ?
                """, (new_tier.value, datetime.now(), patient_id))

                conn.commit()

                # Grant tier upgrade reward
                self._grant_tier_reward(patient_id, new_tier)

                logger.info(f"Patient {patient_id} upgraded to {new_tier.value}")
                return True

        return False

    def _grant_tier_reward(self, patient_id: int, tier: Tier):
        """Grant reward for tier achievement"""
        rewards = {
            Tier.SILVER: {
                'title': '10% Discount on Next Visit',
                'description': 'Congratulations on reaching Silver tier!',
                'type': RewardType.DISCOUNT,
                'value': 10.0
            },
            Tier.GOLD: {
                'title': 'Priority Appointment Booking',
                'description': 'You now have priority booking access',
                'type': RewardType.PRIORITY_BOOKING,
                'value': None
            },
            Tier.PLATINUM: {
                'title': 'Free Annual Checkup',
                'description': 'Thank you for your loyalty! Enjoy a free checkup',
                'type': RewardType.FREE_CHECKUP,
                'value': None
            }
        }

        if tier in rewards:
            reward_data = rewards[tier]

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO loyalty_rewards
                    (patient_id, type, title, description, value, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    patient_id,
                    reward_data['type'].value,
                    reward_data['title'],
                    reward_data['description'],
                    reward_data['value'],
                    datetime.now() + timedelta(days=90)  # 90 day expiry
                ))

                conn.commit()

    def _check_milestone(self, patient_id: int, milestone_type: MilestoneType) -> Optional[Milestone]:
        """Check and record milestone"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if milestone already achieved
            cursor = conn.execute("""
                SELECT id FROM loyalty_milestones
                WHERE patient_id = ? AND type = ?
            """, (patient_id, milestone_type.value))

            if cursor.fetchone():
                return None

            # Milestone details
            milestone_details = {
                MilestoneType.FIRST_VISIT: {
                    'title': 'Welcome!',
                    'description': 'Thank you for choosing us for your healthcare'
                },
                MilestoneType.ONE_YEAR: {
                    'title': '1 Year Anniversary',
                    'description': 'Thank you for trusting us for one year!'
                },
                MilestoneType.TENTH_VISIT: {
                    'title': '10th Visit Milestone',
                    'description': 'You\'ve completed 10 visits with us!'
                },
                MilestoneType.FIRST_REFERRAL: {
                    'title': 'First Referral',
                    'description': 'Thank you for referring someone to us!'
                },
                MilestoneType.FIVE_REFERRALS: {
                    'title': '5 Referrals Champion',
                    'description': 'You\'re an amazing advocate for our practice!'
                }
            }

            details = milestone_details.get(milestone_type, {
                'title': 'Milestone Achieved',
                'description': ''
            })

            # Record milestone
            milestone = Milestone(
                patient_id=patient_id,
                type=milestone_type,
                title=details['title'],
                description=details['description']
            )

            cursor = conn.execute("""
                INSERT INTO loyalty_milestones
                (patient_id, type, title, description)
                VALUES (?, ?, ?, ?)
            """, (
                milestone.patient_id,
                milestone.type.value,
                milestone.title,
                milestone.description
            ))

            conn.commit()
            milestone.id = cursor.lastrowid

            logger.info(f"Milestone achieved: {milestone_type.value} for patient {patient_id}")
            return milestone

    def _check_visit_milestones(self, patient_id: int) -> Optional[Milestone]:
        """Check for visit-based milestones"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT total_visits, enrollment_date
                FROM loyalty_members
                WHERE patient_id = ?
            """, (patient_id,))

            row = cursor.fetchone()
            if not row:
                return None

            visits = row[0]
            enrollment_date = datetime.fromisoformat(row[1]) if row[1] else datetime.now()

            # Check 10th visit
            if visits == 10:
                return self._check_milestone(patient_id, MilestoneType.TENTH_VISIT)

            # Check 1 year anniversary
            if (datetime.now() - enrollment_date).days >= 365:
                return self._check_milestone(patient_id, MilestoneType.ONE_YEAR)

        return None

    def record_referral(self, patient_id: int) -> bool:
        """
        Record a referral made by patient.

        Args:
            patient_id: Patient ID who made the referral

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            # Update referral count
            conn.execute("""
                UPDATE loyalty_members
                SET referral_count = referral_count + 1,
                    points = points + ?
                WHERE patient_id = ?
            """, (self.points_per_referral, patient_id))

            conn.commit()

            # Check for referral milestones
            cursor = conn.execute("""
                SELECT referral_count FROM loyalty_members
                WHERE patient_id = ?
            """, (patient_id,))

            referral_count = cursor.fetchone()[0]

            if referral_count == 1:
                self._check_milestone(patient_id, MilestoneType.FIRST_REFERRAL)
            elif referral_count == 5:
                self._check_milestone(patient_id, MilestoneType.FIVE_REFERRALS)

            # Check for tier upgrade
            self._check_tier_upgrade(patient_id)

            logger.info(f"Referral recorded for patient {patient_id}")
            return True

    def get_member(self, patient_id: int) -> Optional[LoyaltyMember]:
        """
        Get loyalty member details.

        Args:
            patient_id: Patient ID

        Returns:
            LoyaltyMember object or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, tier, points, total_visits, total_spend,
                       referral_count, enrollment_date, last_visit_date, tier_since
                FROM loyalty_members
                WHERE patient_id = ?
            """, (patient_id,))

            row = cursor.fetchone()
            if not row:
                return None

            member = LoyaltyMember(
                id=row[0],
                patient_id=patient_id,
                tier=Tier(row[1]),
                points=row[2],
                total_visits=row[3],
                total_spend=row[4],
                referral_count=row[5],
                enrollment_date=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                last_visit_date=datetime.fromisoformat(row[7]) if row[7] else None,
                tier_since=datetime.fromisoformat(row[8]) if row[8] else datetime.now()
            )

            return member

    def redeem_reward(self, reward_id: int, visit_id: int) -> bool:
        """
        Redeem a reward.

        Args:
            reward_id: Reward ID
            visit_id: Visit where reward is redeemed

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if reward exists and is not redeemed
            cursor = conn.execute("""
                SELECT patient_id, is_redeemed FROM loyalty_rewards
                WHERE id = ?
            """, (reward_id,))

            row = cursor.fetchone()
            if not row:
                logger.error(f"Reward {reward_id} not found")
                return False

            if row[1]:
                logger.warning(f"Reward {reward_id} already redeemed")
                return False

            # Redeem
            conn.execute("""
                UPDATE loyalty_rewards
                SET is_redeemed = 1, redeemed_date = ?, visit_id = ?
                WHERE id = ?
            """, (datetime.now(), visit_id, reward_id))

            conn.commit()

            logger.info(f"Reward {reward_id} redeemed")
            return True
