# Reputation Management Services

Comprehensive reputation and referral tracking for DocAssist EMR, designed for Indian clinic context.

## Overview

This module helps doctors grow their practice through:

- **Review Management**: Google Reviews, sentiment analysis, automated responses
- **Referral Tracking**: Patient and doctor referrals, ROI calculation
- **NPS Surveys**: Net Promoter Score tracking and detractor alerts
- **Growth Recommendations**: AI-powered actionable insights
- **Loyalty Program**: Patient engagement rewards and milestones

## Modules

### 1. Review Manager (`review_manager.py`)

Manages online reviews and patient feedback.

**Key Features:**
- Request reviews after positive visits via WhatsApp
- Sync reviews from Google Places API
- Sentiment analysis (positive/neutral/negative)
- Keyword extraction
- Template responses
- Review analytics and trends

**Usage:**
```python
from src.services.reputation import ReviewManager

rm = ReviewManager("data/clinic.db")

# Request review after visit
request = rm.request_review(
    patient_id=123,
    visit_id=456,
    google_review_link="https://g.page/r/..."
)

# Get analytics
analytics = rm.get_review_analytics(period_days=30)
print(f"Average Rating: {analytics.avg_rating}")
print(f"Total Reviews: {analytics.total_reviews}")
print(f"Trend: {analytics.trend:+.2f}")

# Get sentiment analysis
sentiment = rm.get_sentiment_analysis(period_days=30)
print(f"Positive: {sentiment.positive_count}")
print(f"Negative: {sentiment.negative_count}")
print(f"Top Issues: {sentiment.improvement_areas}")
```

### 2. Referral Tracker (`referral_tracker.py`)

Tracks how patients found your clinic and manages referrals.

**Key Features:**
- Track referral source (patient, doctor, Google, etc.)
- Calculate referral value (lifetime revenue)
- Top referrers leaderboard
- Thank you message automation
- Referral conversion funnel

**Usage:**
```python
from src.services.reputation import ReferralTracker, ReferralType

rt = ReferralTracker("data/clinic.db")

# Track new referral
rt.track_referral(
    patient_id=789,
    referral_type=ReferralType.PATIENT_REFERRAL,
    referrer_id=123,
    referrer_type='patient',
    referrer_name='Ram Lal'
)

# Get top referrers
top_referrers = rt.get_top_referrers(period_days=365, limit=10)
for referrer in top_referrers:
    print(f"{referrer.name}: {referrer.referral_count} referrals, "
          f"₹{referrer.total_value:.2f} value")

# Get stats
stats = rt.get_referral_stats(period_days=30)
print(f"Referral Rate: {stats.conversion_rate}%")
print(f"By Source: {stats.by_source}")
```

### 3. NPS Tracker (`nps_tracker.py`)

Measures patient satisfaction using Net Promoter Score.

**Key Features:**
- Send NPS surveys via WhatsApp
- 0-10 rating scale
- Categorize: Promoters (9-10), Passives (7-8), Detractors (0-6)
- Detractor alerts for immediate follow-up
- NPS trend over time
- Feedback theme analysis

**Usage:**
```python
from src.services.reputation import NPSTracker

nps = NPSTracker("data/clinic.db")

# Send survey
survey = nps.send_nps_survey(patient_id=123)

# Record response
response = nps.record_response(
    survey_id=survey.id,
    score=9,
    feedback="Great experience, very caring doctor"
)

# Calculate NPS
score = nps.calculate_nps(period_days=30)
print(f"NPS Score: {score.score:.1f}")
print(f"Promoters: {score.promoters}, Detractors: {score.detractors}")

# Get detractor alerts
alerts = nps.get_detractor_alerts(days=7)
for alert in alerts:
    print(f"⚠️ {alert.patient_name} gave {alert.score}/10")
    print(f"   Feedback: {alert.feedback}")
```

### 4. Growth Recommendations (`growth_recommendations.py`)

Analyzes practice data and provides actionable growth insights.

**Key Features:**
- Automated practice analysis
- Benchmark comparison
- Priority-based recommendations
- Impact assessment
- Quick wins identification

**Usage:**
```python
from src.services.reputation import GrowthRecommendations

gr = GrowthRecommendations("data/clinic.db")

# Get all recommendations
recommendations = gr.analyze_practice(period_days=30)

for rec in recommendations:
    print(f"{rec.priority.value.upper()}: {rec.title}")
    print(f"   {rec.description}")
    print(f"   Action: {rec.action}")
    print()

# Get quick wins
quick_wins = gr.get_quick_wins(period_days=30)

# Get benchmark comparison
benchmarks = gr.get_competitor_benchmark(specialty="Cardiology")
for bm in benchmarks:
    status_emoji = "✅" if bm.status == 'above' else "⚠️"
    print(f"{status_emoji} {bm.metric_name}: {bm.your_value} "
          f"(benchmark: {bm.benchmark_value}, {bm.percentile}th percentile)")
```

