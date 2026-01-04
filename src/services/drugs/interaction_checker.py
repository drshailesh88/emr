"""Drug-drug and drug-disease interaction checking"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Tuple
import json
from pathlib import Path

class Severity(Enum):
    CRITICAL = "critical"    # Block prescription, life-threatening
    MAJOR = "major"          # Strong warning, serious harm possible
    MODERATE = "moderate"    # Caution, monitoring needed
    MINOR = "minor"          # Informational

@dataclass
class Interaction:
    drug1: str
    drug2: str
    severity: Severity
    mechanism: str
    clinical_effect: str
    management: str
    evidence_level: str  # high, moderate, low

@dataclass
class Alert:
    alert_type: str  # interaction, contraindication, allergy, dose, duplicate
    severity: Severity
    title: str
    message: str
    details: Dict
    alternatives: List[str]
    can_override: bool
    override_requires_reason: bool

class InteractionChecker:
    """Check drug-drug and drug-disease interactions"""

    def __init__(self, data_path: str = "data/interactions"):
        self.interactions: Dict[Tuple[str, str], Interaction] = {}
        self.contraindications: Dict[Tuple[str, str], dict] = {}  # (drug, condition)
        self.cross_allergies: Dict[str, List[str]] = {}  # drug class -> cross-reactive classes
        self.drug_classes: Dict[str, str] = {}  # drug -> class
        self._load_data(data_path)

    def _load_data(self, data_path: str):
        """Load interaction data"""
        try:
            # Load drug-drug interactions
            interactions_file = Path(data_path) / "common_interactions.json"
            if interactions_file.exists():
                with open(interactions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for interaction_data in data.get('interactions', []):
                    drug1 = interaction_data['drug1'].lower()
                    drug2 = interaction_data['drug2'].lower()

                    severity_map = {
                        'critical': Severity.CRITICAL,
                        'major': Severity.MAJOR,
                        'moderate': Severity.MODERATE,
                        'minor': Severity.MINOR
                    }
                    severity = severity_map.get(
                        interaction_data['severity'].lower(),
                        Severity.MODERATE
                    )

                    interaction = Interaction(
                        drug1=drug1,
                        drug2=drug2,
                        severity=severity,
                        mechanism=interaction_data.get('mechanism', ''),
                        clinical_effect=interaction_data.get('clinical_effect', ''),
                        management=interaction_data.get('management', ''),
                        evidence_level=interaction_data.get('evidence', 'moderate')
                    )

                    # Store both directions
                    self.interactions[(drug1, drug2)] = interaction
                    self.interactions[(drug2, drug1)] = interaction

            # Load contraindications
            contraindications_file = Path(data_path) / "contraindications.json"
            if contraindications_file.exists():
                with open(contraindications_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for contra in data.get('contraindications', []):
                    drug = contra['drug'].lower()
                    condition = contra['condition'].lower()
                    self.contraindications[(drug, condition)] = {
                        'severity': contra.get('severity', 'major'),
                        'reason': contra.get('reason', ''),
                        'alternatives': contra.get('alternatives', [])
                    }

            # Load cross-allergies
            allergies_file = Path(data_path) / "cross_allergies.json"
            if allergies_file.exists():
                with open(allergies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cross_allergies = data.get('cross_allergies', {})

            # Load drug classes
            classes_file = Path(data_path) / "drug_classes.json"
            if classes_file.exists():
                with open(classes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.drug_classes = data.get('drug_classes', {})

            print(f"Loaded {len(self.interactions)} interactions")

        except Exception as e:
            print(f"Error loading interaction data: {e}")

    def check_pair(self, drug1: str, drug2: str) -> Optional[Interaction]:
        """Check interaction between two drugs"""
        key = (drug1.lower(), drug2.lower())
        return self.interactions.get(key)

    def check_prescription(self,
                          new_drugs: List[str],
                          current_drugs: List[str],
                          patient_conditions: List[str],
                          patient_allergies: List[str],
                          patient_age: int,
                          patient_gender: str,
                          patient_pregnant: bool = False,
                          patient_lactating: bool = False,
                          creatinine: Optional[float] = None,
                          egfr: Optional[float] = None) -> List[Alert]:
        """
        Comprehensive prescription checking.

        Returns alerts for:
        - Drug-drug interactions
        - Drug-disease contraindications
        - Allergy conflicts (including cross-reactivity)
        - Duplicate therapy (same drug class)
        - Pregnancy/lactation concerns
        - Age-related concerns (pediatric/geriatric)
        """
        alerts = []
        all_drugs = new_drugs + current_drugs

        # Check drug-drug interactions
        for i, drug1 in enumerate(new_drugs):
            for drug2 in all_drugs[i+1:]:
                interaction = self.check_pair(drug1, drug2)
                if interaction:
                    alerts.append(Alert(
                        alert_type="interaction",
                        severity=interaction.severity,
                        title=f"Drug Interaction: {drug1.title()} + {drug2.title()}",
                        message=interaction.clinical_effect,
                        details={
                            'mechanism': interaction.mechanism,
                            'management': interaction.management,
                            'evidence': interaction.evidence_level
                        },
                        alternatives=[],
                        can_override=(interaction.severity != Severity.CRITICAL),
                        override_requires_reason=True
                    ))

        # Check allergies
        for drug in new_drugs:
            allergy_alert = self.check_allergy(drug, patient_allergies)
            if allergy_alert:
                alerts.append(allergy_alert)

        # Check contraindications
        for drug in new_drugs:
            for condition in patient_conditions:
                contra_alert = self.check_contraindication(drug, condition)
                if contra_alert:
                    alerts.append(contra_alert)

        # Check duplicate therapy
        duplicate_alerts = self.check_duplicate_therapy(all_drugs)
        alerts.extend(duplicate_alerts)

        # Check pregnancy/lactation
        if patient_pregnant:
            for drug in new_drugs:
                # Placeholder - would need pregnancy category data
                if drug.lower() in ['warfarin', 'atorvastatin', 'ace inhibitor']:
                    alerts.append(Alert(
                        alert_type="pregnancy",
                        severity=Severity.CRITICAL,
                        title=f"Pregnancy Contraindication: {drug.title()}",
                        message=f"{drug.title()} is contraindicated in pregnancy",
                        details={'category': 'X', 'risk': 'Teratogenic effects'},
                        alternatives=[],
                        can_override=False,
                        override_requires_reason=True
                    ))

        # Check renal dosing
        if egfr and egfr < 60:
            for drug in new_drugs:
                if drug.lower() in ['metformin', 'digoxin', 'gabapentin']:
                    alerts.append(Alert(
                        alert_type="renal",
                        severity=Severity.MAJOR,
                        title=f"Renal Dose Adjustment Needed: {drug.title()}",
                        message=f"eGFR {egfr:.1f} - dose adjustment required",
                        details={'egfr': egfr},
                        alternatives=[],
                        can_override=True,
                        override_requires_reason=True
                    ))

        # Check geriatric concerns
        if patient_age >= 65:
            beers_criteria = ['diazepam', 'diphenhydramine', 'amitriptyline']
            for drug in new_drugs:
                if drug.lower() in beers_criteria:
                    alerts.append(Alert(
                        alert_type="geriatric",
                        severity=Severity.MODERATE,
                        title=f"Potentially Inappropriate in Elderly: {drug.title()}",
                        message=f"Consider alternative - Beers Criteria",
                        details={'age': patient_age},
                        alternatives=[],
                        can_override=True,
                        override_requires_reason=False
                    ))

        return sorted(alerts, key=lambda a: list(Severity).index(a.severity))

    def check_allergy(self, drug: str, allergies: List[str]) -> Optional[Alert]:
        """Check if drug is contraindicated due to allergies"""
        drug_lower = drug.lower()

        # Direct allergy match
        if drug_lower in [a.lower() for a in allergies]:
            return Alert(
                alert_type="allergy",
                severity=Severity.CRITICAL,
                title=f"Allergy Alert: {drug.title()}",
                message=f"Patient has documented allergy to {drug}",
                details={'allergen': drug},
                alternatives=[],
                can_override=False,
                override_requires_reason=True
            )

        # Check cross-allergies
        drug_class = self.drug_classes.get(drug_lower, '')
        if drug_class:
            for allergy in allergies:
                allergy_class = self.drug_classes.get(allergy.lower(), '')
                if allergy_class and allergy_class in self.cross_allergies.get(drug_class, []):
                    return Alert(
                        alert_type="cross_allergy",
                        severity=Severity.MAJOR,
                        title=f"Cross-Allergy Risk: {drug.title()}",
                        message=f"Patient allergic to {allergy} - possible cross-reactivity",
                        details={'related_allergen': allergy, 'risk': 'cross-reactivity'},
                        alternatives=[],
                        can_override=True,
                        override_requires_reason=True
                    )

        return None

    def check_contraindication(self, drug: str, condition: str) -> Optional[Alert]:
        """Check if drug is contraindicated for a condition"""
        key = (drug.lower(), condition.lower())
        contra = self.contraindications.get(key)

        if contra:
            severity_map = {
                'critical': Severity.CRITICAL,
                'major': Severity.MAJOR,
                'moderate': Severity.MODERATE,
                'minor': Severity.MINOR
            }
            severity = severity_map.get(contra['severity'], Severity.MAJOR)

            return Alert(
                alert_type="contraindication",
                severity=severity,
                title=f"Contraindication: {drug.title()} in {condition.title()}",
                message=contra['reason'],
                details={'condition': condition},
                alternatives=contra.get('alternatives', []),
                can_override=(severity != Severity.CRITICAL),
                override_requires_reason=True
            )

        return None

    def check_duplicate_therapy(self, drugs: List[str]) -> List[Alert]:
        """Check for duplicate therapy (same drug class)"""
        alerts = []
        class_counts = {}

        for drug in drugs:
            drug_class = self.drug_classes.get(drug.lower(), '')
            if drug_class:
                if drug_class not in class_counts:
                    class_counts[drug_class] = []
                class_counts[drug_class].append(drug)

        for drug_class, drug_list in class_counts.items():
            if len(drug_list) > 1:
                alerts.append(Alert(
                    alert_type="duplicate",
                    severity=Severity.MODERATE,
                    title=f"Duplicate Therapy: {drug_class.title()}",
                    message=f"Multiple {drug_class}s prescribed: {', '.join(drug_list)}",
                    details={'drug_class': drug_class, 'drugs': drug_list},
                    alternatives=[],
                    can_override=True,
                    override_requires_reason=True
                ))

        return alerts

    def get_alternatives(self, drug: str, indication: str, avoid_interactions_with: List[str] = None) -> List[str]:
        """Suggest safe alternatives for a problematic drug"""
        # Placeholder - would need comprehensive alternative database
        alternatives = {
            'metformin': ['glimepiride', 'sitagliptin', 'empagliflozin'],
            'amlodipine': ['telmisartan', 'enalapril', 'metoprolol'],
            'atorvastatin': ['rosuvastatin', 'fenofibrate'],
        }

        drug_alternatives = alternatives.get(drug.lower(), [])

        # Filter out alternatives that also have interactions
        if avoid_interactions_with:
            safe_alternatives = []
            for alt in drug_alternatives:
                has_interaction = False
                for existing_drug in avoid_interactions_with:
                    if self.check_pair(alt, existing_drug):
                        has_interaction = True
                        break
                if not has_interaction:
                    safe_alternatives.append(alt)
            return safe_alternatives

        return drug_alternatives
