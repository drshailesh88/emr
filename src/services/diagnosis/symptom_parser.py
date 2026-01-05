"""
Symptom Parser

Extracts symptoms from clinical notes written in medical abbreviations,
English, and Hinglish.
"""

import re
from typing import List, Set


class SymptomParser:
    """
    Parses clinical notes to extract normalized symptom keys.

    Handles:
    - Medical abbreviations (c/o, h/o, k/c, etc.)
    - Hinglish phrases ("fever 3 din se")
    - Composite symptoms (chest pain + radiation = chest_pain_radiating_to_arm)
    """

    def __init__(self):
        """Initialize symptom patterns and mappings."""
        self._load_abbreviations()
        self._load_symptom_patterns()

    def _load_abbreviations(self) -> None:
        """Load common medical abbreviations."""
        self.abbreviations = {
            r'\bc/o\b': 'complains of',
            r'\bh/o\b': 'history of',
            r'\bk/c\b': 'known case of',
            r'\bo/e\b': 'on examination',
            r'\bp/w\b': 'presented with',
            r'\bs/p\b': 'status post',
            r'\bw/\b': 'with',
            r'\bw/o\b': 'without',
            r'\bx\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)': r'for \1 \2',
            r'\bHTN\b': 'hypertension',
            r'\bDM\b': 'diabetes mellitus',
            r'\bIHD\b': 'ischemic heart disease',
            r'\bCAD\b': 'coronary artery disease',
            r'\bCOPD\b': 'chronic obstructive pulmonary disease',
            r'\bCKD\b': 'chronic kidney disease',
            r'\bCVA\b': 'cerebrovascular accident',
            r'\bUTI\b': 'urinary tract infection',
            r'\bURI\b': 'upper respiratory infection',
            r'\bLRTI\b': 'lower respiratory tract infection',
            r'\bACS\b': 'acute coronary syndrome',
            r'\bMI\b': 'myocardial infarction',
            r'\bCHF\b': 'congestive heart failure',
            r'\bTB\b': 'tuberculosis',
            r'\bPUD\b': 'peptic ulcer disease',
            r'\bGERD\b': 'gastroesophageal reflux disease',
        }

        # Hinglish translations
        self.hinglish_phrases = {
            r'\bdin se\b': 'days',
            r'\bhafte se\b': 'weeks',
            r'\bmahine se\b': 'months',
            r'\bsal se\b': 'years',
            r'\bbukhar\b': 'fever',
            r'\bpet dard\b': 'abdominal pain',
            r'\bseene mein dard\b': 'chest pain',
            r'\bsaans phoolna\b': 'breathlessness',
            r'\bsir dard\b': 'headache',
            r'\bkhasi\b': 'cough',
            r'\bulti\b': 'vomiting',
            r'\bdast\b': 'diarrhea',
            r'\bkamzori\b': 'weakness',
            r'\bthakan\b': 'fatigue',
            r'\bthakaan\b': 'fatigue',
            r'\bbadan dard\b': 'body ache',
            r'\bjodo mein dard\b': 'joint pain',
            r'\bchakkar\b': 'dizziness',
            r'\bneend nahi\b': 'insomnia',
            r'\bneend nahi aati\b': 'insomnia',
            r'\bbhookh nahi\b': 'anorexia',
            r'\bpeshab mein jalan\b': 'dysuria',
            r'\bkhoon\b': 'blood',
            r'\bkhoon aana\b': 'bleeding',
            r'\bsoojan\b': 'swelling',
            r'\bkhujli\b': 'itching',
            r'\bpetdard\b': 'abdominal pain',
        }

    def _load_symptom_patterns(self) -> None:
        """Load patterns for detecting specific symptoms."""
        # Each pattern maps to a normalized symptom key from differential_engine
        self.symptom_patterns = {
            # Fever patterns
            'fever_continuous': [
                r'\bcontinuous\s+fever\b',
                r'\bpersistent\s+fever\b',
                r'\bconstant\s+fever\b',
                r'\bhigh\s+grade\s+fever\b',
            ],
            'fever_intermittent': [
                r'\bintermittent\s+fever\b',
                r'\bon\s+and\s+off\s+fever\b',
                r'\bperiodic\s+fever\b',
                r'\bfever\s+with\s+chills\b',
                r'\bchills\s+and\s+rigor\b',
            ],
            'fever_with_rash': [
                r'\bfever\s+with\s+rash\b',
                r'\brash\s+with\s+fever\b',
                r'\bskin\s+rash\b.*\bfever\b',
                r'\bfever\b.*\brash\b',
            ],
            'fever_with_headache': [
                r'\bfever\s+with\s+headache\b',
                r'\bheadache\s+with\s+fever\b',
                r'\bfever\b.*\bheadache\b',
            ],
            'fever_with_body_ache': [
                r'\bfever\s+with\s+body\s+ache\b',
                r'\bbody\s+ache\s+with\s+fever\b',
                r'\bmyalgia\b.*\bfever\b',
                r'\bbody\s+pain\b.*\bfever\b',
            ],
            'fever_with_jaundice': [
                r'\bfever\s+with\s+jaundice\b',
                r'\bjaundice\s+with\s+fever\b',
                r'\byellow\s+eyes\b.*\bfever\b',
                r'\bicterus\b.*\bfever\b',
            ],

            # Respiratory symptoms
            'cough_dry': [
                r'\bdry\s+cough\b',
                r'\bnon[\s-]?productive\s+cough\b',
                r'\birritating\s+cough\b',
            ],
            'cough_productive': [
                r'\bproductive\s+cough\b',
                r'\bcough\s+with\s+sputum\b',
                r'\bcough\s+with\s+expectoration\b',
                r'\bwet\s+cough\b',
            ],
            'breathlessness': [
                r'\bbreathlessness\b',
                r'\bshortness\s+of\s+breath\b',
                r'\bdyspn[oe]a\b',
                r'\bSOB\b',
                r'\bdifficulty\s+breathing\b',
                r'\bsaans\s+phoolna\b',
            ],
            'chest_pain_pleuritic': [
                r'\bpleuritic\s+chest\s+pain\b',
                r'\bchest\s+pain\s+on\s+breathing\b',
                r'\bchest\s+pain\s+worse\s+with\s+breathing\b',
            ],

            # Cardiac symptoms
            'chest_pain_crushing': [
                r'\bcrushing\s+chest\s+pain\b',
                r'\bheavy\s+chest\b',
                r'\bpressure\s+in\s+chest\b',
                r'\belephant\s+on\s+chest\b',
                r'\bsqueezing\s+chest\b',
            ],
            'chest_pain_with_sweating': [
                r'\bchest\s+pain\s+with\s+sweating\b',
                r'\bsweating\s+with\s+chest\s+pain\b',
                r'\bdiaphoresis\b.*\bchest\s+pain\b',
                r'\bchest\s+pain\b.*\bsweating\b',
            ],
            'chest_pain_radiating_to_arm': [
                r'\bchest\s+pain\s+radiating\s+to\s+(left\s+)?arm\b',
                r'\bchest\s+pain\b.*\b(left\s+)?arm\b',
                r'\bradiat(ing|ion)\s+to\s+(left\s+)?arm\b',
                r'\bpain\s+in\s+chest\s+and\s+(left\s+)?arm\b',
            ],
            'palpitations': [
                r'\bpalpitations\b',
                r'\bheart\s+racing\b',
                r'\bfast\s+heartbeat\b',
                r'\birregular\s+heartbeat\b',
            ],

            # GI symptoms
            'abdominal_pain': [
                r'\babdominal\s+pain\b',
                r'\bpet\s+dard\b',
                r'\bpetdard\b',
                r'\bstomach\s+pain\b',
                r'\bbelly\s+pain\b',
            ],
            'abdominal_pain_epigastric': [
                r'\bepigastric\s+pain\b',
                r'\bupper\s+abdominal\s+pain\b',
                r'\bpain\s+in\s+upper\s+abdomen\b',
            ],
            'abdominal_pain_right_upper_quadrant': [
                r'\bright\s+upper\s+quadrant\s+pain\b',
                r'\bRUQ\s+pain\b',
                r'\bright\s+hypochondrium\s+pain\b',
            ],
            'abdominal_pain_right_lower_quadrant': [
                r'\bright\s+lower\s+quadrant\s+pain\b',
                r'\bRLQ\s+pain\b',
                r'\bright\s+iliac\s+fossa\s+pain\b',
                r'\bRIF\s+pain\b',
            ],
            'abdominal_pain_rlq': [  # Alias for red flag detector
                r'\bright\s+lower\s+quadrant\s+pain\b',
                r'\bRLQ\s+pain\b',
                r'\bright\s+iliac\s+fossa\s+pain\b',
            ],
            'diarrhea': [
                r'\bdiarr[he]a\b',
                r'\bloose\s+stools\b',
                r'\bwatery\s+stools\b',
                r'\bdast\b',
            ],
            'vomiting': [
                r'\bvomiting\b',
                r'\bnausea\s+and\s+vomiting\b',
                r'\bemesis\b',
                r'\bulti\b',
            ],

            # Neurological
            'headache': [
                r'\bheadache\b',
                r'\bsir\s+dard\b',
                r'\bsirdard\b',
                r'\bhead\s+pain\b',
            ],
            'headache_severe_sudden': [
                r'\bsevere\s+headache\b',
                r'\bsudden\s+headache\b',
                r'\bworst\s+headache\b',
                r'\bthunderclap\s+headache\b',
            ],
            'headache_with_neck_stiffness': [
                r'\bheadache\s+with\s+neck\s+stiffness\b',
                r'\bneck\s+stiffness\b.*\bheadache\b',
                r'\brigid\s+neck\b.*\bheadache\b',
            ],
            'headache_throbbing_unilateral': [
                r'\bthrobbing\s+headache\b',
                r'\bunilateral\s+headache\b',
                r'\bone[\s-]?sided\s+headache\b',
                r'\bmigraine\b',
            ],
            'weakness_focal': [
                r'\bfocal\s+weakness\b',
                r'\bweakness\s+of\s+(left|right)\s+side\b',
                r'\bhemiparesis\b',
                r'\bfacial\s+droop\b',
                r'\bslurred\s+speech\b',
            ],

            # Joint symptoms
            'joint_pain_multiple': [
                r'\bmultiple\s+joint\s+pain\b',
                r'\bpolyarthralgia\b',
                r'\bpain\s+in\s+multiple\s+joints\b',
                r'\ball\s+joints\s+pain\b',
            ],
            'joint_pain_severe': [
                r'\bsevere\s+joint\s+pain\b',
                r'\bintense\s+joint\s+pain\b',
                r'\bincapacitating\s+joint\s+pain\b',
            ],

            # Urinary symptoms
            'dysuria': [
                r'\bdysuria\b',
                r'\bburning\s+urination\b',
                r'\bpainful\s+urination\b',
                r'\bburning\s+micturition\b',
            ],
            'urinary_frequency': [
                r'\burinary\s+frequency\b',
                r'\bfrequent\s+urination\b',
                r'\bincreased\s+urination\b',
                r'\bpolyuria\b',
            ],

            # Constitutional symptoms
            'weight_loss': [
                r'\bweight\s+loss\b',
                r'\bloss\s+of\s+weight\b',
                r'\bdecreased\s+weight\b',
            ],
            'night_sweats': [
                r'\bnight\s+sweats\b',
                r'\bsweating\s+at\s+night\b',
                r'\bnocturnal\s+sweats\b',
            ],
            'fatigue': [
                r'\bfatigue\b',
                r'\btiredness\b',
                r'\bweakness\b',
                r'\bletharg(y|ic)\b',
                r'\bmalaise\b',
                r'\bkamzori\b',
                r'\bthakaan\b',
            ],

            # Generic symptoms (will be picked up for context)
            'fever': [
                r'\bfever\b',
                r'\bpyrexia\b',
                r'\btemperature\b',
                r'\bbukhar\b',
            ],
            'chest_pain': [
                r'\bchest\s+pain\b',
                r'\bprecordial\s+pain\b',
                r'\bretrosternal\s+pain\b',
                r'\bseene\s+mein\s+dard\b',
            ],
            'sweating': [
                r'\bsweating\b',
                r'\bdiaphoresis\b',
                r'\bperspiration\b',
            ],
            'radiation_to_arm': [
                r'\bradiat(ing|ion)\s+to\s+(left\s+)?arm\b',
                r'\bpain\s+in\s+(left\s+)?arm\b',
                r'\barm\s+pain\b',
            ],

            # PEDIATRIC SYMPTOMS
            'crying_excessively': [
                r'\bcrying\s+excessively\b',
                r'\binconsolable\s+crying\b',
                r'\bhigh[\s-]?pitched\s+cry(ing)?\b',
                r'\bcontinuous\s+crying\b',
                r'\bnot\s+consolable\b',
            ],
            'not_feeding': [
                r'\bnot\s+feeding\b',
                r'\brefusing\s+feeds\b',
                r'\bpoor\s+feeding\b',
                r'\bnot\s+taking\s+(milk|feeds)\b',
                r'\bfeeding\s+difficulty\b',
                r'\bnot\s+taking\s+feeds\b',
            ],
            'lethargy_child': [
                r'\blethargic\b',
                r'\bnot\s+active\b',
                r'\bvery\s+sleepy\b',
                r'\bunresponsive\b',
                r'\bnot\s+responding\b',
            ],
            'rash_with_fever_child': [
                r'\brash\s+with\s+fever\b',
                r'\bfever\s+with\s+rash\b',
                r'\bskin\s+eruption\b.*\bfever\b',
            ],
            'bulging_fontanelle': [
                r'\bbulging\s+fontanelle\b',
                r'\bfontanelle\s+bulging\b',
                r'\btense\s+fontanelle\b',
            ],
            'stridor': [
                r'\bstridor\b',
                r'\bnoisy\s+breathing\b',
                r'\brespiratory\s+noise\b',
            ],
            'barking_cough': [
                r'\bbarking\s+cough\b',
                r'\bcroupy\s+cough\b',
                r'\bseal[\s-]?like\s+cough\b',
            ],
            'drooling': [
                r'\bdrooling\b',
                r'\bexcessive\s+salivation\b',
                r'\bsaliva\s+dripping\b',
            ],
            'vomiting_child': [
                r'\bvomiting\b',
                r'\bprojectile\s+vomiting\b',
                r'\bthrows\s+up\b',
            ],
            'loose_stools': [
                r'\bloose\s+stools\b',
                r'\bwatery\s+stools\b',
                r'\bdiarr[he]a\b',
                r'\bdast\b',
            ],
            'dehydration_signs': [
                r'\bdehydration\b',
                r'\bdry\s+mouth\b',
                r'\bsunken\s+eyes\b',
                r'\bskin\s+turgor\s+decreased\b',
                r'\bno\s+tears\b',
            ],
            'seizure_child': [
                r'\bseizure\b',
                r'\bconvulsion\b',
                r'\bfits\b',
                r'\bjerkings\b',
                r'\bshaking\s+movements\b',
            ],
            'febrile_convulsion': [
                r'\bfebrile\s+convulsion\b',
                r'\bfebrile\s+seizure\b',
                r'\bfits\s+with\s+fever\b',
            ],

            # OBSTETRIC SYMPTOMS
            'vaginal_bleeding': [
                r'\bvaginal\s+bleeding\b',
                r'\bbleeding\s+pv\b',
                r'\bspotting\b',
                r'\bbleeding\s+per\s+vaginum\b',
            ],
            'leaking_pv': [
                r'\bleaking\s+pv\b',
                r'\bwater\s+leaking\b',
                r'\bleaking\s+per\s+vaginum\b',
                r'\bmembrane\s+rupture\b',
                r'\bwater\s+broke\b',
            ],
            'decreased_fetal_movements': [
                r'\bdecreased\s+fetal\s+movements\b',
                r'\bbaby\s+not\s+moving\b',
                r'\breduced\s+kicks\b',
                r'\bno\s+fetal\s+movements\b',
            ],
            'contractions': [
                r'\bcontractions\b',
                r'\blabor\s+pains\b',
                r'\buterine\s+contractions\b',
                r'\bpains\s+coming\s+regularly\b',
            ],
            'headache_with_high_bp': [
                r'\bheadache\s+with\s+(high\s+)?bp\b',
                r'\bheadache\b.*\bhypertension\b',
                r'\bsevere\s+headache\b.*\bpregnancy\b',
            ],
            'visual_disturbances': [
                r'\bvisual\s+disturbances\b',
                r'\bblurred\s+vision\b',
                r'\bseeing\s+spots\b',
                r'\bflashing\s+lights\b',
            ],
            'swelling_feet_face': [
                r'\bswelling\s+of\s+feet\b',
                r'\bswelling\s+of\s+face\b',
                r'\bpedal\s+edema\b',
                r'\bfacial\s+puffiness\b',
                r'\bsoojan\b',
            ],
            'epigastric_pain_pregnancy': [
                r'\bepigastric\s+pain\b.*\bpregnancy\b',
                r'\bupper\s+abdominal\s+pain\b.*\bpregnant\b',
            ],

            # PSYCHIATRIC SYMPTOMS
            'suicidal_ideation': [
                r'\bsuicidal\s+ideation\b',
                r'\bsuicidal\s+thoughts\b',
                r'\bwants\s+to\s+die\b',
                r'\bthinking\s+of\s+suicide\b',
                r'\bwants\s+to\s+kill\s+self\b',
            ],
            'self_harm': [
                r'\bself[\s-]?harm\b',
                r'\bcutting\b',
                r'\bburning\s+self\b',
                r'\bhurt(ing)?\s+(him|her)self\b',
            ],
            'hearing_voices': [
                r'\bhearing\s+voices\b',
                r'\bauditory\s+hallucinations\b',
                r'\bvoices\s+in\s+head\b',
            ],
            'seeing_things': [
                r'\bseeing\s+things\b',
                r'\bvisual\s+hallucinations\b',
                r'\bseeing\s+shadows\b',
            ],
            'insomnia': [
                r'\binsomnia\b',
                r'\bnot\s+sleeping\b',
                r'\bcan\'?t\s+sleep\b',
                r'\bsleep\s+disturbance\b',
                r'\bneend\s+nahi\b',
            ],
            'racing_thoughts': [
                r'\bracing\s+thoughts\b',
                r'\bthoughts\s+racing\b',
                r'\brapid\s+thoughts\b',
                r'\bflight\s+of\s+ideas\b',
            ],
            'excessive_worry': [
                r'\bexcessive\s+worry\b',
                r'\banxiety\b',
                r'\bworrying\s+too\s+much\b',
                r'\bconstant\s+worry\b',
            ],
            'panic_attacks': [
                r'\bpanic\s+attacks\b',
                r'\bpanic\b',
                r'\bsudden\s+fear\b',
                r'\bheart\s+racing\s+with\s+fear\b',
            ],
            'memory_problems': [
                r'\bmemory\s+problems\b',
                r'\bforgetfulness\b',
                r'\bmemory\s+loss\b',
                r'\bcan\'?t\s+remember\b',
            ],
            'confusion': [
                r'\bconfusion\b',
                r'\bconfused\b',
                r'\bdisoriented\b',
                r'\bnot\s+aware\b',
            ],

            # OPHTHALMOLOGIC SYMPTOMS
            'sudden_vision_loss': [
                r'\bsudden\s+vision\s+loss\b',
                r'\bvision\s+loss\b',
                r'\bcan\'?t\s+see\b',
                r'\blost\s+vision\b',
                r'\bblindness\b',
            ],
            'floaters': [
                r'\bfloaters\b',
                r'\bseeing\s+spots\b',
                r'\bflying\s+objects\b',
                r'\bdots\s+in\s+vision\b',
            ],
            'red_eye': [
                r'\bred\s+eye\b',
                r'\beye\s+redness\b',
                r'\bbloodshot\s+eye\b',
            ],
            'photophobia': [
                r'\bphotophobia\b',
                r'\blight\s+sensitivity\b',
                r'\bcan\'?t\s+tolerate\s+light\b',
            ],
            'eye_pain': [
                r'\beye\s+pain\b',
                r'\bpain\s+in\s+eye\b',
                r'\bocular\s+pain\b',
            ],
            'eye_discharge': [
                r'\beye\s+discharge\b',
                r'\bpus\s+from\s+eye\b',
                r'\bwatery\s+eye\b',
                r'\beye\s+secretions\b',
            ],
            'double_vision': [
                r'\bdouble\s+vision\b',
                r'\bdiplopia\b',
                r'\bseeing\s+double\b',
            ],

            # DERMATOLOGIC SYMPTOMS
            'itching': [
                r'\bitching\b',
                r'\bpruritus\b',
                r'\bitchy\s+skin\b',
                r'\bkhujli\b',
            ],
            'rash': [
                r'\brash\b',
                r'\bskin\s+eruption\b',
                r'\bskin\s+lesions\b',
            ],
            'blisters': [
                r'\bblisters\b',
                r'\bvesicles\b',
                r'\bbullae\b',
                r'\bfluid[\s-]?filled\s+lesions\b',
            ],
            'hair_loss': [
                r'\bhair\s+loss\b',
                r'\balopecia\b',
                r'\bbalding\b',
                r'\bhair\s+falling\b',
            ],
            'nail_changes': [
                r'\bnail\s+changes\b',
                r'\bnail\s+discoloration\b',
                r'\bnail\s+thickening\b',
            ],
            'skin_lesions': [
                r'\bskin\s+lesions\b',
                r'\bgrowth\s+on\s+skin\b',
                r'\bbump\b',
                r'\blump\s+on\s+skin\b',
            ],
            'mole_changing': [
                r'\bmole\s+changing\b',
                r'\bmole\s+growing\b',
                r'\bnew\s+mole\b',
                r'\bmole\s+bleeding\b',
            ],

            # UROLOGIC SYMPTOMS
            'burning_urination': [
                r'\bburning\s+urination\b',
                r'\bdysuria\b',
                r'\bpainful\s+urination\b',
                r'\bpeshab\s+mein\s+jalan\b',
            ],
            'urinary_frequency': [
                r'\burinary\s+frequency\b',
                r'\bfrequent\s+urination\b',
                r'\bbar\s+bar\s+peshab\b',
            ],
            'blood_in_urine': [
                r'\bblood\s+in\s+urine\b',
                r'\bhematuria\b',
                r'\bred\s+urine\b',
                r'\bpeshab\s+mein\s+khoon\b',
            ],
            'urinary_retention': [
                r'\burinary\s+retention\b',
                r'\bcan\'?t\s+pass\s+urine\b',
                r'\bunable\s+to\s+urinate\b',
                r'\bpeshab\s+nahi\s+ho\s+raha\b',
            ],
            'flank_pain': [
                r'\bflank\s+pain\b',
                r'\bloin\s+pain\b',
                r'\bside\s+pain\b',
                r'\bkidney\s+pain\b',
            ],
            'testicular_pain': [
                r'\btesticular\s+pain\b',
                r'\bscrotal\s+pain\b',
                r'\bpain\s+in\s+testicle\b',
            ],
        }

    def parse(self, clinical_notes: str) -> List[str]:
        """
        Parse clinical notes to extract symptom keys.

        Args:
            clinical_notes: Raw clinical notes (may contain abbreviations, Hinglish)

        Returns:
            List of normalized symptom keys compatible with DifferentialEngine
        """
        if not clinical_notes:
            return []

        # Normalize text
        text = clinical_notes.lower()

        # Expand abbreviations
        for abbrev, expansion in self.abbreviations.items():
            text = re.sub(abbrev, expansion, text, flags=re.IGNORECASE)

        # Translate Hinglish
        for phrase, translation in self.hinglish_phrases.items():
            text = re.sub(phrase, translation, text, flags=re.IGNORECASE)

        # Extract symptoms
        found_symptoms: Set[str] = set()

        for symptom_key, patterns in self.symptom_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found_symptoms.add(symptom_key)
                    break  # Don't duplicate if multiple patterns match

        # Return sorted for consistency
        return sorted(list(found_symptoms))

    def extract_vitals(self, clinical_notes: str) -> dict:
        """
        Extract vitals from clinical notes for red flag detection.

        Args:
            clinical_notes: Raw clinical notes

        Returns:
            Dict with extracted vitals (bp, hr, spo2, temperature, etc.)
        """
        vitals = {}
        text = clinical_notes.lower()

        # Blood pressure
        bp_match = re.search(r'\bbp\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})', text)
        if bp_match:
            vitals['bp_systolic'] = int(bp_match.group(1))
            vitals['bp_diastolic'] = int(bp_match.group(2))

        # Heart rate / Pulse
        hr_match = re.search(r'\b(?:hr|pulse|pr)\s*[:=]?\s*(\d{2,3})', text)
        if hr_match:
            vitals['heart_rate'] = int(hr_match.group(1))

        # SpO2
        spo2_match = re.search(r'\bspo2?\s*[:=]?\s*(\d{2,3})\s*%?', text)
        if spo2_match:
            vitals['spo2'] = int(spo2_match.group(1))

        # Respiratory rate
        rr_match = re.search(r'\b(?:rr|respiratory\s+rate)\s*[:=]?\s*(\d{1,2})', text)
        if rr_match:
            vitals['respiratory_rate'] = int(rr_match.group(1))

        # Temperature
        temp_match = re.search(r'\btemp(?:erature)?\s*[:=]?\s*(\d{2,3}(?:\.\d)?)\s*[°]?[fc]?', text)
        if temp_match:
            vitals['temperature'] = float(temp_match.group(1))

        return vitals


# Singleton instance
_parser = None

def get_symptom_parser() -> SymptomParser:
    """Get singleton symptom parser instance."""
    global _parser
    if _parser is None:
        _parser = SymptomParser()
    return _parser


def parse_symptoms(clinical_notes: str) -> List[str]:
    """
    Parse clinical notes to extract symptoms.

    Args:
        clinical_notes: Raw clinical notes

    Returns:
        List of normalized symptom keys
    """
    parser = get_symptom_parser()
    return parser.parse(clinical_notes)


def extract_vitals_from_notes(clinical_notes: str) -> dict:
    """
    Extract vitals from clinical notes.

    Args:
        clinical_notes: Raw clinical notes

    Returns:
        Dict with extracted vitals
    """
    parser = get_symptom_parser()
    return parser.extract_vitals(clinical_notes)
