"""Sample speech transcripts in Hindi, English, and Hinglish for testing."""


# ============== ENGLISH TRANSCRIPTS ==============

ENGLISH_FEVER_CASE = """
Patient presents with high-grade fever for three days.
Temperature reaching up to 102 Fahrenheit.
Associated with body ache, headache, and fatigue.
No cough, no breathlessness, no chest pain.
Taking plenty of fluids.
Appetite reduced.
"""

ENGLISH_CHEST_PAIN = """
Patient complains of central chest pain.
Started two hours ago.
Pain radiating to left arm and jaw.
Associated with sweating and nausea.
No relief with rest.
This is the first episode.
"""

ENGLISH_DIABETES_FOLLOWUP = """
Patient is a known case of Type 2 Diabetes for five years.
Currently on Metformin 500 mg twice daily.
Blood sugar levels have been well controlled.
No hypoglycemic episodes.
Diet and exercise compliance good.
Last HbA1c was 7.2 percent three months ago.
"""

# ============== HINDI TRANSCRIPTS ==============

HINDI_FEVER_CASE = """
मरीज को तीन दिन से तेज बुखार है।
बुखार 102 फारेनहाइट तक जा रहा है।
शरीर में दर्द, सिर दर्द और कमजोरी भी है।
खांसी नहीं है, सांस लेने में तकलीफ नहीं।
पानी अच्छे से पी रहे हैं।
भूख कम लग रही है।
"""

HINDI_STOMACH_PAIN = """
मरीज को पेट में दर्द की शिकायत है।
पेट फूला हुआ महसूस होता है।
खाने के बाद दर्द बढ़ जाता है।
कभी-कभी उल्टी जैसा लगता है।
कब्ज की भी समस्या है।
"""

HINDI_BP_COMPLAINT = """
मरीज को सिर दर्द और चक्कर आ रहे हैं।
ब्लड प्रेशर हाई रहता है।
दवाई नियमित ले रहे हैं।
नमक कम खा रहे हैं।
पिछली बार BP 150 बटा 95 था।
"""

# ============== HINGLISH TRANSCRIPTS ==============

HINGLISH_DIABETES = """
Patient ko diabetes hai पांच साल से।
Metformin 500 mg ले रहे हैं twice daily.
Sugar level control में है।
Koi problem नहीं है।
Diet bhi ठीक follow कर रहे हैं।
Exercise daily कर रहे हैं।
"""

HINGLISH_COUGH_COLD = """
Patient को सर्दी और खांसी है तीन दिन से।
Khasi में बलगम भी आ रहा है।
Fever नहीं है but थोड़ी weakness है।
Throat में खराश है।
Voice bhi थोड़ी बैठी हुई है।
"""

HINGLISH_KNEE_PAIN = """
Patient के घुटनों में दर्द है।
Subah उठने के बाद stiffness होती है।
Stairs चढ़ने में problem होती है।
Pain killer लेने से थोड़ा आराम मिलता है।
Calcium और Vitamin D supplements ले रहे हैं।
"""

# ============== MIXED CLINICAL SCENARIOS ==============

CARDIAC_EMERGENCY_ENGLISH = """
Sixty-five year old male presents with severe chest pain.
Pain started suddenly thirty minutes ago while at rest.
Described as crushing, substernal, radiating to left arm.
Associated with profuse sweating and shortness of breath.
Patient looks anxious and distressed.
Past history of hypertension and smoking.
No previous cardiac events.
Family history positive for coronary artery disease.
"""

PEDIATRIC_FEVER_ENGLISH = """
Five year old child brought by mother.
High fever for two days, up to 104 Fahrenheit.
Rash appeared today over trunk and limbs.
Child is playful and taking feeds.
No vomiting or diarrhea.
Vaccination up to date.
Probable viral exanthem.
"""

ANTENATAL_CHECKUP_HINGLISH = """
Patient है 28 weeks pregnant.
Ye है second pregnancy.
Pehli delivery normal thi.
Is baar sab kuch normal चल रहा है।
Baby movements अच्छे हैं।
BP और weight gain भी normal है।
Koi problem नहीं है।
Regular checkups ले रही हैं।
"""

COPD_EXACERBATION_ENGLISH = """
Known case of COPD for ten years.
Increased breathlessness for three days.
Productive cough with yellowish sputum.
Using inhalers regularly but no relief currently.
Wheezing has increased.
Sleep disturbed due to cough.
SpO2 92 percent on room air.
No fever.
"""

UTI_ELDERLY_HINGLISH = """
Elderly female patient with burning urination.
Teen din se problem है।
Frequency भी बढ़ गई है।
Lower abdomen में dull pain है।
Fever नहीं है।
Koi previous UTI history नहीं है।
Diabetes hai patient को।
"""

