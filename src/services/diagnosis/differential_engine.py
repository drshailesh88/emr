"""
Differential Diagnosis Engine

Bayesian probability-based differential diagnosis calculator with
India-specific disease prevalence priors.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import math
from collections import defaultdict


@dataclass
class Differential:
    """Represents a differential diagnosis with probability and supporting evidence."""

    diagnosis: str
    probability: float
    supporting_features: List[str] = field(default_factory=list)
    against_features: List[str] = field(default_factory=list)
    suggested_tests: List[str] = field(default_factory=list)
    icd10_code: Optional[str] = None
    severity: str = "moderate"  # mild, moderate, severe, critical

    def __repr__(self) -> str:
        return f"Differential(diagnosis='{self.diagnosis}', probability={self.probability:.2%})"


@dataclass
class Finding:
    """A clinical finding with its likelihood ratio for various diagnoses."""

    name: str
    likelihood_ratios: Dict[str, float]  # diagnosis -> LR+


class DifferentialEngine:
    """
    Calculates differential diagnoses using Bayesian probability with
    India-specific disease prevalence as priors.
    """

    def __init__(self):
        """Initialize with India-specific disease prevalence priors."""
        self._load_india_prevalence()
        self._load_symptom_likelihood_ratios()
        self._load_disease_features()

    def _load_india_prevalence(self) -> None:
        """Load base rate prevalence for common diseases in India."""
        # Prevalence per 100,000 population (approximate)
        self.prevalence = {
            # Infectious diseases (higher in India)
            "tuberculosis": 0.00199,  # 199 per 100k
            "dengue": 0.00132,  # 132 per 100k (seasonal variation)
            "malaria": 0.00058,  # 58 per 100k (regional variation)
            "typhoid": 0.00495,  # 495 per 100k
            "chikungunya": 0.00066,  # 66 per 100k (seasonal)
            "leptospirosis": 0.00011,  # 11 per 100k (monsoon season)
            "viral_fever": 0.02,  # 2% (very common)
            "upper_respiratory_tract_infection": 0.05,  # 5%
            "urinary_tract_infection": 0.015,  # 1.5%
            "gastroenteritis": 0.025,  # 2.5%
            "pneumonia": 0.00313,  # 313 per 100k
            "hepatitis_a": 0.00044,  # 44 per 100k
            "hepatitis_e": 0.00022,  # 22 per 100k

            # Chronic diseases
            "type_2_diabetes": 0.077,  # 7.7% (rapidly increasing)
            "hypertension": 0.254,  # 25.4%
            "ischemic_heart_disease": 0.054,  # 5.4%
            "chronic_kidney_disease": 0.017,  # 1.7%
            "copd": 0.042,  # 4.2%
            "asthma": 0.029,  # 2.9%
            "hypothyroidism": 0.11,  # 11% (very common, especially women)

            # Acute conditions
            "acute_coronary_syndrome": 0.00015,  # 15 per 100k
            "stroke": 0.00119,  # 119 per 100k
            "acute_appendicitis": 0.0001,  # 10 per 100k
            "cholecystitis": 0.00008,  # 8 per 100k
            "pancreatitis": 0.00003,  # 3 per 100k
            "peptic_ulcer_disease": 0.008,  # 0.8%
            "gerd": 0.075,  # 7.5%

            # Other common conditions
            "migraine": 0.015,  # 1.5%
            "tension_headache": 0.03,  # 3%
            "allergic_rhinitis": 0.02,  # 2%
            "anemia": 0.535,  # 53.5% (iron deficiency very common)
            "vitamin_d_deficiency": 0.7,  # 70% (extremely common)
            "dyslipidemia": 0.25,  # 25%

            # Pediatric conditions
            "meningitis": 0.00003,  # 3 per 100k (higher in children)
            "croup": 0.00050,  # 50 per 100k
            "epiglottitis": 0.000005,  # 0.5 per 100k (rare, Hib vaccine)
            "febrile_seizure": 0.00020,  # 20 per 100k
            "intussusception": 0.00010,  # 10 per 100k
            "otitis_media": 0.02,  # 2% (very common in children)
            "foreign_body_aspiration": 0.00005,  # 5 per 100k
            "sepsis": 0.00015,  # 15 per 100k
            "cholera": 0.00002,  # 2 per 100k (endemic areas)
            "dehydration": 0.01,  # 1%

            # Obstetric conditions
            "preeclampsia": 0.00050,  # 50 per 100k pregnancies (~3-5% of pregnancies)
            "eclampsia": 0.00010,  # 10 per 100k pregnancies
            "ectopic_pregnancy": 0.00020,  # 20 per 100k women of reproductive age
            "threatened_abortion": 0.00100,  # 100 per 100k
            "placenta_previa": 0.00050,  # 50 per 100k pregnancies
            "placental_abruption": 0.00030,  # 30 per 100k pregnancies
            "hellp_syndrome": 0.00015,  # 15 per 100k pregnancies
            "premature_rupture_of_membranes": 0.00080,  # 80 per 100k pregnancies
            "labor": 0.00200,  # 200 per 100k (active labor)
            "preterm_labor": 0.00100,  # 100 per 100k
            "fetal_distress": 0.00050,  # 50 per 100k

            # Psychiatric conditions
            "major_depression": 0.042,  # 4.2%
            "bipolar_disorder": 0.010,  # 1.0%
            "schizophrenia": 0.003,  # 0.3%
            "generalized_anxiety_disorder": 0.031,  # 3.1%
            "panic_disorder": 0.023,  # 2.3%
            "borderline_personality_disorder": 0.016,  # 1.6%
            "delirium": 0.00050,  # 50 per 100k
            "dementia": 0.018,  # 1.8% (increases with age)

            # Ophthalmologic conditions
            "acute_angle_closure_glaucoma": 0.00005,  # 5 per 100k
            "retinal_detachment": 0.00010,  # 10 per 100k
            "central_retinal_artery_occlusion": 0.000005,  # 0.5 per 100k
            "conjunctivitis": 0.01,  # 1%
            "uveitis": 0.00020,  # 20 per 100k
            "scleritis": 0.00005,  # 5 per 100k
            "corneal_ulcer": 0.00015,  # 15 per 100k

            # Dermatologic conditions
            "urticaria": 0.01,  # 1%
            "atopic_dermatitis": 0.015,  # 1.5%
            "scabies": 0.005,  # 0.5%
            "herpes_zoster": 0.003,  # 0.3%
            "alopecia_areata": 0.002,  # 0.2%

            # Urologic conditions
            "kidney_stones": 0.007,  # 0.7%
            "pyelonephritis": 0.002,  # 0.2%
            "benign_prostatic_hyperplasia": 0.08,  # 8% (men >50)
            "prostatitis": 0.005,  # 0.5%
            "testicular_torsion": 0.000025,  # 2.5 per 100k
            "epididymitis": 0.00060,  # 60 per 100k
            "urethritis": 0.008,  # 0.8%
        }

    def _load_symptom_likelihood_ratios(self) -> None:
        """
        Load likelihood ratios (LR+) for symptoms in various diagnoses.
        LR+ = sensitivity / (1 - specificity)
        LR+ > 10: Strong evidence for diagnosis
        LR+ 5-10: Moderate evidence
        LR+ 2-5: Weak evidence
        LR+ 1: No diagnostic value
        """
        self.likelihood_ratios = {
            # Fever patterns
            "fever_continuous": {
                "typhoid": 8.0,
                "tuberculosis": 3.5,
                "pneumonia": 4.0,
                "urinary_tract_infection": 3.0,
            },
            "fever_intermittent": {
                "malaria": 12.0,
                "tuberculosis": 4.0,
                "viral_fever": 2.5,
            },
            "fever_with_rash": {
                "dengue": 15.0,
                "chikungunya": 12.0,
                "viral_fever": 3.0,
                "typhoid": 2.0,  # Rose spots
            },
            "fever_with_headache": {
                "dengue": 8.0,
                "malaria": 6.0,
                "typhoid": 5.0,
                "viral_fever": 3.0,
            },
            "fever_with_body_ache": {
                "dengue": 20.0,
                "chikungunya": 25.0,
                "influenza": 10.0,
                "leptospirosis": 8.0,
            },
            "fever_with_jaundice": {
                "leptospirosis": 15.0,
                "hepatitis_a": 12.0,
                "hepatitis_e": 12.0,
                "malaria": 8.0,
            },

            # Respiratory symptoms
            "cough_dry": {
                "upper_respiratory_tract_infection": 5.0,
                "allergic_rhinitis": 4.0,
                "asthma": 6.0,
                "gerd": 3.0,
            },
            "cough_productive": {
                "pneumonia": 8.0,
                "tuberculosis": 10.0,
                "copd": 7.0,
                "bronchitis": 6.0,
            },
            "breathlessness": {
                "asthma": 12.0,
                "copd": 10.0,
                "pneumonia": 8.0,
                "acute_coronary_syndrome": 6.0,
                "anemia": 3.0,
            },
            "chest_pain_pleuritic": {
                "pneumonia": 10.0,
                "pulmonary_embolism": 8.0,
            },

            # Cardiac symptoms
            "chest_pain_crushing": {
                "acute_coronary_syndrome": 20.0,
            },
            "chest_pain_with_sweating": {
                "acute_coronary_syndrome": 15.0,
            },
            "chest_pain_radiating_to_arm": {
                "acute_coronary_syndrome": 12.0,
            },
            "palpitations": {
                "hyperthyroidism": 8.0,
                "anemia": 4.0,
                "anxiety": 3.0,
            },

            # GI symptoms
            "abdominal_pain_epigastric": {
                "peptic_ulcer_disease": 10.0,
                "gerd": 8.0,
                "pancreatitis": 6.0,
                "acute_coronary_syndrome": 2.0,  # Atypical presentation
            },
            "abdominal_pain_right_upper_quadrant": {
                "cholecystitis": 12.0,
                "hepatitis_a": 6.0,
            },
            "abdominal_pain_right_lower_quadrant": {
                "acute_appendicitis": 15.0,
            },
            "diarrhea": {
                "gastroenteritis": 15.0,
                "typhoid": 8.0,
                "inflammatory_bowel_disease": 6.0,
            },
            "vomiting": {
                "gastroenteritis": 12.0,
                "dengue": 8.0,
                "typhoid": 6.0,
            },

            # Neurological
            "headache_severe_sudden": {
                "subarachnoid_hemorrhage": 20.0,
                "meningitis": 12.0,
            },
            "headache_with_neck_stiffness": {
                "meningitis": 25.0,
                "subarachnoid_hemorrhage": 15.0,
            },
            "headache_throbbing_unilateral": {
                "migraine": 15.0,
            },
            "weakness_focal": {
                "stroke": 20.0,
            },

            # Joint symptoms
            "joint_pain_multiple": {
                "chikungunya": 20.0,
                "dengue": 8.0,
                "rheumatoid_arthritis": 10.0,
            },
            "joint_pain_severe": {
                "chikungunya": 25.0,  # "Break-bone fever"
                "gout": 15.0,
            },

            # Urinary symptoms
            "dysuria": {
                "urinary_tract_infection": 20.0,
            },
            "urinary_frequency": {
                "urinary_tract_infection": 15.0,
                "type_2_diabetes": 4.0,
            },

            # Constitutional symptoms
            "weight_loss": {
                "tuberculosis": 12.0,
                "type_2_diabetes": 8.0,
                "hyperthyroidism": 10.0,
                "malignancy": 15.0,
            },
            "night_sweats": {
                "tuberculosis": 15.0,
                "lymphoma": 10.0,
            },
            "fatigue": {
                "anemia": 8.0,
                "hypothyroidism": 10.0,
                "type_2_diabetes": 5.0,
                "vitamin_d_deficiency": 4.0,
            },

            # PEDIATRIC SYMPTOMS
            "crying_excessively": {
                "meningitis": 12.0,
                "intussusception": 10.0,
                "otitis_media": 8.0,
                "colic": 6.0,
            },
            "not_feeding": {
                "meningitis": 15.0,
                "sepsis": 12.0,
                "pneumonia": 8.0,
                "gastroenteritis": 7.0,
            },
            "lethargy_child": {
                "meningitis": 20.0,
                "sepsis": 18.0,
                "hypoglycemia": 12.0,
                "dehydration": 8.0,
            },
            "bulging_fontanelle": {
                "meningitis": 25.0,
                "hydrocephalus": 15.0,
            },
            "stridor": {
                "croup": 15.0,
                "epiglottitis": 20.0,
                "foreign_body_aspiration": 12.0,
            },
            "barking_cough": {
                "croup": 20.0,
            },
            "drooling": {
                "epiglottitis": 25.0,
                "peritonsillar_abscess": 12.0,
            },
            "dehydration_signs": {
                "gastroenteritis": 15.0,
                "cholera": 12.0,
                "diabetic_ketoacidosis": 10.0,
            },
            "seizure_child": {
                "febrile_seizure": 10.0,
                "meningitis": 15.0,
                "epilepsy": 12.0,
                "hypoglycemia": 8.0,
            },
            "febrile_convulsion": {
                "febrile_seizure": 20.0,
                "meningitis": 10.0,
            },

            # OBSTETRIC SYMPTOMS
            "vaginal_bleeding": {
                "threatened_abortion": 12.0,
                "ectopic_pregnancy": 15.0,
                "placenta_previa": 10.0,
                "placental_abruption": 12.0,
            },
            "leaking_pv": {
                "premature_rupture_of_membranes": 20.0,
                "labor": 15.0,
            },
            "decreased_fetal_movements": {
                "fetal_distress": 15.0,
                "placental_insufficiency": 10.0,
            },
            "contractions": {
                "labor": 20.0,
                "preterm_labor": 12.0,
                "braxton_hicks": 5.0,
            },
            "headache_with_high_bp": {
                "preeclampsia": 20.0,
                "eclampsia": 15.0,
                "chronic_hypertension": 8.0,
            },
            "visual_disturbances": {
                "preeclampsia": 18.0,
                "eclampsia": 20.0,
                "migraine": 8.0,
            },
            "swelling_feet_face": {
                "preeclampsia": 12.0,
                "normal_pregnancy_edema": 6.0,
                "nephrotic_syndrome": 10.0,
            },
            "epigastric_pain_pregnancy": {
                "preeclampsia": 15.0,
                "hellp_syndrome": 18.0,
            },

            # PSYCHIATRIC SYMPTOMS
            "suicidal_ideation": {
                "major_depression": 20.0,
                "bipolar_disorder": 12.0,
                "schizophrenia": 10.0,
            },
            "self_harm": {
                "borderline_personality_disorder": 15.0,
                "major_depression": 12.0,
            },
            "hearing_voices": {
                "schizophrenia": 25.0,
                "bipolar_disorder_psychotic": 15.0,
                "psychotic_depression": 12.0,
            },
            "seeing_things": {
                "schizophrenia": 20.0,
                "delirium": 15.0,
                "substance_withdrawal": 10.0,
            },
            "insomnia": {
                "anxiety_disorder": 8.0,
                "major_depression": 10.0,
                "hyperthyroidism": 6.0,
            },
            "racing_thoughts": {
                "bipolar_disorder_manic": 20.0,
                "anxiety_disorder": 10.0,
                "adhd": 8.0,
            },
            "excessive_worry": {
                "generalized_anxiety_disorder": 18.0,
                "panic_disorder": 12.0,
                "major_depression": 8.0,
            },
            "panic_attacks": {
                "panic_disorder": 25.0,
                "generalized_anxiety_disorder": 12.0,
                "hyperthyroidism": 6.0,
            },
            "memory_problems": {
                "dementia": 20.0,
                "depression": 8.0,
                "hypothyroidism": 6.0,
                "vitamin_b12_deficiency": 8.0,
            },
            "confusion": {
                "delirium": 20.0,
                "dementia": 12.0,
                "hypoglycemia": 15.0,
                "stroke": 10.0,
            },

            # OPHTHALMOLOGIC SYMPTOMS
            "sudden_vision_loss": {
                "retinal_detachment": 20.0,
                "central_retinal_artery_occlusion": 18.0,
                "acute_angle_closure_glaucoma": 15.0,
                "stroke": 12.0,
            },
            "floaters": {
                "retinal_detachment": 15.0,
                "posterior_vitreous_detachment": 10.0,
                "vitreous_hemorrhage": 12.0,
            },
            "red_eye": {
                "conjunctivitis": 12.0,
                "acute_angle_closure_glaucoma": 15.0,
                "uveitis": 10.0,
                "scleritis": 8.0,
            },
            "photophobia": {
                "acute_angle_closure_glaucoma": 18.0,
                "uveitis": 15.0,
                "meningitis": 12.0,
                "migraine": 8.0,
            },
            "eye_pain": {
                "acute_angle_closure_glaucoma": 20.0,
                "uveitis": 12.0,
                "scleritis": 10.0,
                "corneal_ulcer": 15.0,
            },
            "double_vision": {
                "stroke": 15.0,
                "myasthenia_gravis": 12.0,
                "third_nerve_palsy": 18.0,
            },

            # DERMATOLOGIC SYMPTOMS
            "itching": {
                "urticaria": 10.0,
                "atopic_dermatitis": 12.0,
                "scabies": 15.0,
                "cholestatic_liver_disease": 8.0,
            },
            "rash": {
                "viral_exanthem": 8.0,
                "drug_reaction": 10.0,
                "allergic_reaction": 12.0,
            },
            "blisters": {
                "herpes_zoster": 15.0,
                "pemphigus": 12.0,
                "bullous_pemphigoid": 10.0,
                "stevens_johnson_syndrome": 18.0,
            },
            "hair_loss": {
                "alopecia_areata": 12.0,
                "telogen_effluvium": 10.0,
                "hypothyroidism": 8.0,
            },

            # UROLOGIC SYMPTOMS
            "burning_urination": {
                "urinary_tract_infection": 20.0,
                "urethritis": 15.0,
                "prostatitis": 10.0,
            },
            "blood_in_urine": {
                "urinary_tract_infection": 12.0,
                "kidney_stones": 15.0,
                "bladder_cancer": 10.0,
                "glomerulonephritis": 12.0,
            },
            "urinary_retention": {
                "benign_prostatic_hyperplasia": 15.0,
                "urethral_stricture": 12.0,
                "neurogenic_bladder": 10.0,
            },
            "flank_pain": {
                "kidney_stones": 20.0,
                "pyelonephritis": 15.0,
                "renal_infarction": 10.0,
            },
            "testicular_pain": {
                "testicular_torsion": 25.0,
                "epididymitis": 15.0,
                "orchitis": 10.0,
            },
        }

    def _load_disease_features(self) -> None:
        """Load characteristic features and distinguishing tests for diagnoses."""
        self.disease_features = {
            "dengue": {
                "classic_triad": ["fever", "headache", "body_ache"],
                "warning_signs": ["abdominal_pain", "persistent_vomiting", "bleeding"],
                "distinguishing_tests": ["NS1 antigen", "Dengue IgM/IgG", "Platelet count", "Hematocrit"],
            },
            "malaria": {
                "classic_features": ["intermittent_fever", "chills", "sweating"],
                "distinguishing_tests": ["Peripheral smear", "Rapid malaria antigen", "QBC"],
            },
            "typhoid": {
                "classic_features": ["step-ladder fever", "relative_bradycardia", "rose_spots"],
                "distinguishing_tests": ["Blood culture", "Widal test", "Typhidot"],
            },
            "tuberculosis": {
                "classic_features": ["prolonged_fever", "night_sweats", "weight_loss", "cough>2weeks"],
                "distinguishing_tests": ["Chest X-ray", "Sputum AFB", "CBNAAT/GeneXpert", "Mantoux test"],
            },
            "acute_coronary_syndrome": {
                "classic_features": ["crushing_chest_pain", "radiation_to_arm", "sweating"],
                "distinguishing_tests": ["ECG", "Troponin I/T", "2D Echo"],
            },
            "pneumonia": {
                "classic_features": ["fever", "productive_cough", "breathlessness", "pleuritic_chest_pain"],
                "distinguishing_tests": ["Chest X-ray", "CBC", "CRP", "SpO2"],
            },
        }

    def calculate_differentials(
        self,
        symptoms: List[str],
        patient: Optional[Dict] = None,
    ) -> List[Differential]:
        """
        Calculate differential diagnoses using Bayesian probability.

        Args:
            symptoms: List of presenting symptoms (e.g., ["fever", "headache", "body_ache"])
            patient: Optional patient context (age, gender, comorbidities, location)

        Returns:
            List of Differential objects sorted by probability (highest first)
        """
        if not symptoms:
            return []

        # Start with all diagnoses and their prior probabilities
        posterior_probs = {}
        supporting_features = defaultdict(list)

        # Adjust priors based on patient context
        priors = self._adjust_priors(patient)

        # Calculate posterior probability for each diagnosis
        for diagnosis, prior in priors.items():
            # Start with prior probability (base rate)
            log_odds = math.log(prior / (1 - prior))

            # Update with likelihood ratios from symptoms
            for symptom in symptoms:
                if symptom in self.likelihood_ratios:
                    lr_dict = self.likelihood_ratios[symptom]
                    if diagnosis in lr_dict:
                        lr = lr_dict[diagnosis]
                        log_odds += math.log(lr)
                        supporting_features[diagnosis].append(symptom)

            # Convert log odds back to probability
            odds = math.exp(log_odds)
            posterior_probs[diagnosis] = odds / (1 + odds)

        # Filter out very low probability diagnoses
        threshold = 0.01  # 1%
        significant_diagnoses = {
            dx: prob for dx, prob in posterior_probs.items() if prob >= threshold
        }

        # Normalize probabilities to sum to 1
        total_prob = sum(significant_diagnoses.values())
        if total_prob > 0:
            normalized_probs = {
                dx: prob / total_prob for dx, prob in significant_diagnoses.items()
            }
        else:
            normalized_probs = {}

        # Create Differential objects
        differentials = []
        for diagnosis, probability in normalized_probs.items():
            diff = Differential(
                diagnosis=diagnosis,
                probability=probability,
                supporting_features=supporting_features[diagnosis],
                against_features=[],  # Can be calculated by checking absent expected features
                suggested_tests=self._get_diagnostic_tests(diagnosis),
            )
            differentials.append(diff)

        # Sort by probability (highest first)
        differentials.sort(key=lambda x: x.probability, reverse=True)

        # Limit to top 10 most likely diagnoses
        return differentials[:10]

    def _adjust_priors(self, patient: Optional[Dict] = None) -> Dict[str, float]:
        """
        Adjust prior probabilities based on patient demographics and context.

        Args:
            patient: Dict with keys like age, gender, location, season, comorbidities

        Returns:
            Adjusted prior probabilities
        """
        priors = self.prevalence.copy()

        if not patient:
            return priors

        age = patient.get("age")
        gender = patient.get("gender")
        season = patient.get("season")  # monsoon, summer, winter
        location = patient.get("location")  # urban, rural

        # Age adjustments
        if age:
            if age < 18:
                # Pediatric adjustments
                priors["viral_fever"] *= 2.0
                priors["upper_respiratory_tract_infection"] *= 1.5
                priors["acute_coronary_syndrome"] *= 0.01
                priors["type_2_diabetes"] *= 0.1
            elif age > 60:
                # Geriatric adjustments
                priors["acute_coronary_syndrome"] *= 3.0
                priors["stroke"] *= 4.0
                priors["type_2_diabetes"] *= 1.5
                priors["hypertension"] *= 1.8

        # Seasonal adjustments
        if season == "monsoon":
            priors["dengue"] *= 5.0
            priors["malaria"] *= 4.0
            priors["leptospirosis"] *= 10.0
            priors["chikungunya"] *= 5.0
        elif season == "summer":
            priors["dengue"] *= 2.0
            priors["typhoid"] *= 2.0

        # Location adjustments
        if location == "rural":
            priors["malaria"] *= 2.0
            priors["tuberculosis"] *= 1.5
            priors["leptospirosis"] *= 3.0

        # Gender adjustments
        if gender == "F":
            priors["urinary_tract_infection"] *= 3.0
            priors["hypothyroidism"] *= 2.0
            priors["anemia"] *= 1.5

        # Ensure probabilities are valid
        for diagnosis in priors:
            priors[diagnosis] = min(priors[diagnosis], 0.99)  # Cap at 99%
            priors[diagnosis] = max(priors[diagnosis], 0.0001)  # Floor at 0.01%

        return priors

    def _get_diagnostic_tests(self, diagnosis: str) -> List[str]:
        """Get recommended diagnostic tests for a diagnosis."""
        if diagnosis in self.disease_features:
            return self.disease_features[diagnosis].get("distinguishing_tests", [])

        # Default tests by category
        test_map = {
            "infectious": ["CBC", "CRP", "ESR"],
            "cardiac": ["ECG", "Troponin", "2D Echo"],
            "respiratory": ["Chest X-ray", "SpO2"],
            "metabolic": ["FBS", "HbA1c", "Lipid profile"],
        }

        # Return generic tests based on diagnosis name
        for category, tests in test_map.items():
            if category in diagnosis.lower():
                return tests

        return ["CBC", "CRP"]

    def get_distinguishing_features(
        self,
        diff1: str,
        diff2: str,
    ) -> List[Tuple[str, str, str]]:
        """
        Get features that would help distinguish between two diagnoses.

        Args:
            diff1: First diagnosis
            diff2: Second diagnosis

        Returns:
            List of tuples: (feature, meaning_for_diff1, meaning_for_diff2)
        """
        distinguishing = []

        # Common differential pairs with distinguishing features
        diff_map = {
            ("dengue", "chikungunya"): [
                ("joint_pain_severity", "Moderate", "Severe (incapacitating)"),
                ("rash_timing", "Day 3-5", "Day 2-3"),
                ("platelet_count", "Usually low", "Normal or mildly low"),
            ],
            ("dengue", "malaria"): [
                ("fever_pattern", "Continuous high", "Intermittent with chills"),
                ("body_ache_severity", "Severe", "Moderate"),
                ("jaundice", "Rare", "Can occur"),
            ],
            ("typhoid", "malaria"): [
                ("fever_pattern", "Step-ladder", "Intermittent"),
                ("pulse", "Relative bradycardia", "Normal or high"),
                ("splenomegaly", "Mild", "Moderate to severe"),
            ],
            ("acute_coronary_syndrome", "gerd"): [
                ("pain_character", "Crushing, pressure", "Burning"),
                ("radiation", "To arm, jaw", "To throat"),
                ("relief_with_antacids", "No", "Yes"),
                ("exertion_related", "Yes", "No"),
            ],
            ("pneumonia", "tuberculosis"): [
                ("onset", "Acute", "Gradual"),
                ("fever_duration", "<1 week", ">2 weeks"),
                ("weight_loss", "Uncommon", "Common"),
                ("chest_xray", "Lobar consolidation", "Apical infiltrates, cavitation"),
            ],
        }

        # Check both orderings
        key = (diff1, diff2)
        if key in diff_map:
            return diff_map[key]

        key_reversed = (diff2, diff1)
        if key_reversed in diff_map:
            # Reverse the meanings
            return [(feat, meaning2, meaning1) for feat, meaning1, meaning2 in diff_map[key_reversed]]

        return []

    def update_probability(
        self,
        current_differentials: List[Differential],
        finding: str,
        present: bool,
    ) -> List[Differential]:
        """
        Update differential probabilities based on new finding.

        Args:
            current_differentials: Current list of differentials
            finding: New clinical finding or test result
            present: Whether the finding is present (True) or absent (False)

        Returns:
            Updated list of differentials
        """
        if finding not in self.likelihood_ratios:
            return current_differentials  # No information gain

        lr_dict = self.likelihood_ratios[finding]

        updated = []
        for diff in current_differentials:
            diagnosis = diff.diagnosis

            # Get likelihood ratio
            if diagnosis in lr_dict:
                if present:
                    lr = lr_dict[diagnosis]
                else:
                    # LR- = (1 - sensitivity) / specificity
                    # Approximate: if LR+ is high, LR- is low
                    lr = 1.0 / lr_dict[diagnosis]
            else:
                lr = 1.0  # No change

            # Update probability using Bayes
            prior_odds = diff.probability / (1 - diff.probability + 1e-10)
            posterior_odds = prior_odds * lr
            new_probability = posterior_odds / (1 + posterior_odds)

            # Update supporting/against features
            new_supporting = diff.supporting_features.copy()
            new_against = diff.against_features.copy()

            if present and lr > 1.5:
                new_supporting.append(finding)
            elif not present and lr < 0.67:
                new_against.append(finding)

            updated_diff = Differential(
                diagnosis=diff.diagnosis,
                probability=new_probability,
                supporting_features=new_supporting,
                against_features=new_against,
                suggested_tests=diff.suggested_tests,
            )
            updated.append(updated_diff)

        # Renormalize probabilities
        total_prob = sum(d.probability for d in updated)
        if total_prob > 0:
            for diff in updated:
                diff.probability /= total_prob

        # Re-sort by probability
        updated.sort(key=lambda x: x.probability, reverse=True)

        return updated
