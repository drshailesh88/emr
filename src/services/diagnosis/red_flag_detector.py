"""
Red Flag Detector

Identifies life-threatening conditions and emergencies requiring
immediate intervention.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from enum import Enum


class UrgencyLevel(Enum):
    """Urgency classification for red flags."""
    EMERGENCY = "EMERGENCY"  # Life-threatening, immediate action (<5 min)
    URGENT = "URGENT"  # Serious, needs action within 1 hour
    WARNING = "WARNING"  # Concerning, needs evaluation within 4-6 hours


@dataclass
class RedFlag:
    """Represents a red flag finding with urgency and recommended action."""

    category: str
    description: str
    urgency: UrgencyLevel
    recommended_action: str
    time_critical: str
    matching_features: List[str]
    differential_concerns: List[str]

    def __repr__(self) -> str:
        return f"RedFlag({self.category}: {self.description} [{self.urgency.value}])"


class RedFlagDetector:
    """
    Detects red flag conditions requiring immediate medical attention.

    Optimized for Indian emergency medicine practice with focus on
    common life-threatening presentations.
    """

    def __init__(self):
        """Initialize red flag patterns."""
        self._load_red_flag_patterns()

    def _load_red_flag_patterns(self) -> None:
        """
        Load red flag patterns organized by system.

        Each pattern has:
        - required: All must be present
        - any_of: At least one must be present
        - category: System involved
        - urgency: How quickly to act
        - action: What to do immediately
        - concerns: Potential diagnoses
        """
        self.patterns = [
            # CARDIAC RED FLAGS
            {
                "name": "acute_coronary_syndrome",
                "category": "CARDIAC",
                "required": ["chest_pain"],
                "any_of": ["sweating", "radiation_to_arm", "radiation_to_jaw", "crushing_pain", "nausea"],
                "threshold": 1,  # At least 1 from any_of
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Acute Coronary Syndrome",
                "action": "Aspirin 325mg chewed immediately, oxygen, ECG within 10 minutes, activate cath lab if STEMI",
                "time_critical": "Door-to-needle: 30 min, Door-to-balloon: 90 min",
                "concerns": ["STEMI", "NSTEMI", "Unstable Angina"],
            },
            {
                "name": "severe_chest_pain",
                "category": "CARDIAC",
                "required": ["chest_pain_severe"],
                "any_of": ["tearing_pain", "back_pain", "syncope", "pulse_deficit"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Aortic Dissection",
                "action": "IV access, BP control (target SBP 100-120), stat CT angiography, surgical consult",
                "time_critical": "Diagnosis within 30 minutes critical",
                "concerns": ["Aortic Dissection", "Ruptured AAA"],
            },

            # NEUROLOGICAL RED FLAGS
            {
                "name": "stroke_symptoms",
                "category": "NEURO",
                "required": [],
                "any_of": ["focal_weakness", "facial_droop", "slurred_speech", "sudden_vision_loss", "severe_vertigo"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Acute Stroke",
                "action": "Activate stroke protocol, NIHSS score, stat CT brain, consider thrombolysis if <4.5 hours",
                "time_critical": "Door-to-needle: 60 min, Golden hour for thrombolysis",
                "concerns": ["Ischemic Stroke", "Hemorrhagic Stroke", "TIA"],
            },
            {
                "name": "worst_headache_of_life",
                "category": "NEURO",
                "required": ["severe_headache"],
                "any_of": ["sudden_onset", "thunderclap", "worst_headache_ever", "neck_stiffness"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Subarachnoid Hemorrhage",
                "action": "Stat CT brain (non-contrast), LP if CT negative, neurosurgery consult",
                "time_critical": "CT within 6 hours has 95% sensitivity",
                "concerns": ["Subarachnoid Hemorrhage", "Meningitis", "Venous Sinus Thrombosis"],
            },
            {
                "name": "meningitis_signs",
                "category": "NEURO",
                "required": ["fever"],
                "any_of": ["neck_stiffness", "altered_consciousness", "photophobia", "severe_headache", "seizure"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Meningitis/Encephalitis",
                "action": "Blood cultures, empiric antibiotics (ceftriaxone 2g IV), dexamethasone, LP after CT if safe",
                "time_critical": "Antibiotics within 1 hour of presentation",
                "concerns": ["Bacterial Meningitis", "Viral Encephalitis", "Tuberculous Meningitis"],
            },

            # RESPIRATORY RED FLAGS
            {
                "name": "severe_breathlessness",
                "category": "RESPIRATORY",
                "required": ["breathlessness"],
                "any_of": ["unable_to_speak", "spo2_below_90", "cyanosis", "altered_consciousness", "respiratory_rate_above_30"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Severe Respiratory Distress",
                "action": "High-flow oxygen, ABG, chest X-ray, consider intubation if SpO2 <85% despite oxygen",
                "time_critical": "Oxygen and monitoring immediately",
                "concerns": ["Severe Pneumonia", "Pulmonary Embolism", "ARDS", "Acute Asthma"],
            },
            {
                "name": "stridor",
                "category": "RESPIRATORY",
                "required": ["stridor"],
                "any_of": ["drooling", "muffled_voice", "tripod_position"],
                "threshold": 0,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Upper Airway Obstruction",
                "action": "Do not examine throat, ENT consult, prepare for emergency airway (cricothyrotomy kit ready)",
                "time_critical": "Potential complete obstruction imminent",
                "concerns": ["Epiglottitis", "Foreign Body", "Angioedema", "Retropharyngeal Abscess"],
            },
            {
                "name": "massive_hemoptysis",
                "category": "RESPIRATORY",
                "required": ["hemoptysis"],
                "any_of": ["large_volume", "hypotension", "tachycardia"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Massive Hemoptysis",
                "action": "Protect airway, IV access, type & cross-match, pulmonology & thoracic surgery consult",
                "time_critical": "Risk of asphyxiation",
                "concerns": ["Pulmonary TB with cavity", "Bronchiectasis", "Lung Cancer", "Pulmonary Embolism"],
            },

            # ABDOMINAL RED FLAGS
            {
                "name": "acute_abdomen",
                "category": "ABDOMINAL",
                "required": ["abdominal_pain"],
                "any_of": ["rigid_abdomen", "rebound_tenderness", "guarding", "hypotension", "tachycardia"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Acute Surgical Abdomen",
                "action": "NPO, IV fluids, analgesics, surgical consult, imaging (CT/USG)",
                "time_critical": "Surgical evaluation within 1 hour",
                "concerns": ["Perforated Viscus", "Ruptured AAA", "Ischemic Bowel", "Ruptured Ectopic"],
            },
            {
                "name": "gi_bleeding",
                "category": "ABDOMINAL",
                "required": [],
                "any_of": ["hematemesis", "melena", "hematochezia", "coffee_ground_vomit"],
                "threshold": 1,
                "urgency": UrgencyLevel.URGENT,
                "description": "GI Bleeding",
                "action": "IV access (2 large bore), IV fluids, type & cross-match 4 units, PPI infusion, GI consult",
                "time_critical": "Resuscitate first, scope within 24 hours if unstable",
                "concerns": ["Peptic Ulcer Bleeding", "Variceal Bleeding", "Mallory-Weiss Tear"],
            },
            {
                "name": "appendicitis",
                "category": "ABDOMINAL",
                "required": ["abdominal_pain_rlq"],
                "any_of": ["fever", "vomiting", "rebound_tenderness", "mcburneys_point_tenderness"],
                "threshold": 2,
                "urgency": UrgencyLevel.URGENT,
                "description": "Possible Acute Appendicitis",
                "action": "NPO, IV fluids, surgical consult, imaging if diagnosis unclear",
                "time_critical": "Surgery within 24 hours to prevent perforation",
                "concerns": ["Acute Appendicitis", "Ovarian Torsion", "Ectopic Pregnancy"],
            },

            # SEPSIS RED FLAGS
            {
                "name": "septic_shock",
                "category": "SEPSIS",
                "required": ["fever"],
                "any_of": ["hypotension", "altered_consciousness", "tachycardia_above_120", "cold_extremities", "mottled_skin"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Septic Shock",
                "action": "IV fluids (30ml/kg bolus), blood cultures x2, broad-spectrum antibiotics within 1 hour, lactate",
                "time_critical": "Each hour delay in antibiotics increases mortality by 7.6%",
                "concerns": ["Septic Shock", "Severe Sepsis"],
            },

            # PEDIATRIC RED FLAGS
            {
                "name": "pediatric_meningitis",
                "category": "PEDIATRIC",
                "required": ["age_below_2"],
                "any_of": ["bulging_fontanelle", "high_pitched_cry", "inconsolable_crying", "fever", "lethargy"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Meningitis in Infant",
                "action": "Empiric antibiotics (ceftriaxone + vancomycin), dexamethasone, LP, PICU consult",
                "time_critical": "Antibiotics within 30 minutes",
                "concerns": ["Bacterial Meningitis", "Viral Meningitis"],
            },
            {
                "name": "non_blanching_rash",
                "category": "PEDIATRIC",
                "required": ["rash_non_blanching"],
                "any_of": ["fever", "lethargy", "vomiting"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Meningococcemia",
                "action": "Immediate IV antibiotics (ceftriaxone), IV fluids, PICU, isolation",
                "time_critical": "Can progress to death within hours",
                "concerns": ["Meningococcemia", "Purpura Fulminans"],
            },

            # OBSTETRIC RED FLAGS
            {
                "name": "preeclampsia_severe",
                "category": "OBSTETRIC",
                "required": ["pregnancy"],
                "any_of": ["severe_headache", "visual_disturbances", "epigastric_pain", "bp_above_160_110"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Severe Preeclampsia/Eclampsia",
                "action": "Magnesium sulfate loading dose, BP control (labetalol), obstetric consult for delivery",
                "time_critical": "Prevent seizures, deliver if term",
                "concerns": ["Severe Preeclampsia", "Eclampsia", "HELLP Syndrome"],
            },
            {
                "name": "antepartum_hemorrhage",
                "category": "OBSTETRIC",
                "required": ["pregnancy", "vaginal_bleeding"],
                "any_of": ["severe_bleeding", "abdominal_pain", "hypotension"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Antepartum Hemorrhage",
                "action": "IV access x2, type & cross-match, fetal monitoring, obstetric consult, prepare for emergency C-section",
                "time_critical": "Maternal and fetal lives at risk",
                "concerns": ["Placenta Previa", "Placental Abruption", "Vasa Previa"],
            },

            # METABOLIC RED FLAGS
            {
                "name": "dka",
                "category": "METABOLIC",
                "required": ["hyperglycemia"],
                "any_of": ["kussmaul_breathing", "fruity_breath", "dehydration", "altered_consciousness"],
                "threshold": 2,
                "urgency": UrgencyLevel.URGENT,
                "description": "Possible Diabetic Ketoacidosis",
                "action": "IV fluids, insulin infusion, K+ replacement, ABG, VBG, electrolytes every 2 hours",
                "time_critical": "Correct gradually over 24-48 hours",
                "concerns": ["Diabetic Ketoacidosis", "HHS"],
            },

            # DENGUE-SPECIFIC (Important for India)
            {
                "name": "dengue_warning_signs",
                "category": "INFECTIOUS",
                "required": ["fever", "dengue_suspected"],
                "any_of": ["abdominal_pain", "persistent_vomiting", "bleeding", "lethargy", "liver_enlargement"],
                "threshold": 1,
                "urgency": UrgencyLevel.WARNING,
                "description": "Dengue Warning Signs",
                "action": "Monitor closely, IV fluids if not tolerating oral, platelet & hematocrit q6h, watch for plasma leakage",
                "time_critical": "Critical phase days 3-7, can progress to shock",
                "concerns": ["Dengue with Warning Signs", "Dengue Hemorrhagic Fever", "Dengue Shock Syndrome"],
            },

            # ADDITIONAL PEDIATRIC RED FLAGS
            {
                "name": "respiratory_distress_child",
                "category": "PEDIATRIC",
                "required": [],
                "any_of": ["stridor", "grunting", "nasal_flaring", "chest_retractions", "cyanosis"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Pediatric Respiratory Distress",
                "action": "High-flow oxygen, pulse oximetry, prepare for intubation, pediatric ICU consult",
                "time_critical": "Can decompensate rapidly in children",
                "concerns": ["Severe Croup", "Bronchiolitis", "Foreign Body Aspiration", "Pneumonia"],
            },
            {
                "name": "epiglottitis",
                "category": "PEDIATRIC",
                "required": ["stridor"],
                "any_of": ["drooling", "tripod_position", "fever", "muffled_voice"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Epiglottitis",
                "action": "Do NOT examine throat, keep child calm, prepare emergency airway, ENT + anesthesia stat",
                "time_critical": "Can cause sudden complete airway obstruction",
                "concerns": ["Epiglottitis", "Retropharyngeal Abscess"],
            },
            {
                "name": "dehydration_severe",
                "category": "PEDIATRIC",
                "required": ["dehydration_signs"],
                "any_of": ["sunken_eyes", "dry_mouth", "no_tears", "lethargy_child", "poor_skin_turgor"],
                "threshold": 2,
                "urgency": UrgencyLevel.URGENT,
                "description": "Severe Dehydration in Child",
                "action": "IV/IO access, fluid bolus 20ml/kg, electrolytes, glucose check",
                "time_critical": "Can lead to hypovolemic shock",
                "concerns": ["Severe Gastroenteritis", "Cholera", "DKA"],
            },
            {
                "name": "febrile_seizure_prolonged",
                "category": "PEDIATRIC",
                "required": ["seizure_child", "fever"],
                "any_of": ["seizure_longer_5_min", "focal_seizure", "multiple_seizures"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Complex Febrile Seizure",
                "action": "Benzodiazepines if still seizing, rule out meningitis, LP if <1 year old",
                "time_critical": "Status epilepticus if >5 minutes",
                "concerns": ["Complex Febrile Seizure", "Meningitis", "Encephalitis"],
            },

            # ADDITIONAL OBSTETRIC RED FLAGS
            {
                "name": "eclampsia",
                "category": "OBSTETRIC",
                "required": ["pregnancy", "seizure"],
                "any_of": ["hypertension", "proteinuria", "headache", "visual_disturbances"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Eclampsia",
                "action": "Magnesium sulfate IV (loading 4g over 20 min), protect airway, BP control, prepare for delivery",
                "time_critical": "Maternal and fetal mortality risk",
                "concerns": ["Eclampsia", "HELLP Syndrome"],
            },
            {
                "name": "ectopic_pregnancy",
                "category": "OBSTETRIC",
                "required": ["vaginal_bleeding"],
                "any_of": ["abdominal_pain", "shoulder_pain", "hypotension", "syncope", "amenorrhea"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Ruptured Ectopic Pregnancy",
                "action": "IV access x2, type & cross-match, FAST scan, gynecology consult for surgery",
                "time_critical": "Can bleed to death from ruptured ectopic",
                "concerns": ["Ruptured Ectopic Pregnancy", "Hemorrhagic Shock"],
            },
            {
                "name": "cord_prolapse",
                "category": "OBSTETRIC",
                "required": ["pregnancy", "leaking_pv"],
                "any_of": ["cord_palpable", "fetal_bradycardia", "variable_decelerations"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Umbilical Cord Prolapse",
                "action": "Knee-chest position, manually elevate presenting part, emergency C-section STAT",
                "time_critical": "Fetal death within minutes from cord compression",
                "concerns": ["Cord Prolapse", "Fetal Asphyxia"],
            },
            {
                "name": "placental_abruption",
                "category": "OBSTETRIC",
                "required": ["pregnancy"],
                "any_of": ["vaginal_bleeding", "severe_abdominal_pain", "rigid_uterus", "fetal_distress"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Placental Abruption",
                "action": "IV access x2, cross-match 4 units, continuous fetal monitoring, prepare for emergency C-section",
                "time_critical": "Maternal and fetal mortality risk",
                "concerns": ["Placental Abruption", "DIC", "Fetal Death"],
            },

            # PSYCHIATRIC RED FLAGS
            {
                "name": "suicidal_with_plan",
                "category": "PSYCHIATRIC",
                "required": ["suicidal_ideation"],
                "any_of": ["suicide_plan", "suicide_attempt", "means_available", "recent_loss"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "High Suicide Risk",
                "action": "1:1 monitoring, remove dangerous objects, psychiatric consult, consider involuntary admission",
                "time_critical": "Imminent risk of self-harm",
                "concerns": ["Major Depression", "Bipolar Disorder", "Psychosis"],
            },
            {
                "name": "acute_psychosis",
                "category": "PSYCHIATRIC",
                "required": [],
                "any_of": ["hearing_voices", "seeing_things", "paranoia", "disorganized_behavior", "agitation"],
                "threshold": 2,
                "urgency": UrgencyLevel.URGENT,
                "description": "Acute Psychosis",
                "action": "Safety assessment, calm environment, consider antipsychotic (haloperidol/olanzapine), psychiatry consult",
                "time_critical": "Risk of harm to self or others",
                "concerns": ["Acute Psychotic Episode", "Schizophrenia", "Bipolar Mania", "Drug-Induced Psychosis"],
            },
            {
                "name": "serotonin_syndrome",
                "category": "PSYCHIATRIC",
                "required": ["psychiatric_medication"],
                "any_of": ["confusion", "agitation", "sweating", "tremor", "hyperthermia", "hyperreflexia"],
                "threshold": 3,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Serotonin Syndrome",
                "action": "Stop serotonergic drugs, supportive care, benzodiazepines, cooling if hyperthermic, ICU admission",
                "time_critical": "Can be fatal if untreated",
                "concerns": ["Serotonin Syndrome", "Neuroleptic Malignant Syndrome"],
            },

            # OPHTHALMOLOGIC RED FLAGS
            {
                "name": "acute_angle_closure_glaucoma",
                "category": "OPHTHALMIC",
                "required": ["eye_pain"],
                "any_of": ["red_eye", "blurred_vision", "halos_around_lights", "headache", "nausea", "hard_eye"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Acute Angle-Closure Glaucoma",
                "action": "IOP measurement, topical beta-blocker + alpha-agonist, IV acetazolamide, ophthalmology STAT",
                "time_critical": "Permanent vision loss within hours",
                "concerns": ["Acute Angle-Closure Glaucoma"],
            },
            {
                "name": "retinal_detachment",
                "category": "OPHTHALMIC",
                "required": [],
                "any_of": ["sudden_vision_loss", "floaters", "flashes_of_light", "curtain_over_vision"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Retinal Detachment",
                "action": "No eye movement, head elevated 30 degrees, urgent ophthalmology consult for surgery",
                "time_critical": "Hours to days for surgical repair",
                "concerns": ["Retinal Detachment", "Vitreous Hemorrhage"],
            },
            {
                "name": "central_retinal_artery_occlusion",
                "category": "OPHTHALMIC",
                "required": ["sudden_vision_loss"],
                "any_of": ["painless", "afferent_pupillary_defect", "cherry_red_spot"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Central Retinal Artery Occlusion",
                "action": "Ocular massage, lower IOP, carbogen if available, ophthalmology STAT (window: 90 minutes)",
                "time_critical": "Irreversible blindness after 90 minutes",
                "concerns": ["Central Retinal Artery Occlusion", "Stroke Equivalent of Eye"],
            },
            {
                "name": "chemical_eye_injury",
                "category": "OPHTHALMIC",
                "required": ["chemical_exposure"],
                "any_of": ["eye_pain", "vision_loss", "corneal_opacity"],
                "threshold": 1,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Chemical Eye Injury",
                "action": "Immediate copious irrigation (30+ minutes), pH check, ophthalmology consult",
                "time_critical": "Every second counts, irrigate BEFORE examination",
                "concerns": ["Alkali Burn", "Acid Burn", "Corneal Perforation"],
            },

            # UROLOGIC RED FLAGS
            {
                "name": "testicular_torsion",
                "category": "UROLOGIC",
                "required": ["testicular_pain"],
                "any_of": ["sudden_onset", "nausea", "vomiting", "high_riding_testis", "absent_cremasteric_reflex"],
                "threshold": 2,
                "urgency": UrgencyLevel.EMERGENCY,
                "description": "Possible Testicular Torsion",
                "action": "Urgent urology consult, Doppler ultrasound only if immediately available, do NOT delay surgery",
                "time_critical": "6-hour window for testicular salvage",
                "concerns": ["Testicular Torsion", "Testicular Infarction"],
            },
            {
                "name": "acute_urinary_retention",
                "category": "UROLOGIC",
                "required": ["urinary_retention"],
                "any_of": ["suprapubic_pain", "distended_bladder", "inability_to_void"],
                "threshold": 1,
                "urgency": UrgencyLevel.URGENT,
                "description": "Acute Urinary Retention",
                "action": "Bladder scan, urethral catheterization (or suprapubic if failed), urology consult",
                "time_critical": "Relief within hours to prevent bladder damage",
                "concerns": ["BPH", "Urethral Stricture", "Neurogenic Bladder", "Post-operative Retention"],
            },
        ]

    def check(self, presentation: Dict[str, any]) -> List[RedFlag]:
        """
        Check for red flag conditions in a clinical presentation.

        Args:
            presentation: Dict containing clinical features
                Example: {
                    "chest_pain": True,
                    "sweating": True,
                    "age": 55,
                    "vital_signs": {"bp": "160/100", "hr": 110}
                }

        Returns:
            List of detected red flags, sorted by urgency
        """
        detected_flags = []

        # Convert presentation to set of present features
        present_features = set()
        for key, value in presentation.items():
            if isinstance(value, bool) and value:
                present_features.add(key)
            elif isinstance(value, str):
                # Add both the key and the value as features
                present_features.add(key)
                present_features.add(value.lower().replace(" ", "_"))
            elif isinstance(value, (int, float)):
                # Add numeric value as feature
                present_features.add(key)
                # Add derived features for vitals
                if key == "age" and value < 2:
                    present_features.add("age_below_2")
                elif key == "spo2" and value < 90:
                    present_features.add("spo2_below_90")
                elif key == "respiratory_rate" and value > 30:
                    present_features.add("respiratory_rate_above_30")
                elif key == "heart_rate" and value > 120:
                    present_features.add("tachycardia_above_120")

        # Check each pattern
        for pattern in self.patterns:
            if self._matches_pattern(pattern, present_features):
                # Find which features triggered this flag
                matching_features = []
                for req in pattern["required"]:
                    if req in present_features:
                        matching_features.append(req)
                for feat in pattern["any_of"]:
                    if feat in present_features:
                        matching_features.append(feat)

                red_flag = RedFlag(
                    category=pattern["category"],
                    description=pattern["description"],
                    urgency=pattern["urgency"],
                    recommended_action=pattern["action"],
                    time_critical=pattern["time_critical"],
                    matching_features=matching_features,
                    differential_concerns=pattern["concerns"],
                )
                detected_flags.append(red_flag)

        # Sort by urgency (EMERGENCY first)
        urgency_order = {
            UrgencyLevel.EMERGENCY: 0,
            UrgencyLevel.URGENT: 1,
            UrgencyLevel.WARNING: 2,
        }
        detected_flags.sort(key=lambda x: urgency_order[x.urgency])

        return detected_flags

    def _matches_pattern(self, pattern: Dict, present_features: Set[str]) -> bool:
        """Check if a pattern matches the present features."""
        # Check all required features are present
        for req in pattern["required"]:
            if req not in present_features:
                return False

        # Check threshold for any_of features
        threshold = pattern.get("threshold", 1)
        any_of_matches = sum(1 for feat in pattern["any_of"] if feat in present_features)

        return any_of_matches >= threshold

    def get_immediate_action(self, red_flag: RedFlag) -> str:
        """
        Get immediate action steps for a red flag.

        Args:
            red_flag: RedFlag object

        Returns:
            Detailed immediate action string
        """
        actions = []

        # Add urgency-based prefix
        if red_flag.urgency == UrgencyLevel.EMERGENCY:
            actions.append("🚨 EMERGENCY - ACT IMMEDIATELY:")
        elif red_flag.urgency == UrgencyLevel.URGENT:
            actions.append("⚠️ URGENT - Action needed within 1 hour:")
        else:
            actions.append("⚡ WARNING - Evaluate within 4-6 hours:")

        # Add specific action
        actions.append(f"\n{red_flag.recommended_action}")

        # Add time critical information
        if red_flag.time_critical:
            actions.append(f"\n⏱️ Time Critical: {red_flag.time_critical}")

        # Add differential concerns
        if red_flag.differential_concerns:
            concerns_str = ", ".join(red_flag.differential_concerns)
            actions.append(f"\n🔍 Consider: {concerns_str}")

        return "\n".join(actions)

    def get_triage_level(self, red_flags: List[RedFlag]) -> str:
        """
        Determine triage level based on red flags.

        Args:
            red_flags: List of detected red flags

        Returns:
            Triage level string
        """
        if not red_flags:
            return "Standard"

        # If any EMERGENCY red flags, triage as Emergency
        if any(rf.urgency == UrgencyLevel.EMERGENCY for rf in red_flags):
            return "Emergency (Red)"

        # If any URGENT red flags, triage as Urgent
        if any(rf.urgency == UrgencyLevel.URGENT for rf in red_flags):
            return "Urgent (Orange)"

        # Otherwise, Semi-urgent
        return "Semi-urgent (Yellow)"
