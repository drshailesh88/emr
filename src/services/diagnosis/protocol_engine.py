"""
Protocol Engine

Evidence-based treatment protocols for common conditions in Indian practice.
Implements clinical guidelines and checks prescription compliance.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class DrugRoute(Enum):
    """Route of medication administration."""
    ORAL = "Oral"
    IV = "IV"
    IM = "IM"
    SC = "SC"
    TOPICAL = "Topical"
    INHALED = "Inhaled"
    PR = "PR"


@dataclass
class Medication:
    """Represents a medication with dosing information."""

    drug_name: str
    generic_name: str
    strength: str
    form: str  # tablet, capsule, syrup, injection
    dose: str
    frequency: str  # OD, BD, TDS, QID, etc.
    route: DrugRoute = DrugRoute.ORAL
    duration: str = ""
    instructions: str = ""  # after meals, before meals, etc.
    indication: str = ""

    def __repr__(self) -> str:
        return f"{self.drug_name} {self.strength} {self.dose} {self.frequency}"


@dataclass
class TreatmentProtocol:
    """Complete treatment protocol for a diagnosis."""

    diagnosis: str
    icd10_code: Optional[str] = None
    first_line_drugs: List[Medication] = field(default_factory=list)
    second_line_drugs: List[Medication] = field(default_factory=list)
    investigations: List[str] = field(default_factory=list)
    monitoring: List[str] = field(default_factory=list)
    lifestyle_advice: List[str] = field(default_factory=list)
    follow_up_interval: str = "1-2 weeks"
    referral_criteria: List[str] = field(default_factory=list)
    contraindications: Dict[str, List[str]] = field(default_factory=dict)
    drug_interactions: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"TreatmentProtocol({self.diagnosis})"


@dataclass
class ComplianceIssue:
    """Represents a deviation from protocol."""

    severity: str  # critical, warning, info
    category: str  # drug_choice, dosing, monitoring, etc.
    description: str
    recommendation: str


@dataclass
class ComplianceReport:
    """Report of protocol compliance."""

    diagnosis: str
    is_compliant: bool
    issues: List[ComplianceIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    score: float = 100.0  # 0-100 compliance score


class ProtocolEngine:
    """
    Provides evidence-based treatment protocols for common conditions.

    Protocols based on:
    - Indian guidelines (RSSDI, API, CSI, etc.)
    - WHO essential medicines list
    - ICMR-NIN guidelines
    - Cost-effectiveness for Indian practice
    """

    def __init__(self):
        """Initialize protocol database."""
        self._load_protocols()

    def _load_protocols(self) -> None:
        """Load evidence-based protocols for common conditions."""
        self.protocols = {
            # DIABETES
            "type_2_diabetes": TreatmentProtocol(
                diagnosis="Type 2 Diabetes Mellitus",
                icd10_code="E11",
                first_line_drugs=[
                    Medication(
                        drug_name="Metformin",
                        generic_name="Metformin",
                        strength="500mg",
                        form="tablet",
                        dose="1",
                        frequency="BD",
                        duration="ongoing",
                        instructions="after meals",
                        indication="First-line for T2DM",
                    ),
                ],
                second_line_drugs=[
                    Medication(
                        drug_name="Glimepiride",
                        generic_name="Glimepiride",
                        strength="1mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        instructions="before breakfast",
                        indication="If HbA1c >7.5% despite metformin",
                    ),
                    Medication(
                        drug_name="Vildagliptin",
                        generic_name="Vildagliptin",
                        strength="50mg",
                        form="tablet",
                        dose="1",
                        frequency="BD",
                        indication="DPP4 inhibitor alternative",
                    ),
                ],
                investigations=[
                    "FBS/PPBS",
                    "HbA1c (every 3 months)",
                    "Lipid profile",
                    "Urine microalbumin",
                    "Serum creatinine",
                    "Fundus examination (yearly)",
                    "Foot examination",
                ],
                monitoring=[
                    "Blood sugar (fasting & PP)",
                    "HbA1c every 3 months",
                    "BP every visit",
                    "Kidney function every 6 months",
                    "Lipid profile yearly",
                ],
                lifestyle_advice=[
                    "Medical nutrition therapy (reduce refined carbs)",
                    "30 min exercise 5 days/week",
                    "Weight reduction if BMI >25",
                    "Avoid sugary drinks",
                    "Portion control",
                ],
                follow_up_interval="2-4 weeks initially, then monthly",
                referral_criteria=[
                    "HbA1c >9% despite dual therapy",
                    "Recurrent hypoglycemia",
                    "Diabetic foot ulcer",
                    "eGFR <30",
                    "Proliferative retinopathy",
                ],
            ),

            # HYPERTENSION
            "hypertension": TreatmentProtocol(
                diagnosis="Essential Hypertension",
                icd10_code="I10",
                first_line_drugs=[
                    Medication(
                        drug_name="Telmisartan",
                        generic_name="Telmisartan",
                        strength="40mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        instructions="morning",
                        indication="ARB for BP <140/90",
                    ),
                    Medication(
                        drug_name="Amlodipine",
                        generic_name="Amlodipine",
                        strength="5mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        indication="CCB, good for elderly",
                    ),
                ],
                second_line_drugs=[
                    Medication(
                        drug_name="Chlorthalidone",
                        generic_name="Chlorthalidone",
                        strength="12.5mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        indication="Add if BP not controlled",
                    ),
                ],
                investigations=[
                    "ECG",
                    "2D Echo",
                    "Lipid profile",
                    "FBS/HbA1c",
                    "Serum creatinine",
                    "Urine R/M",
                    "Fundoscopy",
                ],
                monitoring=[
                    "BP every visit",
                    "ECG yearly",
                    "Kidney function yearly",
                    "Electrolytes if on diuretic",
                ],
                lifestyle_advice=[
                    "DASH diet (low salt <5g/day)",
                    "Regular exercise 150 min/week",
                    "Weight loss if overweight",
                    "Limit alcohol",
                    "Quit smoking",
                    "Stress management",
                ],
                follow_up_interval="2 weeks initially, then monthly until controlled",
                referral_criteria=[
                    "BP >180/110 despite triple therapy",
                    "Secondary hypertension suspected",
                    "Target organ damage",
                ],
            ),

            # UPPER RESPIRATORY TRACT INFECTION
            "upper_respiratory_tract_infection": TreatmentProtocol(
                diagnosis="Upper Respiratory Tract Infection (Viral)",
                icd10_code="J06.9",
                first_line_drugs=[
                    Medication(
                        drug_name="Paracetamol",
                        generic_name="Paracetamol",
                        strength="500mg",
                        form="tablet",
                        dose="1-2",
                        frequency="TDS",
                        duration="3-5 days",
                        instructions="SOS for fever",
                        indication="Symptomatic relief",
                    ),
                    Medication(
                        drug_name="Cetirizine",
                        generic_name="Cetirizine",
                        strength="10mg",
                        form="tablet",
                        dose="1",
                        frequency="HS",
                        duration="5 days",
                        indication="For rhinitis symptoms",
                    ),
                ],
                investigations=[
                    "Usually clinical diagnosis",
                    "CBC if fever >3 days",
                    "Throat swab if bacterial suspected",
                ],
                monitoring=["Fever pattern", "Progression to LRTI"],
                lifestyle_advice=[
                    "Rest and hydration",
                    "Steam inhalation",
                    "Warm salt water gargle",
                    "Avoid cold drinks",
                ],
                follow_up_interval="Only if symptoms worsen or persist >7 days",
                referral_criteria=[
                    "High fever >5 days",
                    "Difficulty breathing",
                    "Severe throat pain with drooling",
                ],
            ),

            # URINARY TRACT INFECTION
            "urinary_tract_infection": TreatmentProtocol(
                diagnosis="Urinary Tract Infection (Uncomplicated)",
                icd10_code="N39.0",
                first_line_drugs=[
                    Medication(
                        drug_name="Nitrofurantoin",
                        generic_name="Nitrofurantoin",
                        strength="100mg",
                        form="tablet",
                        dose="1",
                        frequency="BD",
                        duration="5 days",
                        instructions="after meals",
                        indication="First-line for uncomplicated UTI",
                    ),
                ],
                second_line_drugs=[
                    Medication(
                        drug_name="Cefixime",
                        generic_name="Cefixime",
                        strength="200mg",
                        form="tablet",
                        dose="1",
                        frequency="BD",
                        duration="5-7 days",
                        indication="If nitrofurantoin contraindicated",
                    ),
                ],
                investigations=[
                    "Urine R/M",
                    "Urine C/S",
                    "USG abdomen if recurrent",
                ],
                monitoring=["Symptom resolution", "Repeat urine after treatment"],
                lifestyle_advice=[
                    "Drink plenty of water (3L/day)",
                    "Cranberry juice",
                    "Urinate frequently",
                    "Proper perineal hygiene",
                ],
                follow_up_interval="Only if symptoms persist after 3 days",
                referral_criteria=[
                    "Recurrent UTI (>3/year)",
                    "Pyelonephritis signs",
                    "Pregnancy",
                ],
            ),

            # DENGUE
            "dengue": TreatmentProtocol(
                diagnosis="Dengue Fever",
                icd10_code="A90",
                first_line_drugs=[
                    Medication(
                        drug_name="Paracetamol",
                        generic_name="Paracetamol",
                        strength="500mg",
                        form="tablet",
                        dose="1-2",
                        frequency="QID",
                        duration="as needed",
                        instructions="for fever",
                        indication="AVOID NSAIDs/Aspirin",
                    ),
                ],
                investigations=[
                    "NS1 antigen (days 1-5)",
                    "Dengue IgM/IgG (after day 5)",
                    "CBC with platelet count (daily)",
                    "Hematocrit (daily)",
                    "Liver enzymes",
                ],
                monitoring=[
                    "Platelet count daily",
                    "Hematocrit q12h in critical phase",
                    "Vital signs q4h",
                    "Urine output",
                    "Watch for warning signs (days 3-7)",
                ],
                lifestyle_advice=[
                    "Oral rehydration - ORS, coconut water",
                    "Complete bed rest",
                    "Avoid NSAIDs/aspirin",
                    "Papaya leaf juice (controversial but popular)",
                ],
                follow_up_interval="Daily during fever, critical phase days 3-7",
                referral_criteria=[
                    "Platelet <50,000",
                    "Warning signs (abdominal pain, vomiting, bleeding)",
                    "Hemoconcentration (Hct rise >20%)",
                    "Unable to maintain oral hydration",
                ],
            ),

            # MALARIA
            "malaria": TreatmentProtocol(
                diagnosis="Malaria (Uncomplicated)",
                icd10_code="B54",
                first_line_drugs=[
                    Medication(
                        drug_name="Artemether + Lumefantrine",
                        generic_name="Artemether + Lumefantrine",
                        strength="80mg/480mg",
                        form="tablet",
                        dose="4 tablets",
                        frequency="BD",
                        duration="3 days",
                        instructions="with fatty food",
                        indication="ACT for P. falciparum",
                    ),
                    Medication(
                        drug_name="Chloroquine",
                        generic_name="Chloroquine",
                        strength="250mg",
                        form="tablet",
                        dose="4 tabs stat, then 2 tabs at 6h, 24h, 48h",
                        frequency="per schedule",
                        duration="3 days",
                        indication="For P. vivax",
                    ),
                    Medication(
                        drug_name="Primaquine",
                        generic_name="Primaquine",
                        strength="7.5mg",
                        form="tablet",
                        dose="2 tabs",
                        frequency="OD",
                        duration="14 days",
                        instructions="after chloroquine",
                        indication="Radical cure for P. vivax (check G6PD first)",
                    ),
                ],
                investigations=[
                    "Peripheral smear (thick & thin)",
                    "Rapid malaria antigen (PfPv)",
                    "CBC",
                    "G6PD before primaquine",
                ],
                monitoring=[
                    "Fever clearance",
                    "Repeat smear on day 3",
                    "Watch for complications",
                ],
                follow_up_interval="Day 3, 7, 14, 28",
                referral_criteria=[
                    "Severe malaria (cerebral, ARDS, AKI)",
                    "Pregnant women",
                    "Children <5 years with complications",
                ],
            ),

            # TYPHOID
            "typhoid": TreatmentProtocol(
                diagnosis="Typhoid Fever",
                icd10_code="A01.0",
                first_line_drugs=[
                    Medication(
                        drug_name="Azithromycin",
                        generic_name="Azithromycin",
                        strength="500mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        duration="7 days",
                        indication="First-line for uncomplicated typhoid",
                    ),
                ],
                second_line_drugs=[
                    Medication(
                        drug_name="Ceftriaxone",
                        generic_name="Ceftriaxone",
                        strength="1g",
                        form="injection",
                        dose="1g",
                        frequency="OD",
                        route=DrugRoute.IV,
                        duration="7-10 days",
                        indication="For severe typhoid or resistance",
                    ),
                ],
                investigations=[
                    "Blood culture (first week)",
                    "Widal test (after 1 week)",
                    "Typhidot",
                    "CBC",
                    "LFT",
                ],
                monitoring=["Temperature chart", "Complications"],
                lifestyle_advice=[
                    "Soft, easily digestible diet",
                    "Adequate hydration",
                    "Complete rest",
                ],
                follow_up_interval="Weekly until fever settles",
                referral_criteria=[
                    "Intestinal perforation",
                    "GI bleeding",
                    "Altered sensorium",
                ],
            ),

            # GASTROENTERITIS
            "gastroenteritis": TreatmentProtocol(
                diagnosis="Acute Gastroenteritis",
                icd10_code="K52.9",
                first_line_drugs=[
                    Medication(
                        drug_name="ORS",
                        generic_name="Oral Rehydration Solution",
                        strength="sachets",
                        form="powder",
                        dose="as per requirement",
                        frequency="frequent sips",
                        duration="until diarrhea stops",
                        indication="Cornerstone of treatment",
                    ),
                    Medication(
                        drug_name="Zinc",
                        generic_name="Zinc",
                        strength="20mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        duration="14 days",
                        indication="For children, reduces duration",
                    ),
                ],
                second_line_drugs=[
                    Medication(
                        drug_name="Azithromycin",
                        generic_name="Azithromycin",
                        strength="500mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        duration="3 days",
                        indication="Only if dysentery or cholera",
                    ),
                ],
                investigations=[
                    "Usually clinical",
                    "Stool R/M if >3 days",
                    "Stool C/S if dysentery",
                    "Electrolytes if severe",
                ],
                monitoring=["Hydration status", "Urine output", "Weight (children)"],
                lifestyle_advice=[
                    "Continue feeding (especially children)",
                    "Avoid fruit juice",
                    "BRAT diet (banana, rice, applesauce, toast)",
                    "Hand hygiene",
                ],
                follow_up_interval="Only if worsening or >5 days",
                referral_criteria=[
                    "Severe dehydration",
                    "Bloody diarrhea with fever",
                    "Infants <6 months",
                ],
            ),

            # PNEUMONIA
            "pneumonia": TreatmentProtocol(
                diagnosis="Community-Acquired Pneumonia",
                icd10_code="J18.9",
                first_line_drugs=[
                    Medication(
                        drug_name="Amoxicillin + Clavulanate",
                        generic_name="Amoxicillin + Clavulanate",
                        strength="625mg",
                        form="tablet",
                        dose="1",
                        frequency="TDS",
                        duration="7 days",
                        instructions="after meals",
                        indication="Outpatient CAP",
                    ),
                    Medication(
                        drug_name="Azithromycin",
                        generic_name="Azithromycin",
                        strength="500mg",
                        form="tablet",
                        dose="1",
                        frequency="OD",
                        duration="5 days",
                        indication="If atypical suspected",
                    ),
                ],
                investigations=[
                    "Chest X-ray",
                    "CBC",
                    "CRP",
                    "SpO2",
                    "Sputum C/S if available",
                ],
                monitoring=[
                    "Clinical improvement",
                    "Repeat X-ray at 6 weeks",
                    "SpO2",
                ],
                lifestyle_advice=[
                    "Rest",
                    "Adequate hydration",
                    "Steam inhalation",
                    "Quit smoking",
                ],
                follow_up_interval="Day 3, then 1 week",
                referral_criteria=[
                    "CURB-65 ≥2",
                    "SpO2 <92%",
                    "No improvement in 48-72h",
                    "Complications",
                ],
            ),

            # ASTHMA
            "asthma": TreatmentProtocol(
                diagnosis="Bronchial Asthma",
                icd10_code="J45",
                first_line_drugs=[
                    Medication(
                        drug_name="Salbutamol",
                        generic_name="Salbutamol",
                        strength="100mcg",
                        form="inhaler",
                        dose="2 puffs",
                        frequency="QID or SOS",
                        route=DrugRoute.INHALED,
                        indication="Reliever",
                    ),
                    Medication(
                        drug_name="Budesonide",
                        generic_name="Budesonide",
                        strength="200mcg",
                        form="inhaler",
                        dose="2 puffs",
                        frequency="BD",
                        route=DrugRoute.INHALED,
                        instructions="rinse mouth after use",
                        indication="Controller",
                    ),
                ],
                second_line_drugs=[
                    Medication(
                        drug_name="Formoterol + Budesonide",
                        generic_name="Formoterol + Budesonide",
                        strength="6mcg/200mcg",
                        form="inhaler",
                        dose="2 puffs",
                        frequency="BD",
                        route=DrugRoute.INHALED,
                        indication="Step-up therapy",
                    ),
                ],
                investigations=[
                    "Spirometry with bronchodilator",
                    "Peak flow monitoring",
                    "Chest X-ray baseline",
                    "IgE levels if allergic",
                ],
                monitoring=[
                    "Peak flow diary",
                    "Symptom score",
                    "Inhaler technique",
                    "Spirometry yearly",
                ],
                lifestyle_advice=[
                    "Identify and avoid triggers",
                    "Breathing exercises",
                    "Quit smoking",
                    "Regular exercise",
                    "Maintain healthy weight",
                ],
                follow_up_interval="Monthly until controlled",
                referral_criteria=[
                    "Uncontrolled despite Step 3 therapy",
                    "Frequent exacerbations",
                    "Poor spirometry",
                ],
            ),

            # COPD
            "copd": TreatmentProtocol(
                diagnosis="Chronic Obstructive Pulmonary Disease",
                icd10_code="J44",
                first_line_drugs=[
                    Medication(
                        drug_name="Tiotropium",
                        generic_name="Tiotropium",
                        strength="18mcg",
                        form="inhaler",
                        dose="1 puff",
                        frequency="OD",
                        route=DrugRoute.INHALED,
                        indication="LAMA bronchodilator",
                    ),
                    Medication(
                        drug_name="Formoterol",
                        generic_name="Formoterol",
                        strength="6mcg",
                        form="inhaler",
                        dose="2 puffs",
                        frequency="BD",
                        route=DrugRoute.INHALED,
                        indication="LABA bronchodilator",
                    ),
                ],
                investigations=[
                    "Spirometry",
                    "Chest X-ray",
                    "ABG if severe",
                    "CBC",
                    "Alpha-1 antitrypsin (young patients)",
                ],
                monitoring=[
                    "Spirometry yearly",
                    "Exacerbation frequency",
                    "mMRC dyspnea scale",
                    "6-minute walk test",
                ],
                lifestyle_advice=[
                    "Smoking cessation (MOST IMPORTANT)",
                    "Pulmonary rehabilitation",
                    "Pneumococcal & influenza vaccination",
                    "Nutritional support",
                ],
                follow_up_interval="3 months",
                referral_criteria=[
                    "Severe COPD (FEV1 <30%)",
                    "Oxygen dependency",
                    "Frequent exacerbations",
                ],
            ),
        }

    def get_protocol(self, diagnosis: str) -> Optional[TreatmentProtocol]:
        """
        Get standard treatment protocol for a diagnosis.

        Args:
            diagnosis: Diagnosis name (can be partial match)

        Returns:
            TreatmentProtocol if found, None otherwise
        """
        # Try exact match first
        diagnosis_lower = diagnosis.lower().replace(" ", "_")
        if diagnosis_lower in self.protocols:
            return self.protocols[diagnosis_lower]

        # Try partial match
        for key, protocol in self.protocols.items():
            if diagnosis_lower in key or key in diagnosis_lower:
                return protocol

        return None

    def check_compliance(
        self,
        prescription: Dict,
        diagnosis: str,
    ) -> ComplianceReport:
        """
        Check if prescription follows evidence-based guidelines.

        Args:
            prescription: Dict with 'medications' list
            diagnosis: Diagnosis being treated

        Returns:
            ComplianceReport with issues and suggestions
        """
        protocol = self.get_protocol(diagnosis)

        if not protocol:
            return ComplianceReport(
                diagnosis=diagnosis,
                is_compliant=True,
                suggestions=["No specific protocol available for this diagnosis"],
                score=100.0,
            )

        issues = []
        suggestions = []
        score = 100.0

        prescribed_drugs = prescription.get("medications", [])
        prescribed_drug_names = [
            med.get("drug_name", "").lower() for med in prescribed_drugs
        ]

        # Check if first-line drugs are used
        first_line_used = False
        for first_line in protocol.first_line_drugs:
            if any(first_line.generic_name.lower() in name for name in prescribed_drug_names):
                first_line_used = True
                break

        if not first_line_used and protocol.first_line_drugs:
            issues.append(
                ComplianceIssue(
                    severity="warning",
                    category="drug_choice",
                    description="First-line drugs not used",
                    recommendation=f"Consider {protocol.first_line_drugs[0].generic_name}",
                )
            )
            score -= 20

        # Check for inappropriate antibiotics in viral infections
        if "viral" in diagnosis.lower() or "urti" in diagnosis.lower():
            antibiotics = ["azithromycin", "amoxicillin", "ciprofloxacin", "cefixime"]
            for drug_name in prescribed_drug_names:
                if any(abx in drug_name for abx in antibiotics):
                    issues.append(
                        ComplianceIssue(
                            severity="critical",
                            category="drug_choice",
                            description="Antibiotic prescribed for viral infection",
                            recommendation="Antibiotics not indicated for viral URTI",
                        )
                    )
                    score -= 30
                    break

        # Check for NSAIDs in dengue
        if "dengue" in diagnosis.lower():
            nsaids = ["ibuprofen", "diclofenac", "aspirin", "nimesulide"]
            for drug_name in prescribed_drug_names:
                if any(nsaid in drug_name for nsaid in nsaids):
                    issues.append(
                        ComplianceIssue(
                            severity="critical",
                            category="drug_safety",
                            description="NSAID prescribed in dengue",
                            recommendation="Avoid NSAIDs/aspirin in dengue - use paracetamol only",
                        )
                    )
                    score -= 40
                    break

        # Check if investigations are ordered
        prescribed_tests = prescription.get("investigations", [])
        if protocol.investigations:
            essential_tests_ordered = any(
                test.lower() in [t.lower() for t in prescribed_tests]
                for test in protocol.investigations[:2]  # Check first 2 essential tests
            )
            if not essential_tests_ordered:
                suggestions.append(
                    f"Consider ordering: {', '.join(protocol.investigations[:3])}"
                )
                score -= 10

        # Generate suggestions
        if not issues:
            suggestions.append("Prescription follows evidence-based guidelines")

        # Add lifestyle advice reminder
        if protocol.lifestyle_advice:
            suggestions.append(
                f"Remember to counsel on: {protocol.lifestyle_advice[0]}"
            )

        is_compliant = score >= 70

        return ComplianceReport(
            diagnosis=diagnosis,
            is_compliant=is_compliant,
            issues=issues,
            suggestions=suggestions,
            score=max(0, score),
        )

    def get_first_line_treatment(self, diagnosis: str) -> List[Medication]:
        """
        Get first-line medications for a diagnosis.

        Args:
            diagnosis: Diagnosis name

        Returns:
            List of first-line Medication objects
        """
        protocol = self.get_protocol(diagnosis)
        if protocol:
            return protocol.first_line_drugs
        return []

    def get_monitoring_requirements(self, diagnosis: str) -> List[str]:
        """
        Get monitoring requirements for a diagnosis.

        Args:
            diagnosis: Diagnosis name

        Returns:
            List of monitoring parameters
        """
        protocol = self.get_protocol(diagnosis)
        if protocol:
            return protocol.monitoring
        return []

    def get_lifestyle_advice(self, diagnosis: str) -> List[str]:
        """
        Get lifestyle modification advice for a diagnosis.

        Args:
            diagnosis: Diagnosis name

        Returns:
            List of lifestyle recommendations
        """
        protocol = self.get_protocol(diagnosis)
        if protocol:
            return protocol.lifestyle_advice
        return []

    def get_referral_criteria(self, diagnosis: str) -> List[str]:
        """
        Get criteria for specialist referral.

        Args:
            diagnosis: Diagnosis name

        Returns:
            List of referral criteria
        """
        protocol = self.get_protocol(diagnosis)
        if protocol:
            return protocol.referral_criteria
        return []
