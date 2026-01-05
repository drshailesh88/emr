"""Drug interaction scenario fixtures for DocAssist EMR testing."""

from typing import Dict, List
from src.models.schemas import SafetyAlert


# ============== DRUG INTERACTION SCENARIOS ==============

INTERACTION_SCENARIOS = {
    # Major interactions (high risk)
    'warfarin_aspirin': {
        'current': ['Warfarin 5mg OD'],
        'new': ['Aspirin 325mg OD'],
        'expected_severity': 'CRITICAL',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'Major bleeding risk: Warfarin + Aspirin',
        'description': 'Increased risk of bleeding - both are anticoagulants/antiplatelets',
        'clinical_notes': 'Only combine if benefit outweighs risk. Monitor INR closely. Watch for bleeding signs.',
        'alternatives': ['Clopidogrel (if antiplatelet needed)', 'Consider NOAC instead of warfarin']
    },

    'warfarin_nsaid': {
        'current': ['Warfarin 5mg OD'],
        'new': ['Ibuprofen 400mg TDS'],
        'expected_severity': 'CRITICAL',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'Major bleeding risk: Warfarin + NSAID',
        'description': 'NSAIDs increase bleeding risk and may displace warfarin from protein binding',
        'clinical_notes': 'Avoid NSAIDs in patients on warfarin. Use paracetamol instead.',
        'alternatives': ['Paracetamol 500mg TDS for pain']
    },

    'metformin_contrast': {
        'current': ['Metformin 500mg BD'],
        'new': ['CT scan with contrast'],
        'expected_severity': 'HIGH',
        'expected_category': 'contraindication',
        'expected_action': 'WARN',
        'expected_message': 'Hold metformin before contrast study - risk of lactic acidosis',
        'description': 'Iodinated contrast + metformin can cause lactic acidosis in renal impairment',
        'clinical_notes': 'Stop metformin 48 hours before and after contrast. Check kidney function.',
        'alternatives': ['Temporarily switch to insulin if needed']
    },

    'ssri_maoi': {
        'current': ['Fluoxetine 20mg OD'],
        'new': ['Phenelzine 15mg BD'],
        'expected_severity': 'CRITICAL',
        'expected_category': 'contraindication',
        'expected_action': 'BLOCK',
        'expected_message': 'CONTRAINDICATED: SSRI + MAOI can cause serotonin syndrome',
        'description': 'Life-threatening serotonin syndrome',
        'clinical_notes': 'Absolute contraindication. Washout period of 5 weeks required after stopping SSRI.',
        'alternatives': ['Wait 5 weeks after stopping fluoxetine before starting MAOI']
    },

    'ace_inhibitor_potassium': {
        'current': ['Ramipril 5mg OD', 'Potassium Chloride 600mg BD'],
        'new': [],
        'expected_severity': 'HIGH',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'Hyperkalemia risk: ACE inhibitor + Potassium supplement',
        'description': 'ACE inhibitors reduce potassium excretion',
        'clinical_notes': 'Monitor serum potassium levels. May need to stop potassium supplement.',
        'alternatives': []
    },

    'ace_inhibitor_arb': {
        'current': ['Ramipril 5mg OD'],
        'new': ['Telmisartan 40mg OD'],
        'expected_severity': 'HIGH',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'Dual RAAS blockade: ACE inhibitor + ARB',
        'description': 'Increased risk of hypotension, hyperkalemia, and renal dysfunction',
        'clinical_notes': 'Generally not recommended. Use only in specific heart failure cases.',
        'alternatives': ['Use either ACE-I or ARB, not both']
    },

    'statin_grapefruit': {
        'current': ['Atorvastatin 40mg OD'],
        'new': ['Grapefruit juice'],
        'expected_severity': 'MEDIUM',
        'expected_category': 'interaction',
        'expected_action': 'INFO',
        'expected_message': 'Grapefruit juice increases statin levels',
        'description': 'Grapefruit inhibits CYP3A4, increasing statin levels and myopathy risk',
        'clinical_notes': 'Advise patient to avoid grapefruit juice while on statins.',
        'alternatives': ['Use rosuvastatin (less affected by grapefruit)']
    },

    'methotrexate_nsaid': {
        'current': ['Methotrexate 15mg weekly'],
        'new': ['Diclofenac 50mg BD'],
        'expected_severity': 'HIGH',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'NSAIDs increase methotrexate toxicity',
        'description': 'NSAIDs reduce methotrexate excretion, increasing toxicity risk',
        'clinical_notes': 'Avoid NSAIDs. Monitor CBC and liver function closely if must use.',
        'alternatives': ['Paracetamol for pain']
    },

    'digoxin_amiodarone': {
        'current': ['Digoxin 0.25mg OD'],
        'new': ['Amiodarone 200mg OD'],
        'expected_severity': 'HIGH',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'Amiodarone increases digoxin levels',
        'description': 'Amiodarone inhibits P-glycoprotein, increasing digoxin levels',
        'clinical_notes': 'Reduce digoxin dose by 50%. Monitor digoxin levels.',
        'alternatives': []
    },

    'phenytoin_fluconazole': {
        'current': ['Phenytoin 300mg OD'],
        'new': ['Fluconazole 200mg OD'],
        'expected_severity': 'HIGH',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'Fluconazole increases phenytoin levels',
        'description': 'Azoles inhibit CYP2C9, increasing phenytoin levels and toxicity risk',
        'clinical_notes': 'Monitor phenytoin levels. May need dose adjustment.',
        'alternatives': ['Consider alternative antifungal']
    },

    # Moderate interactions
    'amlodipine_simvastatin': {
        'current': ['Amlodipine 10mg OD'],
        'new': ['Simvastatin 80mg OD'],
        'expected_severity': 'MEDIUM',
        'expected_category': 'interaction',
        'expected_action': 'WARN',
        'expected_message': 'Amlodipine increases simvastatin levels',
        'description': 'Increased risk of myopathy and rhabdomyolysis',
        'clinical_notes': 'Limit simvastatin to 20mg when used with amlodipine.',
        'alternatives': ['Use atorvastatin or rosuvastatin instead']
    },

    'metformin_alcohol': {
        'current': ['Metformin 500mg BD'],
        'new': ['Alcohol consumption'],
        'expected_severity': 'MEDIUM',
        'expected_category': 'interaction',
        'expected_action': 'INFO',
        'expected_message': 'Alcohol increases lactic acidosis risk with metformin',
        'description': 'Both metformin and alcohol can cause lactic acidosis',
        'clinical_notes': 'Advise moderate alcohol consumption or abstinence.',
        'alternatives': []
    },

    'levothyroxine_iron': {
        'current': ['Levothyroxine 75mcg OD'],
        'new': ['Iron Sulphate 150mg OD'],
        'expected_severity': 'MEDIUM',
        'expected_category': 'interaction',
        'expected_action': 'INFO',
        'expected_message': 'Iron reduces levothyroxine absorption',
        'description': 'Iron chelates levothyroxine in the gut',
        'clinical_notes': 'Separate doses by 4 hours. Take levothyroxine on empty stomach.',
        'alternatives': []
    },

    # Pregnancy contraindications
    'ace_inhibitor_pregnancy': {
        'current': ['Pregnancy - 12 weeks'],
        'new': ['Ramipril 5mg OD'],
        'expected_severity': 'CRITICAL',
        'expected_category': 'contraindication',
        'expected_action': 'BLOCK',
        'expected_message': 'CONTRAINDICATED in pregnancy: ACE inhibitors cause fetal toxicity',
        'description': 'Teratogenic - causes renal dysgenesis, oligohydramnios',
        'clinical_notes': 'Absolutely contraindicated in pregnancy. Stop immediately.',
        'alternatives': ['Methyldopa', 'Labetalol', 'Nifedipine for BP in pregnancy']
    },

    'warfarin_pregnancy': {
        'current': ['Pregnancy - 8 weeks'],
        'new': ['Warfarin 5mg OD'],
        'expected_severity': 'CRITICAL',
        'expected_category': 'contraindication',
        'expected_action': 'BLOCK',
        'expected_message': 'CONTRAINDICATED in pregnancy: Warfarin is teratogenic',
        'description': 'Warfarin embryopathy, bleeding risk',
        'clinical_notes': 'Contraindicated especially in first trimester. Switch to LMWH.',
        'alternatives': ['Low molecular weight heparin (LMWH)']
    },

    'methotrexate_pregnancy': {
        'current': ['Pregnancy - 6 weeks'],
        'new': ['Methotrexate 15mg weekly'],
        'expected_severity': 'CRITICAL',
        'expected_category': 'contraindication',
        'expected_action': 'BLOCK',
        'expected_message': 'CONTRAINDICATED in pregnancy: Methotrexate is abortifacient',
        'description': 'Potent teratogen and abortifacient',
        'clinical_notes': 'Absolutely contraindicated. Can cause abortion.',
        'alternatives': []
    },

    # Renal impairment adjustments
    'metformin_ckd': {
        'current': ['CKD Stage 4 (eGFR 25)'],
        'new': ['Metformin 500mg BD'],
        'expected_severity': 'HIGH',
        'expected_category': 'contraindication',
        'expected_action': 'WARN',
        'expected_message': 'Metformin contraindicated in severe renal impairment (eGFR <30)',
        'description': 'Risk of lactic acidosis in renal impairment',
        'clinical_notes': 'Contraindicated if eGFR <30. Reduce dose if eGFR 30-45.',
        'alternatives': ['Insulin', 'DPP-4 inhibitors', 'GLP-1 agonists']
    },

    'nsaid_ckd': {
        'current': ['CKD Stage 3 (eGFR 35)'],
        'new': ['Ibuprofen 400mg TDS'],
        'expected_severity': 'HIGH',
        'expected_category': 'contraindication',
        'expected_action': 'WARN',
        'expected_message': 'NSAIDs can worsen renal function in CKD',
        'description': 'NSAIDs reduce renal perfusion and can cause acute kidney injury',
        'clinical_notes': 'Avoid NSAIDs in CKD. Use paracetamol instead.',
        'alternatives': ['Paracetamol 500mg TDS']
    },

    # Liver impairment
    'statin_liver_disease': {
        'current': ['Chronic liver disease (cirrhosis)'],
        'new': ['Atorvastatin 40mg OD'],
        'expected_severity': 'HIGH',
        'expected_category': 'contraindication',
        'expected_action': 'WARN',
        'expected_message': 'Statins contraindicated in active liver disease',
        'description': 'Risk of hepatotoxicity',
        'clinical_notes': 'Contraindicated in active liver disease. Monitor LFTs closely.',
        'alternatives': []
    },

    # Pediatric contraindications
    'aspirin_child': {
        'current': ['Age: 8 years', 'Viral fever'],
        'new': ['Aspirin 300mg TDS'],
        'expected_severity': 'CRITICAL',
        'expected_category': 'contraindication',
        'expected_action': 'BLOCK',
        'expected_message': 'Aspirin contraindicated in children with viral illness - Reye syndrome risk',
        'description': 'Risk of Reye syndrome (encephalopathy + liver failure)',
        'clinical_notes': 'Never use aspirin in children with viral illness.',
        'alternatives': ['Paracetamol 250mg TDS']
    },

    'tetracycline_child': {
        'current': ['Age: 6 years'],
        'new': ['Doxycycline 100mg BD'],
        'expected_severity': 'HIGH',
        'expected_category': 'contraindication',
        'expected_action': 'WARN',
        'expected_message': 'Tetracyclines cause tooth discoloration in children <8 years',
        'description': 'Permanent tooth discoloration and enamel hypoplasia',
        'clinical_notes': 'Avoid tetracyclines in children <8 years.',
        'alternatives': ['Azithromycin', 'Amoxicillin']
    },
}