### 5. Loyalty Program (`loyalty_program.py`)

Tracks patient engagement and rewards loyalty.

**Key Features:**
- Automatic enrollment on first visit
- Tier system: Bronze → Silver → Gold → Platinum
- Points for visits, spending, referrals
- Milestone tracking (1 year, 10th visit, etc.)
- Rewards (discounts, priority booking, free checkups)

**Tier Thresholds:**
- **Bronze**: 0-3 visits
- **Silver**: 4-10 visits
- **Gold**: 11+ visits OR 2+ referrals
- **Platinum**: 25+ visits AND 5+ referrals

**Usage:**
```python
from src.services.reputation import LoyaltyProgram

lp = LoyaltyProgram("data/clinic.db")

# Enroll patient (auto on first visit)
member = lp.enroll_patient(patient_id=123)

# Record visit
lp.record_visit(patient_id=123, visit_value=500.0)

# Get member details
member = lp.get_member(patient_id=123)
print(f"Tier: {member.tier.value}")
print(f"Points: {member.points}")
print(f"Visits: {member.total_visits}")

# Get rewards
rewards = lp.get_rewards(patient_id=123, active_only=True)
for reward in rewards:
    print(f"🎁 {reward.title}")
    print(f"   {reward.description}")

# Record referral
lp.record_referral(patient_id=123)
```

## Integration with WhatsApp

All services integrate with WhatsApp for automated communication:

```python
from src.services.whatsapp import WhatsAppService

whatsapp = WhatsAppService()

# Send review request
request = review_manager.request_review(patient_id=123, visit_id=456)
message = f"""
Dear {patient_name},

Thank you for visiting us today! We hope you had a great experience.

We'd be grateful if you could spare a moment to review us on Google:
{request.review_link}

Your feedback helps us serve you better.

- Dr. {doctor_name}
"""
whatsapp.send_message(patient_phone, message)
review_manager.mark_request_sent(request.id, message_id)

# Send NPS survey
survey = nps_tracker.send_nps_survey(patient_id=123)
message = f"""
Dear {patient_name},

On a scale of 0-10, how likely are you to recommend our clinic to friends?

Reply with a number from 0 (not likely) to 10 (very likely).

We value your honest feedback!
"""
whatsapp.send_message(patient_phone, message)

# Send thank you to referrer
message = f"""
Dear {referrer_name},

Thank you so much for referring {new_patient_name} to us! 🙏

Your trust means the world to us. As a token of appreciation,
you've earned 50 loyalty points and a 10% discount on your next visit.

- Dr. {doctor_name}
"""
whatsapp.send_message(referrer_phone, message)
```

## Database Schema

All services use SQLite with the following tables:

### Reviews
- `reviews`: Review details, ratings, sentiment
- `review_requests`: Review request tracking

### Referrals
- `referrals`: Referral source tracking
- `referral_thank_you`: Thank you message tracking

### NPS
- `nps_surveys`: Survey status
- `nps_responses`: Patient responses

### Loyalty
- `loyalty_members`: Member tier and points
- `loyalty_rewards`: Available rewards
- `loyalty_milestones`: Achievement tracking

## Best Practices

### Review Management
1. **Request after positive visits only** - Check for no complaints
2. **Respond to all reviews within 24 hours** - Shows you care
3. **Address negative reviews personally** - Call detractors
4. **Thank positive reviewers** - Reinforce good behavior

### Referral Tracking
1. **Always thank referrers** - Within 48 hours
2. **Track source at registration** - Ask "How did you find us?"
3. **Calculate ROI** - Know your best referral sources
4. **Reward top referrers** - Special recognition

### NPS Surveys
1. **Send after 2-3 visits** - Not on first visit
2. **Follow up with detractors immediately** - Within 24 hours
3. **Don't over-survey** - Max once per 30 days
4. **Act on feedback** - Show you're listening

### Loyalty Program
1. **Auto-enroll everyone** - No opt-in friction
2. **Make tiers achievable** - Don't set bars too high
3. **Communicate rewards clearly** - Patients should know benefits
4. **Expire rewards appropriately** - 90 days for discounts

## Performance Considerations

- All database queries use indexes for fast lookups
- Batch operations where possible
- Cache analytics results (TTL: 1 hour)
- Async processing for WhatsApp messages

## Privacy & Compliance

- All patient data encrypted at rest
- No PII sent to external services without consent
- Google Reviews sync uses business account only
- Opt-out mechanism for all communications
- GDPR-compliant data retention policies

## Future Enhancements

- [ ] Practo/Justdial review sync
- [ ] SMS fallback for WhatsApp
- [ ] Multi-language support (Hindi, Tamil, etc.)
- [ ] Automated detractor follow-up workflows
- [ ] Referral reward points redemption
- [ ] Integration with practice management dashboard
- [ ] Predictive churn analysis
- [ ] Competitive benchmarking API

## Support

For questions or issues, contact the development team or refer to the main DocAssist EMR documentation.
