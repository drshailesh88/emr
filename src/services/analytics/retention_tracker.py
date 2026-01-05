"""Track patient retention and follow-up compliance."""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import date, timedelta


@dataclass
class RetentionMetrics:
    """Patient retention metrics."""
    period: str
    total_patients: int
    active_patients: int  # Visited in period
    inactive_patients: int  # No visit in period
    retention_rate: float
    average_visits_per_patient: float
    follow_up_compliance_rate: float
    at_risk_patients: List[Dict]  # Patients who may leave


@dataclass
class FollowUpMetrics:
    """Follow-up compliance metrics."""
    scheduled_follow_ups: int
    completed_follow_ups: int
    missed_follow_ups: int
    compliance_rate: float
    average_days_to_follow_up: float
    overdue_patients: List[Dict]


class RetentionTracker:
    """Track patient retention and follow-up compliance."""

    def __init__(self, db_service):
        """Initialize retention tracker."""
        self.db = db_service

    def get_retention_metrics(
        self,
        period_months: int = 12,
        active_threshold_days: int = 180
    ) -> RetentionMetrics:
        """
        Calculate retention metrics.

        Args:
            period_months: Analysis period in months
            active_threshold_days: Days since last visit to consider active
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=period_months * 30)
        active_cutoff = end_date - timedelta(days=active_threshold_days)

        # Get all patients registered before period end
        all_patients = self._get_all_patients(end_date)
        total = len(all_patients)

        # Categorize as active or inactive
        active_patients = []
        inactive_patients = []
        at_risk_patients = []

        for patient in all_patients:
            last_visit = patient.get('last_visit_date')
            if last_visit and last_visit >= active_cutoff:
                active_patients.append(patient)
                # Check if at risk (visited but not recently)
                days_since = (end_date - last_visit).days
                if days_since > active_threshold_days // 2:
                    at_risk_patients.append({
                        'patient_id': patient.get('id'),
                        'name': patient.get('name'),
                        'last_visit': last_visit,
                        'days_since_visit': days_since,
                        'phone': patient.get('phone'),
                    })
            else:
                inactive_patients.append(patient)

        # Calculate metrics
        active_count = len(active_patients)
        retention_rate = (active_count / total * 100) if total > 0 else 0

        # Average visits per active patient
        total_visits = sum(p.get('visit_count', 0) for p in active_patients)
        avg_visits = total_visits / active_count if active_count > 0 else 0

        # Follow-up compliance
        follow_up_metrics = self.get_follow_up_metrics(period_months)

        return RetentionMetrics(
            period=f"Last {period_months} months",
            total_patients=total,
            active_patients=active_count,
            inactive_patients=len(inactive_patients),
            retention_rate=round(retention_rate, 1),
            average_visits_per_patient=round(avg_visits, 1),
            follow_up_compliance_rate=follow_up_metrics.compliance_rate,
            at_risk_patients=at_risk_patients[:20],  # Top 20 at risk
        )

    def get_follow_up_metrics(self, period_months: int = 3) -> FollowUpMetrics:
        """Calculate follow-up compliance metrics."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_months * 30)

        # Get visits with scheduled follow-ups
        visits_with_followup = self._get_visits_with_followup(start_date, end_date)

        scheduled = len(visits_with_followup)
        completed = 0
        missed = 0
        total_days = 0
        overdue_patients = []

        for visit in visits_with_followup:
            followup_date = visit.get('follow_up_date')
            actual_followup = visit.get('actual_followup_date')

            if actual_followup:
                completed += 1
                total_days += (actual_followup - visit.get('visit_date')).days
            elif followup_date and followup_date < end_date:
                missed += 1
                overdue_patients.append({
                    'patient_id': visit.get('patient_id'),
                    'name': visit.get('patient_name'),
                    'follow_up_date': followup_date,
                    'days_overdue': (end_date - followup_date).days,
                    'phone': visit.get('phone'),
                    'last_diagnosis': visit.get('diagnosis'),
                })

        compliance_rate = (completed / scheduled * 100) if scheduled > 0 else 100
        avg_days = total_days / completed if completed > 0 else 0

        # Sort overdue by days
        overdue_patients.sort(key=lambda x: x['days_overdue'], reverse=True)

        return FollowUpMetrics(
            scheduled_follow_ups=scheduled,
            completed_follow_ups=completed,
            missed_follow_ups=missed,
            compliance_rate=round(compliance_rate, 1),
            average_days_to_follow_up=round(avg_days, 1),
            overdue_patients=overdue_patients[:20],
        )

    def get_at_risk_patients(
        self,
        risk_threshold_days: int = 90
    ) -> List[Dict]:
        """
        Identify patients at risk of leaving the practice.

        Risk factors:
        - Haven't visited in a while
        - Missed follow-ups
        - Declining visit frequency
        """
        end_date = date.today()
        cutoff = end_date - timedelta(days=risk_threshold_days)

        # Get patients with chronic conditions who haven't visited
        chronic_conditions = ['diabetes', 'hypertension', 'cad', 'ckd', 'copd']
        at_risk = []

        all_patients = self._get_all_patients(end_date)

        for patient in all_patients:
            last_visit = patient.get('last_visit_date')
            conditions = patient.get('conditions', [])

            # Check risk factors
            risk_score = 0
            risk_reasons = []

            # Time since last visit
            if last_visit:
                days_since = (end_date - last_visit).days
                if days_since > risk_threshold_days:
                    risk_score += 2
                    risk_reasons.append(f"No visit in {days_since} days")
                elif days_since > risk_threshold_days // 2:
                    risk_score += 1
                    risk_reasons.append(f"Declining visit frequency")
            else:
                continue  # Never visited - skip

            # Chronic condition without recent visit
            has_chronic = any(c.lower() in str(conditions).lower() for c in chronic_conditions)
            if has_chronic and last_visit and (end_date - last_visit).days > 90:
                risk_score += 2
                risk_reasons.append("Chronic condition needs monitoring")

            # Missed follow-ups
            missed_followups = patient.get('missed_followups', 0)
            if missed_followups > 0:
                risk_score += missed_followups
                risk_reasons.append(f"Missed {missed_followups} follow-up(s)")

            # Add to at-risk if score is significant
            if risk_score >= 2:
                at_risk.append({
                    'patient_id': patient.get('id'),
                    'name': patient.get('name'),
                    'phone': patient.get('phone'),
                    'last_visit': last_visit,
                    'risk_score': risk_score,
                    'risk_reasons': risk_reasons,
                    'conditions': conditions,
                })

        # Sort by risk score
        at_risk.sort(key=lambda x: x['risk_score'], reverse=True)

        return at_risk[:50]  # Top 50 at-risk patients

    def get_win_back_opportunities(
        self,
        inactive_threshold_days: int = 180
    ) -> List[Dict]:
        """
        Identify inactive patients who could be won back.

        These are patients who:
        - Were regular visitors
        - Haven't visited in a while
        - Have ongoing conditions
        """
        end_date = date.today()
        inactive_since = end_date - timedelta(days=inactive_threshold_days)

        all_patients = self._get_all_patients(end_date)
        opportunities = []

        for patient in all_patients:
            last_visit = patient.get('last_visit_date')
            visit_count = patient.get('visit_count', 0)

            # Was regular (3+ visits) but now inactive
            if (last_visit and
                last_visit < inactive_since and
                visit_count >= 3):

                opportunities.append({
                    'patient_id': patient.get('id'),
                    'name': patient.get('name'),
                    'phone': patient.get('phone'),
                    'last_visit': last_visit,
                    'total_visits': visit_count,
                    'days_inactive': (end_date - last_visit).days,
                    'conditions': patient.get('conditions', []),
                    'recommended_action': self._get_winback_action(patient),
                })

        # Sort by recency (more recent = easier to win back)
        opportunities.sort(key=lambda x: x['days_inactive'])

        return opportunities[:30]

    def get_returning_patients(self) -> int:
        """Get count of patients with more than one visit."""
        return self.db.get_returning_patients() if self.db else 0

    def get_follow_up_compliance(self) -> float:
        """Get follow-up compliance rate."""
        # Follow-up tracking not fully implemented yet
        # Return a placeholder based on visits
        if not self.db:
            return 0.0

        follow_up_metrics = self.get_follow_up_metrics()
        return follow_up_metrics.compliance_rate

    def get_patient_churn(self, days: int = 180) -> List[Dict]:
        """Get patients not seen in specified days."""
        if not self.db:
            return []

        cutoff_date = date.today() - timedelta(days=days)
        all_patients = self.db.get_patient_visit_counts()

        churned = []
        for patient in all_patients:
            last_visit = patient.get('last_visit_date')
            visit_count = patient.get('visit_count', 0)

            # Only consider patients who have visited before
            if visit_count > 0 and last_visit:
                # Parse date if it's a string
                if isinstance(last_visit, str):
                    try:
                        last_visit = datetime.strptime(last_visit, '%Y-%m-%d').date()
                    except:
                        continue

                if last_visit < cutoff_date:
                    churned.append({
                        'patient_id': patient.get('id'),
                        'name': patient.get('name'),
                        'phone': patient.get('phone'),
                        'last_visit': last_visit,
                        'days_since_visit': (date.today() - last_visit).days,
                        'visit_count': visit_count,
                    })

        return churned

    def _get_all_patients(self, as_of_date: date) -> List[Dict]:
        """Get all patients as of a date."""
        if not self.db:
            return []

        # Use the existing method from database
        patients_stats = self.db.get_all_patients_with_stats(as_of_date)

        # Convert to expected format
        result = []
        for p in patients_stats:
            last_visit = p.get('last_visit_date')
            if isinstance(last_visit, str) and last_visit:
                try:
                    last_visit = datetime.strptime(last_visit, '%Y-%m-%d').date()
                except:
                    last_visit = None

            result.append({
                'id': p.get('id'),
                'name': p.get('name'),
                'phone': p.get('phone'),
                'created_at': p.get('created_at'),
                'visit_count': p.get('visit_count', 0),
                'last_visit_date': last_visit,
                'conditions': p.get('conditions', '').split(',') if p.get('conditions') else [],
                'missed_followups': 0,  # Not tracked yet
            })

        return result

    def _get_visits_with_followup(self, start: date, end: date) -> List[Dict]:
        """Get visits that had follow-up scheduled."""
        # Follow-up tracking not fully implemented yet
        # For now, return empty list
        return []

    def _get_winback_action(self, patient: Dict) -> str:
        """Get recommended action for winning back a patient."""
        conditions = patient.get('conditions', [])

        if any('diabetes' in str(c).lower() for c in conditions):
            return "Send reminder for diabetes monitoring (HbA1c due)"
        elif any('hypertension' in str(c).lower() for c in conditions):
            return "Send reminder for BP check"
        else:
            return "Send wellness check reminder"
