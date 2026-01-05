"""
Example usage of reputation management services.
Demonstrates how to use all modules together for practice growth.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from datetime import datetime, timedelta
from src.services.reputation import (
    ReviewManager,
    ReferralTracker,
    ReferralType,
    NPSTracker,
    GrowthRecommendations,
    LoyaltyProgram
)


def demo_review_management(db_path: str):
    """Demonstrate review management"""
    print("\n" + "=" * 60)
    print("REVIEW MANAGEMENT DEMO")
    print("=" * 60)

    rm = ReviewManager(db_path)

    # Request review
    print("\n1. Requesting review after positive visit...")
    request = rm.request_review(
        patient_id=1,
        visit_id=1,
        google_review_link="https://g.page/r/example"
    )
    if request:
        print(f"   ✓ Review request created (ID: {request.id})")
        print(f"   Status: {request.status.value}")
        print(f"   Expires: {request.expiry_date.strftime('%Y-%m-%d')}")

    # Get analytics
    print("\n2. Getting review analytics (last 30 days)...")
    analytics = rm.get_review_analytics(period_days=30)
    print(f"   Average Rating: {analytics.avg_rating:.2f}/5.0")
    print(f"   Total Reviews: {analytics.total_reviews}")
    print(f"   Response Rate: {analytics.response_rate:.1f}%")
    print(f"   Trend: {analytics.trend:+.2f}")

    if analytics.rating_distribution:
        print("\n   Rating Distribution:")
        for stars in sorted(analytics.rating_distribution.keys(), reverse=True):
            count = analytics.rating_distribution[stars]
            bar = "★" * count
            print(f"   {stars}⭐: {bar} ({count})")

    # Sentiment analysis
    print("\n3. Sentiment analysis...")
    sentiment = rm.get_sentiment_analysis(period_days=30)
    print(f"   Positive: {sentiment.positive_count}")
    print(f"   Neutral: {sentiment.neutral_count}")
    print(f"   Negative: {sentiment.negative_count}")

    if sentiment.positive_keywords:
        print(f"\n   Top Positive Keywords:")
        for keyword, count in sentiment.positive_keywords[:5]:
            print(f"   - {keyword} ({count}x)")

    if sentiment.negative_keywords:
        print(f"\n   Top Negative Keywords:")
        for keyword, count in sentiment.negative_keywords[:5]:
            print(f"   - {keyword} ({count}x)")

    if sentiment.improvement_areas:
        print(f"\n   Improvement Areas:")
        for area in sentiment.improvement_areas[:3]:
            print(f"   - {area}")


def demo_referral_tracking(db_path: str):
    """Demonstrate referral tracking"""
    print("\n" + "=" * 60)
    print("REFERRAL TRACKING DEMO")
    print("=" * 60)

    rt = ReferralTracker(db_path)

    # Track referral
    print("\n1. Tracking new patient referral...")
    success = rt.track_referral(
        patient_id=2,
        referral_type=ReferralType.PATIENT_REFERRAL,
        referrer_id=1,
        referrer_type='patient',
        referrer_name='Ram Lal'
    )
    if success:
        print("   ✓ Referral tracked successfully")

    # Get referral stats
    print("\n2. Referral statistics (last 30 days)...")
    stats = rt.get_referral_stats(period_days=30)
    print(f"   Total Referrals: {stats.total_referrals}")
    print(f"   Conversion Rate: {stats.conversion_rate:.1f}%")
    print(f"   Trend: {stats.trend:+.1f}%")

    if stats.by_source:
        print("\n   Referrals by Source:")
        for source, count in sorted(stats.by_source.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {source}: {count}")

    # Top referrers
    print("\n3. Top referrers...")
    top_referrers = rt.get_top_referrers(period_days=365, limit=5)
    if top_referrers:
        print(f"\n   {'Name':<20} {'Referrals':<10} {'Value':<15} {'Thank You'}")
        print("   " + "-" * 60)
        for ref in top_referrers:
            thanks = "✓" if ref.thank_you_sent else "✗"
            print(f"   {ref.name:<20} {ref.referral_count:<10} ₹{ref.total_value:<14,.2f} {thanks}")

    # Conversion funnel
    print("\n4. Referral conversion funnel...")
    funnel = rt.get_referral_conversion_funnel(period_days=30)
    print(f"   Total Referrals: {funnel['total_referrals']}")
    print(f"   Became Patients: {funnel['became_patients']}")
    print(f"   Repeat Visits: {funnel['repeat_visits']}")


def demo_nps_tracking(db_path: str):
    """Demonstrate NPS tracking"""
    print("\n" + "=" * 60)
    print("NPS TRACKING DEMO")
    print("=" * 60)

    nps = NPSTracker(db_path)

    # Send survey
    print("\n1. Sending NPS survey...")
    survey = nps.send_nps_survey(patient_id=1)
    if survey:
        print(f"   ✓ Survey created (ID: {survey.id})")
        print(f"   Status: {survey.status.value}")

    # Calculate NPS
    print("\n2. Calculating NPS (last 30 days)...")
    score = nps.calculate_nps(period_days=30)
    print(f"   NPS Score: {score.score:.1f}")
    print(f"   Promoters: {score.promoters} ({score.promoters/score.total_responses*100:.1f}%)" if score.total_responses > 0 else "   No responses yet")
    print(f"   Passives: {score.passives} ({score.passives/score.total_responses*100:.1f}%)" if score.total_responses > 0 else "")
    print(f"   Detractors: {score.detractors} ({score.detractors/score.total_responses*100:.1f}%)" if score.total_responses > 0 else "")
    print(f"   Trend: {score.trend:+.1f}")
    print(f"   Response Rate: {score.response_rate:.1f}%")

    # Detractor alerts
    print("\n3. Checking for detractor alerts...")
    alerts = nps.get_detractor_alerts(days=7)
    if alerts:
        print(f"   ⚠️  {len(alerts)} detractor(s) need follow-up:")
        for alert in alerts:
            follow_up = "✓" if alert.follow_up_completed else "✗"
            print(f"\n   - {alert.patient_name} (Score: {alert.score}/10)")
            print(f"     Feedback: {alert.feedback}")
            print(f"     Follow-up: {follow_up}")
    else:
        print("   ✓ No detractors to follow up with")

    # NPS trend
    print("\n4. NPS trend (last 6 months)...")
    trend = nps.get_nps_trend(months=6)
    if trend:
        print(f"\n   {'Month':<10} {'NPS Score'}")
        print("   " + "-" * 25)
        for month, nps_score in trend:
            bar = "█" * int(abs(nps_score) / 10)
            sign = "+" if nps_score >= 0 else ""
            print(f"   {month:<10} {sign}{nps_score:>6.1f} {bar}")


def demo_growth_recommendations(db_path: str):
    """Demonstrate growth recommendations"""
    print("\n" + "=" * 60)
    print("GROWTH RECOMMENDATIONS DEMO")
    print("=" * 60)

    gr = GrowthRecommendations(db_path)

    # Get all recommendations
    print("\n1. Analyzing practice (last 30 days)...")
    recommendations = gr.analyze_practice(period_days=30)

    if recommendations:
        print(f"\n   Found {len(recommendations)} recommendations:")

        # Group by priority
        by_priority = {}
        for rec in recommendations:
            priority = rec.priority.value
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(rec)

        for priority in ['critical', 'high', 'medium', 'low']:
            if priority in by_priority:
                print(f"\n   {priority.upper()} Priority:")
                for rec in by_priority[priority]:
                    impact_emoji = "🔥" if rec.impact.value == "high" else "📊"
                    print(f"\n   {impact_emoji} {rec.title}")
                    print(f"      {rec.description}")
                    print(f"      → Action: {rec.action}")
    else:
        print("   ✓ No issues found - practice is running smoothly!")

    # Quick wins
    print("\n2. Quick wins (high impact, easy to implement)...")
    quick_wins = gr.get_quick_wins(period_days=30)
    if quick_wins:
        for i, rec in enumerate(quick_wins, 1):
            print(f"\n   {i}. {rec.title}")
            print(f"      {rec.action}")

    # Benchmark comparison
    print("\n3. Benchmark comparison...")
    benchmarks = gr.get_competitor_benchmark()
    print(f"\n   {'Metric':<25} {'Your Value':<15} {'Benchmark':<15} {'Status'}")
    print("   " + "-" * 70)
    for bm in benchmarks:
        status_emoji = "✅" if bm.status == 'above' else "⚠️ "
        print(f"   {bm.metric_name:<25} {bm.your_value:<15.2f} {bm.benchmark_value:<15.2f} {status_emoji}")


def demo_loyalty_program(db_path: str):
    """Demonstrate loyalty program"""
    print("\n" + "=" * 60)
    print("LOYALTY PROGRAM DEMO")
    print("=" * 60)

    lp = LoyaltyProgram(db_path)

    # Enroll patient
    print("\n1. Enrolling patient in loyalty program...")
    member = lp.enroll_patient(patient_id=3)
    if member:
        print(f"   ✓ Patient enrolled (ID: {member.id})")
        print(f"   Tier: {member.tier.value.upper()}")
        print(f"   Points: {member.points}")

    # Record visits
    print("\n2. Recording visits and calculating points...")
    for i in range(5):
        lp.record_visit(patient_id=3, visit_value=500.0)
    print("   ✓ Recorded 5 visits worth ₹500 each")

    # Get member details
    member = lp.get_member(patient_id=3)
    if member:
        print(f"\n   Updated member status:")
        print(f"   Tier: {member.tier.value.upper()}")
        print(f"   Points: {member.points}")
        print(f"   Total Visits: {member.total_visits}")
        print(f"   Total Spend: ₹{member.total_spend:,.2f}")
        print(f"   Referrals: {member.referral_count}")

    # Get rewards
    print("\n3. Available rewards...")
    rewards = lp.get_rewards(patient_id=3, active_only=True)
    if rewards:
        for reward in rewards:
            print(f"\n   🎁 {reward.title}")
            print(f"      {reward.description}")
            if reward.value:
                print(f"      Value: ₹{reward.value}")
            if reward.expiry_date:
                print(f"      Expires: {reward.expiry_date.strftime('%Y-%m-%d')}")
    else:
        print("   No active rewards yet")

    # Record referral
    print("\n4. Recording referral...")
    lp.record_referral(patient_id=3)
    print("   ✓ Referral recorded")

    member = lp.get_member(patient_id=3)
    print(f"   Points earned: +{lp.points_per_referral}")
    print(f"   New total: {member.points} points")


def main():
    """Run all demos"""
    # Use test database
    db_path = "data/clinic.db"

    print("\n" + "=" * 60)
    print("DOCASSIST EMR - REPUTATION MANAGEMENT DEMO")
    print("=" * 60)
    print("\nThis demo showcases all reputation management features:")
    print("• Review Management")
    print("• Referral Tracking")
    print("• NPS Surveys")
    print("• Growth Recommendations")
    print("• Loyalty Program")

    # Run demos
    demo_review_management(db_path)
    demo_referral_tracking(db_path)
    demo_nps_tracking(db_path)
    demo_growth_recommendations(db_path)
    demo_loyalty_program(db_path)

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nAll reputation management features demonstrated successfully!")
    print("Check the README.md for detailed usage instructions.")
    print()


if __name__ == "__main__":
    main()
