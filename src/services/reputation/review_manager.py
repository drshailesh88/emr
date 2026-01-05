"""
Review management service for DocAssist EMR.
Handles Google Reviews, review requests, sentiment analysis, and analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
import sqlite3
import json
import logging
from collections import Counter
import re

logger = logging.getLogger(__name__)


class ReviewSource(Enum):
    """Source of the review"""
    GOOGLE = "google"
    PRACTO = "practo"
    JUSTDIAL = "justdial"
    DIRECT = "direct"  # Direct feedback via app


class ReviewStatus(Enum):
    """Status of review request"""
    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class Sentiment(Enum):
    """Sentiment analysis result"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class Review:
    """Patient review data"""
    id: Optional[int] = None
    source: ReviewSource = ReviewSource.GOOGLE
    patient_id: Optional[int] = None
    rating: float = 0.0  # 1-5 stars
    text: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewer_profile_url: Optional[str] = None
    review_date: datetime = field(default_factory=datetime.now)
    response: Optional[str] = None
    response_date: Optional[datetime] = None
    sentiment: Sentiment = Sentiment.NEUTRAL
    keywords: List[str] = field(default_factory=list)
    is_verified: bool = False  # Verified patient
    helpful_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'source': self.source.value,
            'patient_id': self.patient_id,
            'rating': self.rating,
            'text': self.text,
            'reviewer_name': self.reviewer_name,
            'reviewer_profile_url': self.reviewer_profile_url,
            'review_date': self.review_date.isoformat(),
            'response': self.response,
            'response_date': self.response_date.isoformat() if self.response_date else None,
            'sentiment': self.sentiment.value,
            'keywords': self.keywords,
            'is_verified': self.is_verified,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ReviewRequest:
    """Review request sent to patient"""
    id: Optional[int] = None
    patient_id: int = 0
    visit_id: int = 0
    status: ReviewStatus = ReviewStatus.PENDING
    request_date: datetime = field(default_factory=datetime.now)
    sent_date: Optional[datetime] = None
    viewed_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    review_link: Optional[str] = None
    message_id: Optional[str] = None  # WhatsApp message ID
    expiry_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'visit_id': self.visit_id,
            'status': self.status.value,
            'request_date': self.request_date.isoformat(),
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'viewed_date': self.viewed_date.isoformat() if self.viewed_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'review_link': self.review_link,
            'message_id': self.message_id,
            'expiry_date': self.expiry_date.isoformat()
        }


@dataclass
class ReviewAnalytics:
    """Review analytics for a period"""
    period_start: datetime
    period_end: datetime
    avg_rating: float = 0.0
    total_reviews: int = 0
    rating_distribution: Dict[int, int] = field(default_factory=dict)  # {5: 10, 4: 5, ...}
    trend: float = 0.0  # Change from previous period
    response_rate: float = 0.0  # % of reviews responded to
    keywords_positive: List[Tuple[str, int]] = field(default_factory=list)  # [(keyword, count)]
    keywords_negative: List[Tuple[str, int]] = field(default_factory=list)
    sentiment_distribution: Dict[str, int] = field(default_factory=dict)
    reviews_by_source: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'avg_rating': round(self.avg_rating, 2),
            'total_reviews': self.total_reviews,
            'rating_distribution': self.rating_distribution,
            'trend': round(self.trend, 2),
            'response_rate': round(self.response_rate, 2),
            'keywords_positive': self.keywords_positive,
            'keywords_negative': self.keywords_negative,
            'sentiment_distribution': self.sentiment_distribution,
            'reviews_by_source': self.reviews_by_source
        }


@dataclass
class SentimentReport:
    """Detailed sentiment analysis report"""
    total_reviews: int = 0
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    positive_keywords: List[Tuple[str, int]] = field(default_factory=list)
    negative_keywords: List[Tuple[str, int]] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    sentiment_trend: List[Tuple[datetime, float]] = field(default_factory=list)  # (date, avg_sentiment_score)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'total_reviews': self.total_reviews,
            'positive_count': self.positive_count,
            'neutral_count': self.neutral_count,
            'negative_count': self.negative_count,
            'positive_keywords': self.positive_keywords,
            'negative_keywords': self.negative_keywords,
            'improvement_areas': self.improvement_areas,
            'sentiment_trend': [(d.isoformat(), s) for d, s in self.sentiment_trend]
        }