# ============== HELPER FUNCTIONS ==============

def get_interaction_by_severity(severity: str) -> Dict:
    """Get all interactions of a specific severity level."""
    return {
        name: scenario
        for name, scenario in INTERACTION_SCENARIOS.items()
        if scenario['expected_severity'] == severity
    }


def get_all_interactions() -> Dict:
    """Get all interaction scenarios."""
    return INTERACTION_SCENARIOS


def get_interactions_by_category(category: str) -> Dict:
    """Get interactions by category (interaction, contraindication, etc.)."""
    return {
        name: scenario
        for name, scenario in INTERACTION_SCENARIOS.items()
        if scenario['expected_category'] == category
    }


def create_safety_alert_from_scenario(scenario_name: str) -> SafetyAlert:
    """Create a SafetyAlert object from an interaction scenario."""
    scenario = INTERACTION_SCENARIOS.get(scenario_name)
    if not scenario:
        return None

    return SafetyAlert(
        severity=scenario['expected_severity'],
        category=scenario['expected_category'],
        message=scenario['expected_message'],
        action=scenario['expected_action'],
        details=scenario.get('description', '')
    )


def get_critical_interactions() -> Dict:
    """Get all critical/life-threatening interactions."""
    return get_interaction_by_severity('CRITICAL')


def get_pregnancy_contraindications() -> Dict:
    """Get all pregnancy-related contraindications."""
    return {
        name: scenario
        for name, scenario in INTERACTION_SCENARIOS.items()
        if 'pregnancy' in name.lower()
    }


def get_renal_contraindications() -> Dict:
    """Get all renal impairment-related contraindications."""
    return {
        name: scenario
        for name, scenario in INTERACTION_SCENARIOS.items()
        if 'ckd' in name.lower() or 'renal' in scenario.get('description', '').lower()
    }


def get_pediatric_contraindications() -> Dict:
    """Get all pediatric contraindications."""
    return {
        name: scenario
        for name, scenario in INTERACTION_SCENARIOS.items()
        if 'child' in name.lower() or 'pediatric' in scenario.get('description', '').lower()
    }


__all__ = [
    "INTERACTION_SCENARIOS",
    "get_interaction_by_severity",
    "get_all_interactions",
    "get_interactions_by_category",
    "create_safety_alert_from_scenario",
    "get_critical_interactions",
    "get_pregnancy_contraindications",
    "get_renal_contraindications",
    "get_pediatric_contraindications",
]
