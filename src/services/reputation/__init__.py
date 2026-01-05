"""
Reputation management services for DocAssist EMR.

This module provides comprehensive reputation and referral tracking:
- Review management (Google, Practo, etc.)
- Referral tracking and analytics
- NPS (Net Promoter Score) surveys
- Growth recommendations
- Loyalty program management
"""

from .review_manager import (
    ReviewManager,
    Review,
    ReviewRequest,
    ReviewAnalytics,
    SentimentReport,
    ReviewSource,
    ReviewStatus,
    Sentiment
)

from .referral_tracker import (
    ReferralTracker,
    ReferralSource,
    Referrer,
    ReferralStats,
    ReferralType
)

from .nps_tracker import (
    NPSTracker,
    Survey,
    NPSResponse,
    NPSScore,
    DetractorAlert,
    NPSCategory,
    SurveyStatus
)

from .growth_recommendations import (
    GrowthRecommendations,
    Recommendation,
    Benchmark,
    RecommendationType,
    Priority,
    ImpactLevel
)

from .loyalty_program import (
    LoyaltyProgram,
    LoyaltyMember,
    Reward,
    Milestone,
    Tier,
    RewardType,
    MilestoneType
)

__all__ = [
    # Review Management
    'ReviewManager',
    'Review',
    'ReviewRequest',
    'ReviewAnalytics',
    'SentimentReport',
    'ReviewSource',
    'ReviewStatus',
    'Sentiment',

    # Referral Tracking
    'ReferralTracker',
    'ReferralSource',
    'Referrer',
    'ReferralStats',
    'ReferralType',

    # NPS Tracking
    'NPSTracker',
    'Survey',
    'NPSResponse',
    'NPSScore',
    'DetractorAlert',
    'NPSCategory',
    'SurveyStatus',

    # Growth Recommendations
    'GrowthRecommendations',
    'Recommendation',
    'Benchmark',
    'RecommendationType',
    'Priority',
    'ImpactLevel',

    # Loyalty Program
    'LoyaltyProgram',
    'LoyaltyMember',
    'Reward',
    'Milestone',
    'Tier',
    'RewardType',
    'MilestoneType',
]
