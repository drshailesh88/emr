"""India-specific drug database with search and lookup"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
import json
import os
from pathlib import Path

@dataclass
class DrugFormulation:
    brand_name: str
    salt: str
    strength: str
    form: str  # tablet, capsule, syrup, injection
    manufacturer: str
    price_approx: float  # in INR

@dataclass
class Drug:
    generic_name: str
    drug_class: str
    category: str  # antibiotic, antidiabetic, etc.
    formulations: List[DrugFormulation]
    common_doses: List[str]
    max_daily_dose: str
    pregnancy_category: str  # A, B, C, D, X
    lactation_safe: bool
    requires_monitoring: List[str]  # what labs to monitor

class DrugDatabase:
    """Searchable drug database with India-specific data"""

    def __init__(self, data_path: str = "data/drugs"):
        self.data_path = data_path
        self.drugs: Dict[str, Drug] = {}
        self.salt_index: Dict[str, List[str]] = {}  # salt -> generic names
        self.brand_index: Dict[str, str] = {}  # brand -> generic name
        self._load_database()

    def _load_database(self):
        """Load drug data from JSON files"""
        try:
            db_file = Path(self.data_path) / "drug_database.json"
            if not db_file.exists():
                print(f"Warning: Drug database not found at {db_file}")
                self._create_sample_database()
                return

            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for drug_data in data.get('drugs', []):
                formulations = [
                    DrugFormulation(**form) for form in drug_data.get('formulations', [])
                ]
                drug = Drug(
                    generic_name=drug_data['generic_name'],
                    drug_class=drug_data['drug_class'],
                    category=drug_data['category'],
                    formulations=formulations,
                    common_doses=drug_data.get('common_doses', []),
                    max_daily_dose=drug_data.get('max_daily_dose', ''),
                    pregnancy_category=drug_data.get('pregnancy_category', 'C'),
                    lactation_safe=drug_data.get('lactation_safe', True),
                    requires_monitoring=drug_data.get('requires_monitoring', [])
                )

                self.drugs[drug.generic_name.lower()] = drug

                # Build indices
                for formulation in formulations:
                    salt_lower = formulation.salt.lower()
                    if salt_lower not in self.salt_index:
                        self.salt_index[salt_lower] = []
                    if drug.generic_name not in self.salt_index[salt_lower]:
                        self.salt_index[salt_lower].append(drug.generic_name)

                    brand_lower = formulation.brand_name.lower()
                    self.brand_index[brand_lower] = drug.generic_name

            print(f"Loaded {len(self.drugs)} drugs from database")

        except Exception as e:
            print(f"Error loading drug database: {e}")
            self._create_sample_database()

    def _create_sample_database(self):
        """Create sample database with common Indian drugs"""
        sample_drugs = [
            {
                "generic_name": "metformin",
                "drug_class": "biguanide",
                "category": "antidiabetic",
                "formulations": [
                    {
                        "brand_name": "Glycomet",
                        "salt": "Metformin HCl",
                        "strength": "500mg",
                        "form": "tablet",
                        "manufacturer": "USV",
                        "price_approx": 2.5
                    },
                    {
                        "brand_name": "Glucophage",
                        "salt": "Metformin HCl",
                        "strength": "850mg",
                        "form": "tablet",
                        "manufacturer": "Merck",
                        "price_approx": 4.0
                    }
                ],
                "common_doses": ["500mg BD", "850mg BD", "1000mg BD"],
                "max_daily_dose": "2550mg",
                "pregnancy_category": "B",
                "lactation_safe": True,
                "requires_monitoring": ["renal function", "vitamin B12"]
            },
            {
                "generic_name": "amlodipine",
                "drug_class": "calcium channel blocker",
                "category": "antihypertensive",
                "formulations": [
                    {
                        "brand_name": "Amlong",
                        "salt": "Amlodipine Besylate",
                        "strength": "5mg",
                        "form": "tablet",
                        "manufacturer": "Micro Labs",
                        "price_approx": 1.8
                    }
                ],
                "common_doses": ["2.5mg OD", "5mg OD", "10mg OD"],
                "max_daily_dose": "10mg",
                "pregnancy_category": "C",
                "lactation_safe": True,
                "requires_monitoring": ["blood pressure", "heart rate"]
            },
            {
                "generic_name": "atorvastatin",
                "drug_class": "statin",
                "category": "lipid-lowering",
                "formulations": [
                    {
                        "brand_name": "Atorva",
                        "salt": "Atorvastatin Calcium",
                        "strength": "10mg",
                        "form": "tablet",
                        "manufacturer": "Zydus",
                        "price_approx": 3.2
                    }
                ],
                "common_doses": ["10mg OD", "20mg OD", "40mg OD"],
                "max_daily_dose": "80mg",
                "pregnancy_category": "X",
                "lactation_safe": False,
                "requires_monitoring": ["liver function", "CPK"]
            }
        ]

        # Load sample drugs into memory
        for drug_data in sample_drugs:
            formulations = [
                DrugFormulation(**form) for form in drug_data.get('formulations', [])
            ]
            drug = Drug(
                generic_name=drug_data['generic_name'],
                drug_class=drug_data['drug_class'],
                category=drug_data['category'],
                formulations=formulations,
                common_doses=drug_data.get('common_doses', []),
                max_daily_dose=drug_data.get('max_daily_dose', ''),
                pregnancy_category=drug_data.get('pregnancy_category', 'C'),
                lactation_safe=drug_data.get('lactation_safe', True),
                requires_monitoring=drug_data.get('requires_monitoring', [])
            )
            self.drugs[drug.generic_name.lower()] = drug

    def search(self, query: str, limit: int = 20) -> List[Drug]:
        """Search drugs by name, salt, or brand"""
        if not query:
            return []

        query_lower = query.lower()
        results = []
        seen = set()

        # Search by generic name
        for name, drug in self.drugs.items():
            if query_lower in name and drug.generic_name not in seen:
                results.append(drug)
                seen.add(drug.generic_name)

        # Search by brand name
        for brand, generic in self.brand_index.items():
            if query_lower in brand and generic not in seen:
                if generic.lower() in self.drugs:
                    results.append(self.drugs[generic.lower()])
                    seen.add(generic)

        # Search by salt
        for salt, generics in self.salt_index.items():
            if query_lower in salt:
                for generic in generics:
                    if generic not in seen and generic.lower() in self.drugs:
                        results.append(self.drugs[generic.lower()])
                        seen.add(generic)

        return results[:limit]

    def get_by_generic_name(self, name: str) -> Optional[Drug]:
        """Get drug by generic name"""
        return self.drugs.get(name.lower())

    def get_by_salt(self, salt: str) -> List[Drug]:
        """Get all drugs containing a salt"""
        generics = self.salt_index.get(salt.lower(), [])
        return [self.drugs[g.lower()] for g in generics if g.lower() in self.drugs]

    def get_formulations(self, generic_name: str) -> List[DrugFormulation]:
        """Get all formulations of a drug"""
        drug = self.get_by_generic_name(generic_name)
        return drug.formulations if drug else []

    def get_drug_class(self, generic_name: str) -> str:
        """Get drug class for a drug"""
        drug = self.get_by_generic_name(generic_name)
        return drug.drug_class if drug else ""

    def get_common_doses(self, generic_name: str) -> List[str]:
        """Get common dose options"""
        drug = self.get_by_generic_name(generic_name)
        return drug.common_doses if drug else []