class ReviewManager:
    """Manages reviews, requests, and analytics"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize review manager.

        Args:
            db_path: Path to SQLite database. If None, operates in memory-only mode.
        """
        self.db_path = db_path
        if db_path:
            self._init_tables()

        # Positive/negative keywords for sentiment analysis (Indian context)
        self.positive_keywords = {
            'excellent', 'great', 'best', 'good', 'helpful', 'caring', 'kind',
            'patient', 'professional', 'experienced', 'knowledgeable', 'recommend',
            'trusted', 'relief', 'cured', 'better', 'improved', 'clean', 'hygienic',
            'affordable', 'reasonable', 'punctual', 'polite', 'friendly', 'understanding'
        }

        self.negative_keywords = {
            'bad', 'worst', 'terrible', 'poor', 'rude', 'arrogant', 'waiting',
            'delay', 'expensive', 'costly', 'unprofessional', 'dirty', 'unhygienic',
            'rushed', 'careless', 'wrong', 'mistake', 'ineffective', 'waste',
            'cheating', 'fraud', 'overcharging', 'negligent', 'incompetent'
        }

    def _init_tables(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    patient_id INTEGER,
                    rating REAL NOT NULL,
                    text TEXT,
                    reviewer_name TEXT,
                    reviewer_profile_url TEXT,
                    review_date TIMESTAMP NOT NULL,
                    response TEXT,
                    response_date TIMESTAMP,
                    sentiment TEXT,
                    keywords TEXT,  -- JSON array
                    is_verified BOOLEAN DEFAULT 0,
                    helpful_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS review_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    visit_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_date TIMESTAMP,
                    viewed_date TIMESTAMP,
                    completed_date TIMESTAMP,
                    review_link TEXT,
                    message_id TEXT,
                    expiry_date TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    FOREIGN KEY (visit_id) REFERENCES visits(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_reviews_date
                ON reviews(review_date DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_reviews_rating
                ON reviews(rating)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_review_requests_patient
                ON review_requests(patient_id, status)
            """)

            conn.commit()

    def request_review(self, patient_id: int, visit_id: int,
                      google_review_link: Optional[str] = None) -> ReviewRequest:
        """
        Request a review from patient after positive visit.

        Args:
            patient_id: Patient ID
            visit_id: Visit ID
            google_review_link: Google review link for the clinic

        Returns:
            ReviewRequest object
        """
        # Check if already requested for this visit
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id FROM review_requests
                WHERE visit_id = ? AND status != ?
            """, (visit_id, ReviewStatus.EXPIRED.value))

            if cursor.fetchone():
                logger.warning(f"Review already requested for visit {visit_id}")
                return None

            # Check visit indicators (should be called after positive visit)
            cursor = conn.execute("""
                SELECT chief_complaint FROM visits WHERE id = ?
            """, (visit_id,))

            visit_data = cursor.fetchone()
            if not visit_data:
                logger.error(f"Visit {visit_id} not found")
                return None

            # Create review request
            request = ReviewRequest(
                patient_id=patient_id,
                visit_id=visit_id,
                status=ReviewStatus.PENDING,
                review_link=google_review_link
            )

            conn.execute("""
                INSERT INTO review_requests
                (patient_id, visit_id, status, review_link, expiry_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                request.patient_id,
                request.visit_id,
                request.status.value,
                request.review_link,
                request.expiry_date
            ))

            conn.commit()
            request.id = cursor.lastrowid

            logger.info(f"Review request created for patient {patient_id}, visit {visit_id}")
            return request

    def mark_request_sent(self, request_id: int, message_id: str) -> bool:
        """Mark review request as sent"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE review_requests
                SET status = ?, sent_date = ?, message_id = ?
                WHERE id = ?
            """, (ReviewStatus.SENT.value, datetime.now(), message_id, request_id))
            conn.commit()
            return True

    def sync_google_reviews(self, place_id: str, api_key: str) -> List[Review]:
        """
        Fetch reviews from Google Places API.

        Args:
            place_id: Google Places ID for the clinic
            api_key: Google Places API key

        Returns:
            List of Review objects
        """
        # Note: This is a skeleton - actual implementation needs Google Places API
        # For production, use google-api-python-client library

        logger.info(f"Syncing Google reviews for place {place_id}")

        # Placeholder for API call
        # In production:
        # 1. Call Google Places API details endpoint
        # 2. Parse reviews from response
        # 3. Store new reviews, update existing ones

        reviews = []

        # Example: Store fetched reviews
        with sqlite3.connect(self.db_path) as conn:
            for review_data in reviews:
                # Check if review already exists
                cursor = conn.execute("""
                    SELECT id FROM reviews
                    WHERE source = ? AND reviewer_name = ? AND review_date = ?
                """, (ReviewSource.GOOGLE.value, review_data.reviewer_name,
                      review_data.review_date))

                existing = cursor.fetchone()

                if existing:
                    # Update existing review
                    conn.execute("""
                        UPDATE reviews
                        SET rating = ?, text = ?, response = ?, response_date = ?
                        WHERE id = ?
                    """, (review_data.rating, review_data.text, review_data.response,
                          review_data.response_date, existing[0]))
                else:
                    # Insert new review
                    sentiment = self._analyze_sentiment(review_data.text)
                    keywords = self._extract_keywords(review_data.text)

                    conn.execute("""
                        INSERT INTO reviews
                        (source, rating, text, reviewer_name, reviewer_profile_url,
                         review_date, response, response_date, sentiment, keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ReviewSource.GOOGLE.value,
                        review_data.rating,
                        review_data.text,
                        review_data.reviewer_name,
                        review_data.reviewer_profile_url,
                        review_data.review_date,
                        review_data.response,
                        review_data.response_date,
                        sentiment.value,
                        json.dumps(keywords)
                    ))

            conn.commit()

        return reviews

    def respond_to_review(self, review_id: int, response: str) -> bool:
        """
        Post response to a review.

        Args:
            review_id: Review ID
            response: Response text

        Returns:
            Success status
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get review details
            cursor = conn.execute("""
                SELECT source, reviewer_name FROM reviews WHERE id = ?
            """, (review_id,))

            review = cursor.fetchone()
            if not review:
                logger.error(f"Review {review_id} not found")
                return False

            source, reviewer_name = review

            # In production: Post to Google/Practo API
            # For now, just store locally

            conn.execute("""
                UPDATE reviews
                SET response = ?, response_date = ?
                WHERE id = ?
            """, (response, datetime.now(), review_id))

            conn.commit()

            logger.info(f"Response posted to review {review_id}")
            return True

    def get_review_analytics(self, period_days: int = 30) -> ReviewAnalytics:
        """
        Get review analytics for a period.

        Args:
            period_days: Number of days to analyze

        Returns:
            ReviewAnalytics object
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Previous period for trend calculation
        prev_start = start_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Current period stats
            cursor = conn.execute("""
                SELECT
                    AVG(rating) as avg_rating,
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN response IS NOT NULL THEN 1 ELSE 0 END) as responded
                FROM reviews
                WHERE review_date BETWEEN ? AND ?
            """, (start_date, end_date))

            row = cursor.fetchone()
            avg_rating = row[0] or 0.0
            total_reviews = row[1] or 0
            responded = row[2] or 0
            response_rate = (responded / total_reviews * 100) if total_reviews > 0 else 0.0

            # Rating distribution
            cursor = conn.execute("""
                SELECT CAST(rating AS INTEGER) as star, COUNT(*) as count
                FROM reviews
                WHERE review_date BETWEEN ? AND ?
                GROUP BY CAST(rating AS INTEGER)
            """, (start_date, end_date))

            rating_dist = {int(row[0]): row[1] for row in cursor.fetchall()}

            # Previous period average for trend
            cursor = conn.execute("""
                SELECT AVG(rating) FROM reviews
                WHERE review_date BETWEEN ? AND ?
            """, (prev_start, start_date))

            prev_avg = cursor.fetchone()[0] or 0.0
            trend = avg_rating - prev_avg

            # Sentiment distribution
            cursor = conn.execute("""
                SELECT sentiment, COUNT(*) FROM reviews
                WHERE review_date BETWEEN ? AND ?
                GROUP BY sentiment
            """, (start_date, end_date))

            sentiment_dist = {row[0]: row[1] for row in cursor.fetchall()}

            # Reviews by source
            cursor = conn.execute("""
                SELECT source, COUNT(*) FROM reviews
                WHERE review_date BETWEEN ? AND ?
                GROUP BY source
            """, (start_date, end_date))

            reviews_by_source = {row[0]: row[1] for row in cursor.fetchall()}

            # Extract keywords
            cursor = conn.execute("""
                SELECT text, sentiment FROM reviews
                WHERE review_date BETWEEN ? AND ? AND text IS NOT NULL
            """, (start_date, end_date))

            positive_keywords = []
            negative_keywords = []

            for text, sentiment in cursor.fetchall():
                keywords = self._extract_keywords(text)
                if sentiment == Sentiment.POSITIVE.value:
                    positive_keywords.extend(keywords)
                elif sentiment == Sentiment.NEGATIVE.value:
                    negative_keywords.extend(keywords)

            # Count and sort keywords
            pos_counter = Counter(positive_keywords)
            neg_counter = Counter(negative_keywords)

            analytics = ReviewAnalytics(
                period_start=start_date,
                period_end=end_date,
                avg_rating=avg_rating,
                total_reviews=total_reviews,
                rating_distribution=rating_dist,
                trend=trend,
                response_rate=response_rate,
                keywords_positive=pos_counter.most_common(10),
                keywords_negative=neg_counter.most_common(10),
                sentiment_distribution=sentiment_dist,
                reviews_by_source=reviews_by_source
            )

            return analytics

    def get_sentiment_analysis(self, period_days: int = 30) -> SentimentReport:
        """
        Get detailed sentiment analysis for reviews.

        Args:
            period_days: Number of days to analyze

        Returns:
            SentimentReport object
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        with sqlite3.connect(self.db_path) as conn:
            # Get all reviews in period
            cursor = conn.execute("""
                SELECT text, sentiment, rating, review_date
                FROM reviews
                WHERE review_date BETWEEN ? AND ? AND text IS NOT NULL
            """, (start_date, end_date))

            reviews = cursor.fetchall()

            positive_count = 0
            neutral_count = 0
            negative_count = 0

            positive_keywords = []
            negative_keywords = []

            # Sentiment trend (weekly)
            sentiment_by_week = {}

            for text, sentiment, rating, review_date in reviews:
                # Count sentiments
                if sentiment == Sentiment.POSITIVE.value:
                    positive_count += 1
                elif sentiment == Sentiment.NEUTRAL.value:
                    neutral_count += 1
                elif sentiment == Sentiment.NEGATIVE.value:
                    negative_count += 1

                # Extract keywords
                keywords = self._extract_keywords(text)
                if sentiment == Sentiment.POSITIVE.value:
                    positive_keywords.extend(keywords)
                elif sentiment == Sentiment.NEGATIVE.value:
                    negative_keywords.extend(keywords)

                # Track weekly sentiment
                review_date_obj = datetime.fromisoformat(review_date) if isinstance(review_date, str) else review_date
                week_start = review_date_obj - timedelta(days=review_date_obj.weekday())
                week_key = week_start.date()

                if week_key not in sentiment_by_week:
                    sentiment_by_week[week_key] = []
                sentiment_by_week[week_key].append(rating)

            # Calculate weekly averages
            sentiment_trend = []
            for week, ratings in sorted(sentiment_by_week.items()):
                avg_rating = sum(ratings) / len(ratings)
                sentiment_trend.append((datetime.combine(week, datetime.min.time()), avg_rating))

            # Count keywords
            pos_counter = Counter(positive_keywords)
            neg_counter = Counter(negative_keywords)

            # Identify improvement areas from negative keywords
            improvement_areas = []
            top_negative = neg_counter.most_common(5)

            improvement_map = {
                'waiting': 'Reduce waiting time',
                'delay': 'Improve appointment scheduling',
                'expensive': 'Review pricing transparency',
                'costly': 'Consider affordable packages',
                'rude': 'Staff training on patient communication',
                'rushed': 'Allow more time per consultation',
                'dirty': 'Improve clinic hygiene',
                'unhygienic': 'Enhance sanitation protocols'
            }

            for keyword, count in top_negative:
                if keyword in improvement_map:
                    improvement_areas.append(improvement_map[keyword])

            report = SentimentReport(
                total_reviews=len(reviews),
                positive_count=positive_count,
                neutral_count=neutral_count,
                negative_count=negative_count,
                positive_keywords=pos_counter.most_common(10),
                negative_keywords=neg_counter.most_common(10),
                improvement_areas=improvement_areas,
                sentiment_trend=sentiment_trend
            )

            return report

    def get_template_response(self, review: Review) -> str:
        """
        Get template response based on review rating and content.

        Args:
            review: Review object

        Returns:
            Template response text
        """
        if review.rating >= 4.0:
            # Positive review
            templates = [
                f"Thank you so much {review.reviewer_name}! We're delighted that you had a positive experience. Your health and satisfaction are our top priorities. 🙏",
                f"Dear {review.reviewer_name}, we truly appreciate your kind words! It motivates our entire team to continue providing the best care possible. Thank you for trusting us with your health. 🙏",
                f"Thank you {review.reviewer_name}! We're grateful for your feedback and happy we could help. Looking forward to serving you again. 🙏"
            ]
        elif review.rating >= 3.0:
            # Neutral review
            templates = [
                f"Thank you for your feedback {review.reviewer_name}. We appreciate you taking the time to share your experience. We'd love to know how we can serve you better. Please feel free to reach out to us directly. 🙏",
                f"Dear {review.reviewer_name}, thank you for your review. We're always looking to improve. If you have specific suggestions, we'd be happy to hear them. 🙏"
            ]
        else:
            # Negative review
            templates = [
                f"Dear {review.reviewer_name}, we sincerely apologize for your experience. This is not the standard of care we strive for. We would appreciate the opportunity to discuss this with you directly and make things right. Please contact us at your convenience. 🙏",
                f"{review.reviewer_name}, we're truly sorry for falling short of your expectations. Your feedback is important to us. Please allow us to address your concerns personally. We're committed to improving. 🙏"
            ]

        # Return first template (in production, could rotate or personalize)
        return templates[0]

    def _analyze_sentiment(self, text: Optional[str]) -> Sentiment:
        """
        Analyze sentiment of review text.

        Args:
            text: Review text

        Returns:
            Sentiment enum
        """
        if not text:
            return Sentiment.NEUTRAL

        text_lower = text.lower()

        # Count positive and negative keywords
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)

        if positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    def _extract_keywords(self, text: Optional[str]) -> List[str]:
        """
        Extract keywords from review text.

        Args:
            text: Review text

        Returns:
            List of keywords
        """
        if not text:
            return []

        text_lower = text.lower()

        # Remove punctuation
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)

        # Extract known keywords
        keywords = []
        all_keywords = self.positive_keywords | self.negative_keywords

        for keyword in all_keywords:
            if keyword in text_clean:
                keywords.append(keyword)

        return keywords

    def get_recent_reviews(self, limit: int = 10) -> List[Review]:
        """
        Get recent reviews.

        Args:
            limit: Number of reviews to fetch

        Returns:
            List of Review objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, source, patient_id, rating, text, reviewer_name,
                       reviewer_profile_url, review_date, response, response_date,
                       sentiment, keywords, is_verified, helpful_count, created_at
                FROM reviews
                ORDER BY review_date DESC
                LIMIT ?
            """, (limit,))

            reviews = []
            for row in cursor.fetchall():
                review = Review(
                    id=row[0],
                    source=ReviewSource(row[1]),
                    patient_id=row[2],
                    rating=row[3],
                    text=row[4],
                    reviewer_name=row[5],
                    reviewer_profile_url=row[6],
                    review_date=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                    response=row[8],
                    response_date=datetime.fromisoformat(row[9]) if row[9] else None,
                    sentiment=Sentiment(row[10]) if row[10] else Sentiment.NEUTRAL,
                    keywords=json.loads(row[11]) if row[11] else [],
                    is_verified=bool(row[12]),
                    helpful_count=row[13] or 0,
                    created_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now()
                )
                reviews.append(review)

            return reviews
