"""
Obstetrics & Gynecology Clinical Protocols

Evidence-based protocols for OB/GYN conditions in Indian practice.
Based on FOGSI, WHO, ICMR, DIPSI, and international guidelines.
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
    """OB/GYN red flag warning."""
    symptom: str
    urgency: str  # EMERGENCY, URGENT, MONITOR
    action: str
    trimester_specific: Optional[str] = None


@dataclass
class ANCVisit:
    """Antenatal care visit schedule."""
    visit_number: int
    timing: str
    key_investigations: List[str]
    key_interventions: List[str]


class OBGYNProtocols:
    """
    Obstetrics & Gynecology protocols.

    Implements evidence-based management for:
    - Antenatal care (India-specific)
    - Gestational diabetes (DIPSI criteria)
    - Preeclampsia/Eclampsia
    - Postpartum care
    - Common gynecological conditions
    """

    def __init__(self):
        """Initialize OB/GYN protocols."""
        self._load_protocols()

    def _load_protocols(self) -> None:
        """Load OB/GYN-specific protocols."""
        self.protocols = {
            "antenatal_care": self._antenatal_care_protocol(),
            "gestational_diabetes": self._gestational_diabetes_protocol(),
            "preeclampsia": self._preeclampsia_protocol(),
            "eclampsia": self._eclampsia_protocol(),
            "postpartum_care": self._postpartum_care_protocol(),
            "pcos": self._pcos_protocol(),
            "menorrhagia": self._menorrhagia_protocol(),
            "dysmenorrhea": self._dysmenorrhea_protocol(),
            "menopause": self._menopause_protocol(),
        }

    def _antenatal_care_protocol(self) -> TreatmentProtocol:
        """Antenatal Care (ANC) protocol - India guidelines."""
        return TreatmentProtocol(
            diagnosis="Normal Pregnancy - Antenatal Care",
            icd10_code="Z34.9",
            first_line_drugs=[
                Medication(
                    drug_name="Folic Acid",
                    generic_name="Folic Acid",
                    strength="5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="First trimester (ideally preconception to 12 weeks)",
                    indication="Neural tube defect prevention",
                ),
                Medication(
                    drug_name="Iron + Folic Acid (IFA)",
                    generic_name="Ferrous Sulfate + Folic Acid",
                    strength="100mg elemental iron + 500mcg folic acid",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="Second & third trimester (from 14 weeks onwards)",
                    instructions="with vitamin C for better absorption",
                    indication="Anemia prevention (India dosing)",
                ),
                Medication(
                    drug_name="Calcium",
                    generic_name="Calcium carbonate",
                    strength="500mg",
                    form="tablet",
                    dose="2 tablets (1000mg total)",
                    frequency="OD",
                    duration="Throughout pregnancy",
                    instructions="separate from iron by 2 hours",
                    indication="Calcium supplementation (India recommendation)",
                ),
                Medication(
                    drug_name="Tetanus Toxoid (Td)",
                    generic_name="Tetanus-Diphtheria vaccine",
                    strength="",
                    form="injection",
                    dose="2 doses (Td1 at booking, Td2 after 4 weeks)",
                    frequency="As per schedule",
                    route=DrugRoute.IM,
                    indication="Tetanus prevention (if not previously immunized)",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Aspirin (low-dose)",
                    generic_name="Aspirin",
                    strength="75mg",
                    form="tablet",
                    dose="1",
                    frequency="HS (bedtime)",
                    duration="From 12 weeks to 36 weeks",
                    indication="Preeclampsia prevention (if high risk)",
                ),
                Medication(
                    drug_name="Progesterone",
                    generic_name="Micronized Progesterone",
                    strength="200mg",
                    form="capsule",
                    dose="1",
                    frequency="OD",
                    route=DrugRoute.PR,
                    duration="Till 36 weeks",
                    indication="Preterm birth prevention (if short cervix/h/o preterm)",
                ),
            ],
            investigations=[
                # First trimester (booking visit)
                "Hemoglobin, CBC",
                "Blood group & Rh typing",
                "Random blood sugar (diabetes screening)",
                "HIV, HBsAg, VDRL",
                "Urine R/M, culture",
                "TSH",
                "USG dating scan (11-13 weeks for NT scan if available)",

                # Second trimester
                "Anomaly scan (18-20 weeks)",
                "DIPSI (75g OGTT) at 24-28 weeks",
                "Repeat Hb at 28 weeks",

                # Third trimester
                "Repeat HIV, HBsAg at 32-36 weeks",
                "Repeat Hb at 36 weeks",
                "GBS swab at 35-37 weeks (if available)",
                "Growth scan at 32-36 weeks",
            ],
            monitoring=[
                "BP every visit",
                "Weight gain (10-12 kg target)",
                "Fundal height (after 24 weeks)",
                "Fetal heart rate (Doppler from 12 weeks)",
                "Fetal movements (from 20 weeks, count daily after 28 weeks)",
                "Urine protein (every visit after 20 weeks)",
                "Edema assessment",
            ],
            lifestyle_advice=[
                "Balanced diet (extra 300 kcal/day in 2nd & 3rd trimester)",
                "Avoid raw/undercooked foods (listeria, toxoplasma)",
                "Continue regular activity, avoid heavy lifting",
                "Sleep on left side (after 28 weeks)",
                "Avoid alcohol, smoking, tobacco",
                "Folic acid-rich foods (green leafy vegetables)",
                "Birth preparedness plan",
            ],
            follow_up_interval="""
            Minimum 4 ANC visits (WHO):
            - First visit: <12 weeks
            - Second visit: 20-24 weeks
            - Third visit: 28-32 weeks
            - Fourth visit: 36+ weeks

            Ideal 8+ visits:
            - Monthly till 28 weeks
            - Fortnightly 28-36 weeks
            - Weekly after 36 weeks
            """,
            referral_criteria=[
                "High-risk pregnancy (age <18 or >35, diabetes, hypertension)",
                "Multiple pregnancy",
                "Abnormal lie after 36 weeks",
                "Preeclampsia (BP ≥140/90 + proteinuria)",
                "IUGR, oligohydramnios, polyhydramnios",
                "Any obstetric emergency",
            ],
        )

    def _gestational_diabetes_protocol(self) -> TreatmentProtocol:
        """Gestational Diabetes Mellitus (GDM) - DIPSI criteria (India)."""
        return TreatmentProtocol(
            diagnosis="Gestational Diabetes Mellitus (GDM)",
            icd10_code="O24.4",
            first_line_drugs=[
                # Medical Nutrition Therapy first for 2 weeks
                Medication(
                    drug_name="Medical Nutrition Therapy (MNT)",
                    generic_name="N/A",
                    strength="",
                    form="",
                    dose="",
                    frequency="",
                    duration="2 weeks trial",
                    indication="First-line treatment for GDM",
                ),
            ],
            second_line_drugs=[
                # If MNT fails (FBS >95, 2h PPBS >120)
                Medication(
                    drug_name="Insulin (Human Regular)",
                    generic_name="Human Regular Insulin",
                    strength="100 IU/ml",
                    form="injection",
                    dose="Start 4-6 units, titrate based on sugars",
                    frequency="Before meals (TDS) + bedtime NPH",
                    route=DrugRoute.SC,
                    instructions="Titrate to targets: FBS <95, 2h PP <120",
                    indication="Gold standard if MNT fails",
                ),
                Medication(
                    drug_name="Metformin",
                    generic_name="Metformin",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="BD (start 500mg OD, increase gradually)",
                    duration="Till delivery",
                    instructions="Alternative to insulin (if patient refuses insulin)",
                    indication="Alternative option (not first-line in India)",
                ),
            ],
            investigations=[
                "DIPSI test: 75g OGTT (2h plasma glucose)",
                "Diagnostic if 2h PG ≥140 mg/dL",
                "Fasting & 2h postprandial glucose monitoring",
                "HbA1c at diagnosis (rule out preexisting DM)",
                "Growth scans q4 weeks (macrosomia risk)",
                "Fetal echo at 24 weeks (cardiac anomaly risk if DM in T1)",
            ],
            monitoring=[
                "Self-monitoring blood glucose (SMBG)",
                "Fasting daily",
                "2h postprandial after each meal",
                "Targets: FBS <95, 2h PP <120 mg/dL",
                "Fetal growth scans q4 weeks",
                "NST from 36 weeks",
            ],
            lifestyle_advice=[
                "Medical Nutrition Therapy:",
                "  - Carbohydrate counting (40-45% of calories)",
                "  - 3 meals + 3 snacks",
                "  - Avoid simple sugars, refined carbs",
                "  - Complex carbs (whole grains, millets)",
                "Regular exercise (30 min walk after meals)",
                "Ketone check if fasting (avoid starvation)",
            ],
            follow_up_interval="Weekly until controlled, then fortnightly",
            referral_criteria=[
                "Uncontrolled sugars despite insulin",
                "Macrosomia (EFW >90th percentile)",
                "Polyhydramnios",
                "Preeclampsia with GDM",
            ],
            contraindications={
                "oral_hypoglycemics": ["Not first-line in India (insulin preferred)"],
            },
        )

    def _preeclampsia_protocol(self) -> TreatmentProtocol:
        """Preeclampsia management protocol."""
        return TreatmentProtocol(
            diagnosis="Preeclampsia",
            icd10_code="O14.9",
            first_line_drugs=[
                Medication(
                    drug_name="Methyldopa",
                    generic_name="Methyldopa",
                    strength="250mg",
                    form="tablet",
                    dose="2-4 tablets",
                    frequency="TDS",
                    instructions="Start 250mg TDS, increase to max 2g/day",
                    indication="First-line antihypertensive in pregnancy",
                ),
                Medication(
                    drug_name="Nifedipine (sustained release)",
                    generic_name="Nifedipine SR",
                    strength="20mg",
                    form="tablet",
                    dose="1-2",
                    frequency="BD",
                    instructions="Not with MgSO4 (severe hypotension risk)",
                    indication="Second-line or add-on",
                ),
                Medication(
                    drug_name="Labetalol",
                    generic_name="Labetalol",
                    strength="100mg",
                    form="tablet/injection",
                    dose="100mg BD, titrate to 400mg TDS",
                    frequency="BD-TDS",
                    indication="Alternative first-line",
                ),
            ],
            second_line_drugs=[
                # Severe features: MgSO4 for seizure prophylaxis
                Medication(
                    drug_name="Magnesium Sulfate (MgSO4)",
                    generic_name="MgSO4",
                    strength="50%",
                    form="injection",
                    dose="Pritchard regimen (see instructions)",
                    frequency="Loading + maintenance",
                    route=DrugRoute.IM,
                    instructions="""
                    Pritchard Regimen (IM):
                    - Loading: 4g IV (20% in 20ml over 5min) + 10g IM (5g each buttock)
                    - Maintenance: 5g IM q4h (alternate buttocks)

                    Monitor: RR >16, Urine output >30ml/h, Knee jerk present
                    Antidote: Calcium gluconate 10% 10ml IV
                    """,
                    indication="Seizure prophylaxis (severe preeclampsia)",
                ),
            ],
            investigations=[
                "BP monitoring (severe if ≥160/110)",
                "Urine protein (24h or spot PCR)",
                "CBC (platelet count - HELLP syndrome)",
                "LFT (AST, ALT - HELLP)",
                "Serum creatinine",
                "Uric acid",
                "Fetal monitoring (NST, Doppler)",
            ],
            monitoring=[
                "BP q4-6h",
                "Proteinuria",
                "Symptoms: Headache, visual disturbances, epigastric pain",
                "Deep tendon reflexes (hyperreflexia)",
                "Urine output (oliguria <400ml/24h)",
                "Labs: Platelet, LFT, creatinine",
                "Fetal well-being (NST, AFI)",
            ],
            lifestyle_advice=[
                "Bed rest (left lateral position)",
                "Normal salt diet (no restriction)",
                "Adequate hydration",
                "Monitor fetal movements",
            ],
            follow_up_interval="Hospitalize if severe features",
            referral_criteria=[
                "Severe preeclampsia (BP ≥160/110, proteinuria >5g/24h)",
                "Symptoms: Severe headache, blurred vision, epigastric pain",
                "HELLP syndrome (Hemolysis, Elevated Liver enzymes, Low Platelets)",
                "Eclampsia (seizures)",
                "Fetal compromise",
                "Plan delivery if ≥37 weeks or severe features",
            ],
            contraindications={
                "ace_inhibitors": ["Teratogenic - NEVER in pregnancy"],
                "arbs": ["Teratogenic - NEVER in pregnancy"],
            },
        )

    def _eclampsia_protocol(self) -> TreatmentProtocol:
        """Eclampsia (seizures in pregnancy) - Emergency protocol."""
        return TreatmentProtocol(
            diagnosis="Eclampsia",
            icd10_code="O15.9",
            first_line_drugs=[
                Medication(
                    drug_name="Magnesium Sulfate",
                    generic_name="MgSO4",
                    strength="50%",
                    form="injection",
                    dose="See Pritchard/Zuspan regimen",
                    frequency="Loading + maintenance for 24h post-delivery",
                    route=DrugRoute.IV,
                    instructions="""
                    EMERGENCY - MgSO4 is drug of choice (NOT phenytoin/diazepam)

                    Zuspan Regimen (IV):
                    - Loading: 4-6g IV over 15-20 min
                    - Maintenance: 1-2g/hour continuous infusion

                    Continue for 24 hours after delivery or last seizure
                    """,
                    indication="Seizure control and prophylaxis",
                ),
            ],
            investigations=["As per preeclampsia + immediate delivery planning"],
            monitoring=[
                "AIRWAY protection",
                "MgSO4 toxicity: RR, urine output, reflexes",
                "Continuous vitals monitoring",
            ],
            lifestyle_advice=["N/A - EMERGENCY"],
            follow_up_interval="Hospitalize - ICU/HDU",
            referral_criteria=[
                "ALL eclampsia cases need tertiary care",
                "Stabilize, give MgSO4, transfer",
                "Plan delivery after stabilization",
            ],
        )

    def _postpartum_care_protocol(self) -> TreatmentProtocol:
        """Postpartum care protocol."""
        return TreatmentProtocol(
            diagnosis="Postpartum Period (Normal)",
            icd10_code="Z39.2",
            first_line_drugs=[
                Medication(
                    drug_name="Iron + Folic Acid",
                    generic_name="Ferrous Sulfate + Folic Acid",
                    strength="100mg + 500mcg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months postpartum",
                    indication="Anemia correction/prevention",
                ),
                Medication(
                    drug_name="Paracetamol",
                    generic_name="Paracetamol",
                    strength="500mg",
                    form="tablet",
                    dose="1-2",
                    frequency="TDS PRN",
                    duration="3-5 days",
                    indication="Pain relief (perineal/uterine cramping)",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Ibuprofen",
                    generic_name="Ibuprofen",
                    strength="400mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    duration="5-7 days",
                    indication="If stronger analgesia needed (safe in breastfeeding)",
                ),
            ],
            investigations=[
                "Hemoglobin at 6 weeks (if anemic in pregnancy)",
                "BP check (if hypertensive in pregnancy)",
                "Thyroid function (if at risk)",
            ],
            monitoring=[
                "Lochia (should decrease progressively, not foul-smelling)",
                "Uterine involution (fundus should decrease)",
                "Perineal healing (if episiotomy/tear)",
                "Breastfeeding assessment",
                "Postpartum depression screening (Edinburgh scale)",
                "Contraception counseling",
            ],
            lifestyle_advice=[
                "BREASTFEEDING support:",
                "  - Exclusive breastfeeding for 6 months",
                "  - Proper latch technique",
                "  - Feed on demand (8-12 times/day)",
                "  - No prelacteal feeds",
                "Adequate nutrition (extra 500 kcal/day)",
                "Rest when baby sleeps",
                "Perineal hygiene (warm water wash)",
                "Pelvic floor exercises (after 6 weeks)",
                "Sexual activity (after 6 weeks or when comfortable)",
            ],
            follow_up_interval="Week 1, Week 6, 6 months",
            referral_criteria=[
                "Postpartum hemorrhage (>500ml)",
                "Foul-smelling lochia (endometritis)",
                "Persistent fever",
                "Severe perineal pain",
                "Breast engorgement, mastitis",
                "Postpartum depression",
            ],
        )

    def _pcos_protocol(self) -> TreatmentProtocol:
        """Polycystic Ovary Syndrome (PCOS) protocol - Rotterdam criteria."""
        return TreatmentProtocol(
            diagnosis="Polycystic Ovary Syndrome (PCOS)",
            icd10_code="E28.2",
            first_line_drugs=[
                Medication(
                    drug_name="Metformin",
                    generic_name="Metformin",
                    strength="500mg",
                    form="tablet",
                    dose="1-2",
                    frequency="BD-TDS",
                    duration="Long-term",
                    instructions="Start low (500mg OD), increase gradually",
                    indication="Insulin resistance, menstrual regulation",
                ),
                Medication(
                    drug_name="Combined Oral Contraceptive (COC)",
                    generic_name="Ethinyl Estradiol + Progestin",
                    strength="30mcg + varies",
                    form="tablet",
                    dose="1",
                    frequency="OD x 21 days",
                    duration="Cyclical (if not planning pregnancy)",
                    indication="Menstrual regulation, hyperandrogenism",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Clomiphene Citrate",
                    generic_name="Clomiphene",
                    strength="50mg",
                    form="tablet",
                    dose="1",
                    frequency="OD for 5 days (day 2-6 of cycle)",
                    indication="Ovulation induction (if planning pregnancy)",
                ),
                Medication(
                    drug_name="Spironolactone",
                    generic_name="Spironolactone",
                    strength="50mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    indication="Hirsutism, acne (anti-androgen)",
                ),
            ],
            investigations=[
                "Diagnosis (Rotterdam criteria - 2 of 3):",
                "  1. Oligo/anovulation",
                "  2. Hyperandrogenism (clinical or biochemical)",
                "  3. Polycystic ovaries on USG",
                "",
                "Investigations:",
                "Pelvic USG (ovarian morphology)",
                "Total testosterone, free testosterone",
                "LH, FSH (LH:FSH ratio often >2)",
                "DHEAS (to rule out adrenal cause)",
                "75g OGTT (insulin resistance, diabetes screening)",
                "Lipid profile",
                "TSH (hypothyroidism common)",
            ],
            monitoring=[
                "Menstrual cycle regularity",
                "Weight, BMI",
                "Hirsutism score (Ferriman-Gallwey)",
                "Metabolic parameters (OGTT, lipids)",
                "Ovulation tracking (if trying to conceive)",
            ],
            lifestyle_advice=[
                "WEIGHT LOSS (5-10% can restore ovulation)",
                "Low glycemic index diet",
                "Regular exercise (150 min/week)",
                "Stress management",
            ],
            follow_up_interval="3 months initially, then 6 monthly",
            referral_criteria=[
                "Infertility despite ovulation induction",
                "Severe hirsutism",
                "Metabolic syndrome",
            ],
        )

    def _menorrhagia_protocol(self) -> TreatmentProtocol:
        """Menorrhagia (Heavy Menstrual Bleeding) protocol."""
        return TreatmentProtocol(
            diagnosis="Menorrhagia (Heavy Menstrual Bleeding)",
            icd10_code="N92.0",
            first_line_drugs=[
                Medication(
                    drug_name="Tranexamic Acid",
                    generic_name="Tranexamic Acid",
                    strength="500mg",
                    form="tablet",
                    dose="2",
                    frequency="TDS",
                    duration="During menses only (days 1-5)",
                    indication="Reduces blood loss by 40-50%",
                ),
                Medication(
                    drug_name="Mefenamic Acid",
                    generic_name="Mefenamic Acid",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    duration="During menses",
                    instructions="after meals",
                    indication="NSAID - reduces flow + dysmenorrhea",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Combined Oral Contraceptive",
                    generic_name="COC",
                    strength="30mcg EE",
                    form="tablet",
                    dose="1",
                    frequency="OD x 21 days",
                    indication="If medical management fails, consider hormonal",
                ),
                Medication(
                    drug_name="Levonorgestrel IUS (Mirena)",
                    generic_name="LNG-IUS",
                    strength="52mg",
                    form="intrauterine device",
                    dose="",
                    frequency="",
                    duration="5 years",
                    indication="Most effective medical treatment for menorrhagia",
                ),
            ],
            investigations=[
                "Hemoglobin, serum ferritin (anemia)",
                "Thyroid function (hypothyroidism)",
                "Coagulation profile (if h/o bleeding disorder)",
                "Pelvic USG (fibroids, adenomyosis, endometrial thickness)",
                "Endometrial biopsy (if >40 years or risk factors)",
            ],
            monitoring=["Hemoglobin", "Menstrual diary"],
            lifestyle_advice=[
                "Iron supplementation",
                "Menstrual cup/chart to quantify flow",
            ],
            follow_up_interval="3 months",
            referral_criteria=[
                "Medical management failure",
                "Severe anemia (Hb <7)",
                "Structural abnormality needing surgery",
            ],
        )

    def _dysmenorrhea_protocol(self) -> TreatmentProtocol:
        """Dysmenorrhea (painful periods) protocol."""
        return TreatmentProtocol(
            diagnosis="Dysmenorrhea (Primary)",
            icd10_code="N94.6",
            first_line_drugs=[
                Medication(
                    drug_name="Mefenamic Acid",
                    generic_name="Mefenamic Acid",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    duration="Days 1-3 of menses",
                    instructions="Start at onset of bleeding or pain",
                    indication="NSAID - prostaglandin inhibition",
                ),
                Medication(
                    drug_name="Ibuprofen",
                    generic_name="Ibuprofen",
                    strength="400mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    duration="Days 1-3",
                    indication="Alternative NSAID",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Combined Oral Contraceptive",
                    generic_name="COC",
                    strength="30mcg EE",
                    form="tablet",
                    dose="1",
                    frequency="OD x 21 days",
                    indication="If NSAIDs fail, hormonal suppression",
                ),
            ],
            investigations=[
                "Usually clinical diagnosis (primary dysmenorrhea)",
                "Pelvic USG (if severe, to rule out endometriosis, fibroids)",
            ],
            monitoring=["Pain severity", "Response to treatment"],
            lifestyle_advice=[
                "Heat application (hot water bottle)",
                "Exercise",
                "Stress reduction",
            ],
            follow_up_interval="3 months",
            referral_criteria=[
                "Severe pain despite treatment (suspect secondary causes)",
                "Deep dyspareunia (endometriosis)",
            ],
        )

    def _menopause_protocol(self) -> TreatmentProtocol:
        """Menopause management protocol."""
        return TreatmentProtocol(
            diagnosis="Menopause",
            icd10_code="N95.1",
            first_line_drugs=[
                # HRT (if symptoms severe and no contraindications)
                Medication(
                    drug_name="Estrogen + Progesterone (HRT)",
                    generic_name="Conjugated Estrogen + MPA",
                    strength="0.625mg + 5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="Shortest duration for symptom control",
                    instructions="Use only if severe symptoms, counsel risks/benefits",
                    indication="Vasomotor symptoms, vaginal atrophy",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Fluoxetine/Paroxetine (SSRI)",
                    generic_name="SSRI",
                    strength="20mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="Hot flashes (if HRT contraindicated)",
                ),
                Medication(
                    drug_name="Vaginal Estrogen",
                    generic_name="Estradiol vaginal cream",
                    strength="0.01%",
                    form="cream",
                    dose="",
                    frequency="As directed",
                    indication="Vaginal atrophy, dyspareunia",
                ),
            ],
            investigations=[
                "FSH (if diagnosis unclear - >30 IU/L suggests menopause)",
                "TSH (hypothyroidism mimics menopause)",
                "Lipid profile (CVD risk increases)",
                "DEXA scan (osteoporosis screening at 65 or earlier if risk factors)",
                "Mammography (before starting HRT, then yearly)",
            ],
            monitoring=[
                "Symptom improvement",
                "Breast exam (yearly)",
                "Mammography (yearly if on HRT)",
                "Cardiovascular risk assessment",
            ],
            lifestyle_advice=[
                "Calcium 1200mg/day + Vitamin D",
                "Weight-bearing exercise (osteoporosis prevention)",
                "Healthy diet",
                "Avoid triggers (caffeine, alcohol, spicy food for hot flashes)",
                "Pelvic floor exercises",
            ],
            follow_up_interval="3 months initially, then yearly",
            referral_criteria=["Abnormal bleeding (endometrial cancer risk)"],
        )

    def get_protocol(self, condition: str) -> Optional[TreatmentProtocol]:
        """Get OB/GYN protocol for a condition."""
        condition_key = condition.lower().replace(" ", "_")
        return self.protocols.get(condition_key)

    def check_compliance(
        self,
        prescription: Dict,
        condition: str,
        is_pregnant: bool = False,
        trimester: Optional[int] = None,
    ) -> ComplianceReport:
        """
        Check OB/GYN prescription compliance.

        Args:
            prescription: Dict with medications
            condition: OB/GYN condition
            is_pregnant: Whether patient is pregnant
            trimester: Trimester (1, 2, or 3)

        Returns:
            ComplianceReport with pregnancy-specific safety checks
        """
        protocol = self.get_protocol(condition)
        if not protocol:
            return ComplianceReport(
                diagnosis=condition,
                is_compliant=True,
                suggestions=["No specific OB/GYN protocol found"],
                score=100.0,
            )

        issues = []
        score = 100.0
        prescribed_drugs = prescription.get("medications", [])
        prescribed_names = [m.get("drug_name", "").lower() for m in prescribed_drugs]

        # CRITICAL: Teratogenic drugs in pregnancy
        if is_pregnant:
            teratogenic_drugs = {
                "ace": "ACE inhibitors (teratogenic)",
                "arb": "ARBs (teratogenic)",
                "warfarin": "Warfarin (teratogenic, especially T1)",
                "isotretinoin": "Isotretinoin (highly teratogenic)",
                "methotrexate": "Methotrexate (teratogenic)",
                "finasteride": "Finasteride (teratogenic)",
            }

            for drug_key, drug_desc in teratogenic_drugs.items():
                if any(drug_key in name for name in prescribed_names):
                    issues.append(
                        ComplianceIssue(
                            severity="critical",
                            category="drug_safety",
                            description=f"{drug_desc} prescribed in pregnancy",
                            recommendation="CONTRAINDICATED in pregnancy. Stop immediately.",
                        )
                    )
                    score -= 50

        # Antenatal care: Check for IFA
        if "antenatal" in condition.lower() or (is_pregnant and trimester and trimester >= 2):
            has_iron = any(
                "iron" in name or "ferrous" in name or "ifa" in name
                for name in prescribed_names
            )
            if not has_iron:
                issues.append(
                    ComplianceIssue(
                        severity="warning",
                        category="drug_choice",
                        description="Iron supplementation not prescribed in pregnancy",
                        recommendation="IFA 100mg elemental iron + 500mcg folic acid OD",
                    )
                )
                score -= 15

        # GDM: Check for MNT first, then insulin
        if "gestational_diabetes" in condition.lower() or "gdm" in condition.lower():
            has_insulin = any("insulin" in name for name in prescribed_names)
            has_metformin = any("metformin" in name for name in prescribed_names)

            # Metformin not first-line in India
            if has_metformin and not has_insulin:
                issues.append(
                    ComplianceIssue(
                        severity="warning",
                        category="drug_choice",
                        description="Metformin used as first-line in GDM",
                        recommendation="Insulin is gold standard in India (metformin second-line)",
                    )
                )
                score -= 10

        # Preeclampsia: Check for appropriate antihypertensives
        if "preeclampsia" in condition.lower():
            has_appropriate_bp_med = any(
                drug in name for drug in ["methyldopa", "labetalol", "nifedipine"]
                for name in prescribed_names
            )
            if not has_appropriate_bp_med:
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_choice",
                        description="No appropriate antihypertensive in preeclampsia",
                        recommendation="Use Methyldopa, Labetalol, or Nifedipine SR",
                    )
                )
                score -= 30

        return ComplianceReport(
            diagnosis=condition,
            is_compliant=score >= 70,
            issues=issues,
            score=max(0, score),
        )

    def get_red_flags(self, presentation: Dict, is_pregnant: bool = False) -> List[RedFlag]:
        """
        Identify OB/GYN red flags.

        Args:
            presentation: Symptoms, vitals, etc.
            is_pregnant: Whether patient is pregnant

        Returns:
            List of RedFlag objects
        """
        red_flags = []

        if is_pregnant:
            # Pregnancy red flags
            bp_systolic = presentation.get("bp_systolic")
            if bp_systolic and bp_systolic >= 140:
                red_flags.append(
                    RedFlag(
                        symptom=f"Hypertension in pregnancy (BP {bp_systolic}/...)",
                        urgency="URGENT",
                        action="Check for preeclampsia (BP, proteinuria, symptoms)",
                    )
                )

            if "bleeding" in presentation.get("chief_complaint", "").lower():
                red_flags.append(
                    RedFlag(
                        symptom="Vaginal bleeding in pregnancy",
                        urgency="EMERGENCY",
                        action="Rule out placenta previa, abruption, miscarriage",
                    )
                )

            if "headache" in presentation.get("chief_complaint", "").lower():
                red_flags.append(
                    RedFlag(
                        symptom="Severe headache in pregnancy",
                        urgency="URGENT",
                        action="Rule out preeclampsia/eclampsia",
                        trimester_specific="Especially 2nd/3rd trimester",
                    )
                )

            if "abdominal pain" in presentation.get("chief_complaint", "").lower():
                red_flags.append(
                    RedFlag(
                        symptom="Abdominal pain in pregnancy",
                        urgency="URGENT",
                        action="Rule out preterm labor, abruption, ectopic (if T1)",
                    )
                )

        return red_flags

    def get_anc_visit_schedule(self) -> List[ANCVisit]:
        """
        Get detailed ANC visit schedule (India guidelines).

        Returns:
            List of ANCVisit objects with timing and interventions
        """
        return [
            ANCVisit(
                visit_number=1,
                timing="<12 weeks (First trimester)",
                key_investigations=[
                    "Hemoglobin, Blood group",
                    "HIV, HBsAg, VDRL",
                    "Urine R/M, culture",
                    "TSH, Random blood sugar",
                    "USG dating + NT scan (11-13 weeks)",
                ],
                key_interventions=[
                    "Folic Acid 5mg OD",
                    "Td vaccination (if not previously immunized)",
                    "History, risk assessment",
                ],
            ),
            ANCVisit(
                visit_number=2,
                timing="20-24 weeks",
                key_investigations=[
                    "Anomaly scan (18-20 weeks)",
                ],
                key_interventions=[
                    "Start IFA tablets",
                    "Calcium supplementation",
                    "Td booster (4 weeks after Td1)",
                ],
            ),
            ANCVisit(
                visit_number=3,
                timing="28-32 weeks",
                key_investigations=[
                    "DIPSI test (75g OGTT) at 24-28 weeks",
                    "Repeat Hemoglobin",
                    "Growth scan",
                ],
                key_interventions=[
                    "Continue IFA",
                    "Fetal movement counting",
                ],
            ),
            ANCVisit(
                visit_number=4,
                timing="36+ weeks",
                key_investigations=[
                    "Repeat HIV, HBsAg",
                    "Repeat Hb",
                    "GBS swab (35-37 weeks)",
                    "Growth scan",
                ],
                key_interventions=[
                    "Birth preparedness",
                    "Breastfeeding counseling",
                    "Danger signs education",
                ],
            ),
        ]

    def get_referral_criteria(self, condition: str) -> List[str]:
        """Get referral criteria for OB/GYN conditions."""
        protocol = self.get_protocol(condition)
        if protocol:
            return protocol.referral_criteria
        return []
