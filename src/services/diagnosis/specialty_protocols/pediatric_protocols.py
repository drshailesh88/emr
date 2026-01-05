"""
Pediatric Clinical Protocols

Evidence-based protocols for common pediatric conditions in Indian practice.
Based on IAP (Indian Academy of Pediatrics), WHO, IMNCI guidelines.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date, timedelta
from ..protocol_engine import (
    TreatmentProtocol,
    Medication,
    DrugRoute,
    ComplianceReport,
    ComplianceIssue,
)


@dataclass
class RedFlag:
    """Pediatric red flag warning."""
    symptom: str
    urgency: str  # EMERGENCY, URGENT, MONITOR
    action: str
    age_specific: bool = False


@dataclass
class GrowthAssessment:
    """Child growth assessment result."""
    weight_for_age: str  # Normal, Underweight, Severely Underweight
    height_for_age: str  # Normal, Stunted
    weight_for_height: str  # Normal, Wasted, Severely Wasted
    nutritional_status: str  # Normal, MAM, SAM
    recommendations: List[str]


class PediatricProtocols:
    """
    Pediatric-specific treatment protocols.

    Implements evidence-based management for:
    - Acute Gastroenteritis (WHO ORS protocol)
    - Pneumonia (IMNCI guidelines)
    - Fever in children
    - Growth monitoring
    - India National Immunization Schedule
    """

    def __init__(self):
        """Initialize pediatric protocols."""
        self._load_protocols()

    def _load_protocols(self) -> None:
        """Load pediatric-specific protocols."""
        self.protocols = {
            "acute_gastroenteritis": self._gastroenteritis_protocol(),
            "pneumonia_infant": self._pneumonia_infant_protocol(),
            "pneumonia_child": self._pneumonia_child_protocol(),
            "fever_child": self._fever_child_protocol(),
            "dengue_pediatric": self._dengue_pediatric_protocol(),
            "bronchiolitis": self._bronchiolitis_protocol(),
            "croup": self._croup_protocol(),
            "asthma_pediatric": self._asthma_pediatric_protocol(),
        }

    def _gastroenteritis_protocol(self) -> TreatmentProtocol:
        """Acute Gastroenteritis - WHO ORS protocol (India-specific)."""
        return TreatmentProtocol(
            diagnosis="Acute Gastroenteritis (Pediatric)",
            icd10_code="A09",
            first_line_drugs=[
                Medication(
                    drug_name="ORS (WHO formula)",
                    generic_name="Oral Rehydration Solution",
                    strength="sachets",
                    form="powder for solution",
                    dose="Plan A/B/C based on dehydration",
                    frequency="frequent sips",
                    duration="until diarrhea stops",
                    instructions="""
                    Plan A (No dehydration): 50-100ml after each loose stool
                    Plan B (Some dehydration): 75ml/kg over 4 hours
                    Plan C (Severe): IV rehydration, refer
                    """,
                    indication="Cornerstone of treatment",
                ),
                Medication(
                    drug_name="Zinc sulfate",
                    generic_name="Zinc",
                    strength="20mg",
                    form="dispersible tablet",
                    dose="20mg for >6 months, 10mg for <6 months",
                    frequency="OD",
                    duration="14 days",
                    instructions="dissolve in water or breast milk",
                    indication="Reduces duration and severity (IAP/WHO recommendation)",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Ondansetron",
                    generic_name="Ondansetron",
                    strength="2mg",
                    form="syrup",
                    dose="0.15mg/kg (max 8mg)",
                    frequency="single dose",
                    indication="Only if severe vomiting preventing ORS intake",
                ),
            ],
            investigations=[
                "Usually clinical diagnosis",
                "Stool R/M if >7 days or bloody",
                "Stool C/S if dysentery",
                "Electrolytes if severe dehydration or IV fluids needed",
            ],
            monitoring=[
                "Hydration status (skin turgor, mucous membranes, urine output)",
                "Weight (every visit)",
                "Stool frequency and consistency",
                "Signs of severe dehydration (sunken eyes, lethargy)",
            ],
            lifestyle_advice=[
                "CONTINUE BREASTFEEDING (critical in infants)",
                "Continue age-appropriate diet (avoid starvation)",
                "Give extra fluids",
                "Avoid fruit juices (high osmolarity worsens diarrhea)",
                "Hand hygiene",
                "Safe water and food",
            ],
            follow_up_interval="Only if worsening or >5 days",
            referral_criteria=[
                "Severe dehydration (Plan C)",
                "Intractable vomiting",
                "Bloody diarrhea with high fever",
                "Age <2 months",
                "Suspected cholera outbreak",
                "Signs of shock",
            ],
            contraindications={
                "antibiotics": ["NOT indicated for routine AGE", "Only if dysentery or cholera"],
                "antiemetics": ["Avoid unless preventing ORS intake"],
                "antidiarrheals": ["CONTRAINDICATED in children"],
            },
        )

    def _pneumonia_infant_protocol(self) -> TreatmentProtocol:
        """Pneumonia in infants (<2 months) - IMNCI guidelines."""
        return TreatmentProtocol(
            diagnosis="Pneumonia (Infant <2 months)",
            icd10_code="J18.9",
            first_line_drugs=[
                # All infants <2 months with pneumonia should be referred
                Medication(
                    drug_name="REFER TO HOSPITAL",
                    generic_name="N/A",
                    strength="",
                    form="",
                    dose="",
                    frequency="",
                    indication="All infants <2 months with pneumonia need hospitalization",
                ),
            ],
            investigations=[
                "Respiratory rate (>60/min = pneumonia in infants)",
                "SpO2",
                "Chest X-ray (in hospital)",
                "CBC, CRP",
            ],
            monitoring=[
                "Respiratory rate every 4 hours",
                "SpO2 continuous",
                "Signs of severe pneumonia (chest indrawing, cyanosis, grunting)",
            ],
            lifestyle_advice=[
                "Keep warm",
                "Continue breastfeeding",
                "Head elevation",
            ],
            follow_up_interval="N/A - hospitalize",
            referral_criteria=[
                "ALL infants <2 months with pneumonia",
                "Fast breathing (RR >60)",
                "Chest indrawing",
                "Danger signs (lethargic, not feeding)",
            ],
        )

    def _pneumonia_child_protocol(self) -> TreatmentProtocol:
        """Pneumonia in children (2 months - 5 years) - IMNCI."""
        return TreatmentProtocol(
            diagnosis="Pneumonia (Child 2m-5y)",
            icd10_code="J18.9",
            first_line_drugs=[
                # High-dose amoxicillin (India IMNCI protocol)
                Medication(
                    drug_name="Amoxicillin (HIGH DOSE)",
                    generic_name="Amoxicillin",
                    strength="250mg/5ml",
                    form="syrup",
                    dose="80-90 mg/kg/day divided TDS",
                    frequency="TDS",
                    duration="5 days",
                    instructions="""
                    Weight-based dosing:
                    <5kg: 2.5ml TDS
                    5-10kg: 5ml TDS
                    10-15kg: 10ml TDS
                    >15kg: 15ml TDS (or tablet 500mg TDS)
                    """,
                    indication="First-line for pneumonia (IAP high-dose protocol)",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Amoxicillin-Clavulanate",
                    generic_name="Amoxicillin-Clavulanate",
                    strength="400mg/5ml",
                    form="syrup",
                    dose="Same as amoxicillin dosing",
                    frequency="TDS",
                    duration="5-7 days",
                    indication="If failure after 48h or severe pneumonia",
                ),
                Medication(
                    drug_name="Ceftriaxone",
                    generic_name="Ceftriaxone",
                    strength="250mg",
                    form="injection",
                    dose="50-75mg/kg/day",
                    frequency="OD-BD",
                    route=DrugRoute.IV,
                    indication="Severe pneumonia, hospitalized",
                ),
            ],
            investigations=[
                "Respiratory rate (key diagnostic criterion)",
                "SpO2",
                "Chest X-ray (if severe or not improving)",
                "CBC if severe",
            ],
            monitoring=[
                "Respiratory rate q4-6h",
                "Danger signs (chest indrawing, inability to drink, convulsions)",
                "Response to treatment (should improve in 48h)",
            ],
            lifestyle_advice=[
                "Continue breastfeeding/feeding",
                "Increase fluids",
                "Keep warm",
                "Clear nasal secretions",
                "Head elevation while sleeping",
            ],
            follow_up_interval="48 hours (critical reassessment)",
            referral_criteria=[
                "Severe pneumonia (chest indrawing, SpO2 <92%)",
                "Danger signs (unable to drink, convulsions, lethargy)",
                "Age <2 months",
                "No improvement in 48-72h",
                "Worsening",
            ],
            contraindications={
                "macrolides_monotherapy": ["Not first-line in children (resistance in India)"],
            },
        )

    def _fever_child_protocol(self) -> TreatmentProtocol:
        """Fever in children - India-specific (dengue/malaria endemic)."""
        return TreatmentProtocol(
            diagnosis="Fever (Child)",
            icd10_code="R50.9",
            first_line_drugs=[
                Medication(
                    drug_name="Paracetamol",
                    generic_name="Paracetamol",
                    strength="250mg/5ml",
                    form="syrup",
                    dose="15 mg/kg/dose",
                    frequency="TDS-QID (6-8 hourly)",
                    duration="as needed",
                    instructions="""
                    Weight-based dosing (15mg/kg):
                    5kg: 2.5ml (150mg)
                    10kg: 5ml (250mg)
                    15kg: 7.5ml (375mg)
                    20kg: 10ml (500mg)
                    Max: 75mg/kg/day or 4g/day
                    """,
                    indication="Antipyretic (ONLY safe option in children)",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Ibuprofen",
                    generic_name="Ibuprofen",
                    strength="100mg/5ml",
                    form="syrup",
                    dose="10 mg/kg/dose",
                    frequency="TDS (8 hourly)",
                    instructions="ONLY if dengue ruled out",
                    indication="Alternative if paracetamol ineffective (NOT in dengue)",
                ),
            ],
            investigations=[
                "ALWAYS consider malaria/dengue in endemic areas",
                "CBC with platelet count (dengue screening)",
                "Peripheral smear (malaria)",
                "Dengue NS1/IgM (if platelets low or day 3-7)",
                "Urine R/M (UTI)",
                "Blood culture if high fever >5 days",
            ],
            monitoring=[
                "Temperature trend",
                "Hydration status",
                "Activity level (lethargy is red flag)",
                "Rash (dengue, measles, scarlet fever)",
                "Bleeding manifestations (dengue)",
                "Platelet count if dengue suspected",
            ],
            lifestyle_advice=[
                "Tepid sponging (NOT cold water)",
                "Adequate fluids (ORS, coconut water)",
                "Light clothing",
                "Rest",
                "Monitor urine output",
            ],
            follow_up_interval="48 hours or immediately if danger signs",
            referral_criteria=[
                "Age <3 months with fever >38°C",
                "Toxic appearance, lethargy",
                "Fever >5 days",
                "Petechial rash or bleeding",
                "Severe headache, neck stiffness (meningitis)",
                "Seizures",
                "Respiratory distress",
            ],
            contraindications={
                "aspirin": ["NEVER in children (Reye syndrome risk)"],
                "nsaids": ["Avoid in dengue (bleeding risk)"],
            },
        )

    def _dengue_pediatric_protocol(self) -> TreatmentProtocol:
        """Dengue fever - Pediatric protocol."""
        return TreatmentProtocol(
            diagnosis="Dengue Fever (Pediatric)",
            icd10_code="A90",
            first_line_drugs=[
                Medication(
                    drug_name="Paracetamol ONLY",
                    generic_name="Paracetamol",
                    strength="250mg/5ml",
                    form="syrup",
                    dose="15 mg/kg/dose",
                    frequency="QID (every 6 hours)",
                    duration="as needed",
                    instructions="AVOID NSAIDs/Aspirin (bleeding risk)",
                    indication="Antipyretic",
                ),
            ],
            investigations=[
                "NS1 antigen (days 1-5)",
                "Dengue IgM/IgG (after day 5)",
                "CBC with platelet count (DAILY during critical phase)",
                "Hematocrit (q12h in critical phase days 3-7)",
                "LFT (ALT/AST often elevated)",
            ],
            monitoring=[
                "Critical phase: Days 3-7 (when fever subsides)",
                "Warning signs: Abdominal pain, persistent vomiting, bleeding",
                "Platelet count daily",
                "Hematocrit q12h (hemoconcentration indicates plasma leakage)",
                "Urine output (oliguria is danger sign)",
                "Vitals q4h",
            ],
            lifestyle_advice=[
                "Aggressive oral hydration (ORS, coconut water, soups)",
                "Complete bed rest",
                "Avoid NSAIDs/Aspirin",
                "Mosquito bite prevention",
                "Watch for warning signs (especially days 3-7)",
            ],
            follow_up_interval="Daily during fever, CRITICAL PHASE monitoring days 3-7",
            referral_criteria=[
                "Warning signs (severe abdominal pain, persistent vomiting, bleeding)",
                "Platelet <50,000",
                "Hematocrit rise >20%",
                "Severe plasma leakage (ascites, pleural effusion)",
                "Shock (cold extremities, narrow pulse pressure)",
                "Age <1 year (higher risk)",
            ],
        )

    def _bronchiolitis_protocol(self) -> TreatmentProtocol:
        """Bronchiolitis (typically RSV) - supportive care."""
        return TreatmentProtocol(
            diagnosis="Bronchiolitis (Infant <2 years)",
            icd10_code="J21.9",
            first_line_drugs=[
                Medication(
                    drug_name="Supportive care ONLY",
                    generic_name="N/A",
                    strength="",
                    form="",
                    dose="",
                    frequency="",
                    instructions="NO proven medications",
                    indication="Self-limiting viral illness",
                ),
            ],
            second_line_drugs=[
                # These are NOT recommended routinely but commonly used
                Medication(
                    drug_name="Salbutamol (trial)",
                    generic_name="Salbutamol",
                    strength="2.5mg",
                    form="nebulization",
                    dose="2.5mg in 2ml NS",
                    frequency="Trial dose, continue only if response",
                    indication="NOT evidence-based, but can trial",
                ),
            ],
            investigations=[
                "Usually clinical diagnosis",
                "SpO2 monitoring",
                "Chest X-ray if severe (to rule out pneumonia)",
                "Nasal swab for RSV (if available, not essential)",
            ],
            monitoring=[
                "Respiratory rate, work of breathing",
                "SpO2",
                "Feeding ability (key marker)",
                "Hydration status",
            ],
            lifestyle_advice=[
                "Frequent small feeds",
                "Nasal saline drops + suction (very helpful)",
                "Head elevation",
                "Avoid smoke exposure",
                "Humidified air",
            ],
            follow_up_interval="24-48 hours",
            referral_criteria=[
                "SpO2 <92%",
                "Severe respiratory distress (indrawing, grunting)",
                "Unable to feed",
                "Age <3 months",
                "Apnea episodes",
            ],
        )

    def _croup_protocol(self) -> TreatmentProtocol:
        """Croup (laryngotracheobronchitis) protocol."""
        return TreatmentProtocol(
            diagnosis="Croup (Laryngotracheobronchitis)",
            icd10_code="J05.0",
            first_line_drugs=[
                Medication(
                    drug_name="Dexamethasone",
                    generic_name="Dexamethasone",
                    strength="4mg/ml",
                    form="injection/syrup",
                    dose="0.6 mg/kg (single dose)",
                    frequency="STAT, repeat after 12h if severe",
                    route=DrugRoute.ORAL,
                    instructions="oral preferred over IM",
                    indication="Reduces inflammation, proven benefit",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Nebulized Adrenaline",
                    generic_name="Adrenaline",
                    strength="1:1000",
                    form="nebulization",
                    dose="0.5ml/kg (max 5ml) in NS",
                    frequency="single dose",
                    route=DrugRoute.INHALED,
                    indication="Severe croup only (stridor at rest)",
                ),
            ],
            investigations=["Clinical diagnosis (barking cough, stridor)"],
            monitoring=[
                "Stridor (at rest vs with agitation)",
                "Respiratory distress",
                "SpO2",
            ],
            lifestyle_advice=[
                "Humidified air (steam inhalation)",
                "Keep child calm (agitation worsens)",
                "Adequate hydration",
            ],
            follow_up_interval="If mild: 24-48h. If severe: hospital",
            referral_criteria=[
                "Stridor at rest",
                "Severe respiratory distress",
                "Hypoxia (SpO2 <92%)",
                "Age <6 months",
                "Drooling (suggests epiglottitis, not croup)",
            ],
        )

    def _asthma_pediatric_protocol(self) -> TreatmentProtocol:
        """Pediatric asthma protocol."""
        return TreatmentProtocol(
            diagnosis="Bronchial Asthma (Pediatric)",
            icd10_code="J45.9",
            first_line_drugs=[
                # Reliever
                Medication(
                    drug_name="Salbutamol",
                    generic_name="Salbutamol",
                    strength="100mcg",
                    form="MDI with spacer",
                    dose="2-4 puffs",
                    frequency="QID or SOS",
                    route=DrugRoute.INHALED,
                    instructions="MUST use spacer (better delivery)",
                    indication="Reliever (rescue medication)",
                ),
                # Controller (if persistent asthma)
                Medication(
                    drug_name="Budesonide",
                    generic_name="Budesonide",
                    strength="200mcg",
                    form="MDI with spacer",
                    dose="1-2 puffs",
                    frequency="BD",
                    route=DrugRoute.INHALED,
                    instructions="rinse mouth after, use spacer",
                    indication="Controller (inhaled corticosteroid)",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Montelukast",
                    generic_name="Montelukast",
                    strength="4mg (2-5y), 5mg (6-14y)",
                    form="chewable tablet",
                    dose="1",
                    frequency="HS (bedtime)",
                    indication="Leukotriene modifier, add-on therapy",
                ),
            ],
            investigations=[
                "Peak flow monitoring (if >5 years)",
                "Spirometry (if >5 years)",
                "Chest X-ray (baseline)",
                "Allergy testing if indicated",
            ],
            monitoring=[
                "Symptom diary",
                "Peak flow diary (if >5 years)",
                "Inhaler technique at every visit",
                "Growth monitoring (steroids can affect)",
                "Exacerbation frequency",
            ],
            lifestyle_advice=[
                "Identify and avoid triggers (dust, pets, smoke)",
                "Ensure proper inhaler technique (spacer mandatory)",
                "Regular follow-up",
                "Asthma action plan for parents",
                "Avoid smoke exposure",
            ],
            follow_up_interval="Monthly until controlled, then 3 monthly",
            referral_criteria=[
                "Severe persistent asthma",
                "Poor control despite Step 3 therapy",
                "Frequent ED visits",
                "Need for oral steroids >2 times/year",
            ],
        )

    def get_protocol(self, condition: str) -> Optional[TreatmentProtocol]:
        """Get pediatric protocol for a condition."""
        condition_key = condition.lower().replace(" ", "_")
        return self.protocols.get(condition_key)

    def check_compliance(
        self,
        prescription: Dict,
        condition: str,
        age_years: Optional[float] = None,
    ) -> ComplianceReport:
        """
        Check pediatric prescription compliance.

        Args:
            prescription: Dict with medications
            condition: Pediatric condition
            age_years: Child's age (important for age-appropriate checks)

        Returns:
            ComplianceReport with pediatric-specific safety checks
        """
        protocol = self.get_protocol(condition)
        if not protocol:
            return ComplianceReport(
                diagnosis=condition,
                is_compliant=True,
                suggestions=["No specific pediatric protocol found"],
                score=100.0,
            )

        issues = []
        score = 100.0
        prescribed_drugs = prescription.get("medications", [])
        prescribed_names = [m.get("drug_name", "").lower() for m in prescribed_drugs]

        # CRITICAL: Check for aspirin in children
        if any("aspirin" in name for name in prescribed_names):
            issues.append(
                ComplianceIssue(
                    severity="critical",
                    category="drug_safety",
                    description="ASPIRIN prescribed in child",
                    recommendation="CONTRAINDICATED (Reye syndrome risk). Use Paracetamol.",
                )
            )
            score -= 40

        # Gastroenteritis: Check for ORS and Zinc
        if "gastroenteritis" in condition.lower() or "diarrhea" in condition.lower():
            has_ors = any("ors" in name or "rehydration" in name for name in prescribed_names)
            has_zinc = any("zinc" in name for name in prescribed_names)

            if not has_ors:
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_choice",
                        description="ORS not prescribed in gastroenteritis",
                        recommendation="ORS is cornerstone of treatment (WHO protocol)",
                    )
                )
                score -= 30

            if not has_zinc:
                issues.append(
                    ComplianceIssue(
                        severity="warning",
                        category="drug_choice",
                        description="Zinc not prescribed",
                        recommendation="Zinc 20mg OD x 14 days (IAP/WHO recommendation)",
                    )
                )
                score -= 10

            # Check for inappropriate antibiotics
            has_antibiotics = any(
                abx in name for abx in ["azithromycin", "amoxicillin", "cefixime"]
                for name in prescribed_names
            )
            if has_antibiotics and "dysentery" not in condition.lower():
                issues.append(
                    ComplianceIssue(
                        severity="warning",
                        category="drug_choice",
                        description="Antibiotic prescribed for non-dysenteric diarrhea",
                        recommendation="Antibiotics NOT routinely indicated in AGE",
                    )
                )
                score -= 15

        # Pneumonia: Check for high-dose amoxicillin
        if "pneumonia" in condition.lower():
            has_amoxicillin = any("amoxicillin" in name for name in prescribed_names)
            if not has_amoxicillin:
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_choice",
                        description="Amoxicillin not prescribed in pneumonia",
                        recommendation="High-dose Amoxicillin 80-90mg/kg/day TDS (IMNCI)",
                    )
                )
                score -= 30

        # Fever: Check for dengue-safe antipyretics
        if "fever" in condition.lower() or "dengue" in condition.lower():
            nsaids_used = any(
                drug in name for drug in ["ibuprofen", "diclofenac", "nimesulide"]
                for name in prescribed_names
            )
            if nsaids_used and "dengue" in condition.lower():
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_safety",
                        description="NSAID prescribed in dengue",
                        recommendation="Use ONLY Paracetamol in dengue (bleeding risk)",
                    )
                )
                score -= 35

        return ComplianceReport(
            diagnosis=condition,
            is_compliant=score >= 70,
            issues=issues,
            score=max(0, score),
        )

    def get_red_flags(self, presentation: Dict, age_months: Optional[int] = None) -> List[RedFlag]:
        """
        Identify pediatric red flags.

        Args:
            presentation: Symptoms, vitals, etc.
            age_months: Child's age in months

        Returns:
            List of RedFlag objects
        """
        red_flags = []

        # Age-specific danger signs
        if age_months is not None and age_months < 2:
            red_flags.append(
                RedFlag(
                    symptom="Infant <2 months",
                    urgency="URGENT",
                    action="Any serious illness in <2mo requires hospital evaluation",
                    age_specific=True,
                )
            )

        # Respiratory red flags
        rr = presentation.get("respiratory_rate")
        if rr and age_months:
            # WHO IMNCI criteria
            if age_months < 2 and rr >= 60:
                red_flags.append(
                    RedFlag(
                        symptom=f"Fast breathing (RR {rr})",
                        urgency="URGENT",
                        action="Pneumonia likely, needs immediate treatment",
                    )
                )
            elif age_months < 12 and rr >= 50:
                red_flags.append(
                    RedFlag(
                        symptom=f"Fast breathing (RR {rr})",
                        urgency="URGENT",
                        action="Pneumonia likely",
                    )
                )
            elif age_months < 60 and rr >= 40:
                red_flags.append(
                    RedFlag(
                        symptom=f"Fast breathing (RR {rr})",
                        urgency="URGENT",
                        action="Pneumonia likely",
                    )
                )

        # Dehydration
        if "diarrhea" in presentation.get("chief_complaint", "").lower():
            red_flags.append(
                RedFlag(
                    symptom="Diarrhea",
                    urgency="MONITOR",
                    action="Assess hydration status, ensure ORS given",
                )
            )

        # Fever with petechiae
        chief_complaint = presentation.get("chief_complaint", "").lower()
        if "rash" in chief_complaint and "fever" in chief_complaint:
            red_flags.append(
                RedFlag(
                    symptom="Fever + Rash",
                    urgency="URGENT",
                    action="Check for petechiae (dengue, meningococcemia), platelet count",
                )
            )

        return red_flags

    def get_immunization_schedule(self) -> Dict[str, List[str]]:
        """
        Get India National Immunization Schedule (NIS).

        Returns:
            Dict mapping age to vaccines due
        """
        return {
            "Birth": [
                "BCG",
                "OPV 0",
                "Hepatitis B (birth dose)",
            ],
            "6 weeks": [
                "DTwP/DTaP 1",
                "IPV 1",
                "Hepatitis B 1",
                "Hib 1",
                "Rotavirus 1",
                "PCV 1",
            ],
            "10 weeks": [
                "DTwP/DTaP 2",
                "IPV 2",
                "Hepatitis B 2",
                "Hib 2",
                "Rotavirus 2",
                "PCV 2",
            ],
            "14 weeks": [
                "DTwP/DTaP 3",
                "IPV 3",
                "Hepatitis B 3",
                "Hib 3",
                "Rotavirus 3",
                "PCV 3",
            ],
            "6 months": [
                "OPV 1",
                "Influenza 1 (start annual)",
            ],
            "9 months": [
                "MR 1 (Measles-Rubella)",
                "OPV 2",
            ],
            "12 months": [
                "Hepatitis A 1",
            ],
            "15 months": [
                "MMR 1",
                "Varicella 1",
                "PCV booster",
            ],
            "16-18 months": [
                "DTwP/DTaP booster 1",
                "IPV booster 1",
                "Hib booster",
            ],
            "18 months": [
                "Hepatitis A 2",
            ],
            "4-6 years": [
                "DTwP/DTaP booster 2",
                "OPV 3",
                "MMR 2",
                "Varicella 2",
            ],
            "10-12 years": [
                "Tdap/Td",
                "HPV (for girls - 2 doses, 6 months apart)",
            ],
        }

    def get_referral_criteria(self, condition: str) -> List[str]:
        """Get referral criteria for pediatric conditions."""
        protocol = self.get_protocol(condition)
        if protocol:
            return protocol.referral_criteria
        return []