# ============== VITAL SIGNS IN TRANSCRIPTS ==============

VITALS_MIXED = """
BP is 140 by 90.
Pulse 88 per minute.
Temperature 101 Fahrenheit.
Respiratory rate 18 per minute.
SpO2 96 percent on room air.
Weight है 72 kilograms.
Height 165 centimeters.
BMI approximately 26.
"""

# ============== PRESCRIPTION INSTRUCTIONS ==============

PRESCRIPTION_INSTRUCTIONS_ENGLISH = """
Start the patient on Paracetamol 500 mg thrice daily after meals.
Add Azithromycin 500 mg once daily for three days.
Continue the existing medications.
Plenty of oral fluids.
Rest advised.
Follow up after three days if fever persists.
"""

PRESCRIPTION_INSTRUCTIONS_HINGLISH = """
Patient को Paracetamol 500 mg दें thrice daily khane ke baad.
Cetirizine 10 mg रात को सोते time.
Vitamin C tablets भी दे सकते हैं।
Rest करें aur fluids ज्यादा लें।
Agar fever persist करे to 3 din baad follow-up.
"""

# ============== INVESTIGATION ORDERS ==============

INVESTIGATIONS_ENGLISH = """
Order CBC, ESR, CRP.
Chest X-ray PA view.
Blood sugar fasting and postprandial.
Kidney function tests.
Liver function tests.
Urine routine and microscopy.
ECG.
"""

INVESTIGATIONS_HINGLISH = """
CBC karwa लें.
Sugar fasting aur PP check करें.
Kidney function test bhi karwa दें.
HbA1c if diabetic.
ECG bhi करा लें.
X-ray chest if needed.
"""

# ============== RED FLAG SCENARIOS ==============

RED_FLAG_CARDIAC = """
Severe crushing chest pain with radiation to jaw and left arm.
Profuse diaphoresis.
Shortness of breath.
Patient very anxious.
BP 90 by 60.
Heart rate 120.
Consider acute MI - start ACS protocol.
"""

RED_FLAG_NEURO = """
Worst headache of life.
Sudden onset thunderclap headache.
Associated with vomiting.
Photophobia present.
Neck stiffness.
Consider subarachnoid hemorrhage.
Needs immediate CT head.
"""

RED_FLAG_SEPSIS = """
High fever with rigors.
Blood pressure dropping.
Tachycardia, tachypnea.
Altered sensorium.
Urine output reduced.
Probable septic shock.
Start sepsis protocol immediately.
"""

# ============== HELPER FUNCTIONS ==============

def get_transcript_by_language(case_type: str, language: str) -> str:
    """Get transcript by case type and language."""
    transcript_map = {
        ("fever", "english"): ENGLISH_FEVER_CASE,
        ("fever", "hindi"): HINDI_FEVER_CASE,
        ("diabetes", "english"): ENGLISH_DIABETES_FOLLOWUP,
        ("diabetes", "hinglish"): HINGLISH_DIABETES,
        ("chest_pain", "english"): ENGLISH_CHEST_PAIN,
        ("cardiac_emergency", "english"): CARDIAC_EMERGENCY_ENGLISH,
        ("cough", "hinglish"): HINGLISH_COUGH_COLD,
        ("pediatric", "english"): PEDIATRIC_FEVER_ENGLISH,
    }

    return transcript_map.get((case_type, language), "")


def get_all_transcripts():
    """Get all sample transcripts."""
    return {
        "english": {
            "fever": ENGLISH_FEVER_CASE,
            "chest_pain": ENGLISH_CHEST_PAIN,
            "diabetes": ENGLISH_DIABETES_FOLLOWUP,
            "cardiac_emergency": CARDIAC_EMERGENCY_ENGLISH,
            "pediatric": PEDIATRIC_FEVER_ENGLISH,
            "copd": COPD_EXACERBATION_ENGLISH,
        },
        "hindi": {
            "fever": HINDI_FEVER_CASE,
            "stomach_pain": HINDI_STOMACH_PAIN,
            "bp": HINDI_BP_COMPLAINT,
        },
        "hinglish": {
            "diabetes": HINGLISH_DIABETES,
            "cough": HINGLISH_COUGH_COLD,
            "knee_pain": HINGLISH_KNEE_PAIN,
            "anc": ANTENATAL_CHECKUP_HINGLISH,
            "uti": UTI_ELDERLY_HINGLISH,
        },
        "red_flags": {
            "cardiac": RED_FLAG_CARDIAC,
            "neuro": RED_FLAG_NEURO,
            "sepsis": RED_FLAG_SEPSIS,
        }
    }
