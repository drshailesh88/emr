"""Generate realistic patient data for load testing.

This generator creates Indian patient data with realistic names, ages,
and demographics for load testing scenarios.
"""

import random
from datetime import datetime, timedelta
from typing import List, Tuple

# Common Indian first names
MALE_FIRST_NAMES = [
    'Rajesh', 'Amit', 'Suresh', 'Ramesh', 'Vijay', 'Ajay', 'Anil', 'Sanjay',
    'Manoj', 'Deepak', 'Rahul', 'Ravi', 'Sandeep', 'Ashok', 'Vinod', 'Prakash',
    'Mahesh', 'Naveen', 'Rakesh', 'Mukesh', 'Arun', 'Vishal', 'Rohan', 'Karan',
    'Arjun', 'Krishna', 'Mohan', 'Govind', 'Nitin', 'Ankit', 'Gaurav', 'Rohit',
    'Ram', 'Shyam', 'Hari', 'Gopal', 'Dinesh', 'Pankaj', 'Sachin', 'Vikas',
    'Abhishek', 'Manish', 'Pradeep', 'Sunil', 'Lalit', 'Devendra', 'Bharat'
]

FEMALE_FIRST_NAMES = [
    'Priya', 'Sunita', 'Savita', 'Asha', 'Anita', 'Rekha', 'Meena', 'Geeta',
    'Kavita', 'Seema', 'Neha', 'Pooja', 'Ritu', 'Sonal', 'Anjali', 'Kiran',
    'Manjula', 'Lakshmi', 'Parvati', 'Saraswati', 'Radha', 'Sita', 'Gita',
    'Kamala', 'Padma', 'Vaishali', 'Divya', 'Sneha', 'Nikita', 'Preeti',
    'Swati', 'Shilpa', 'Renu', 'Usha', 'Vidya', 'Nisha', 'Smita', 'Alka',
    'Vandana', 'Archana', 'Sapna', 'Deepa', 'Meera', 'Jyoti', 'Komal'
]

# Common Indian surnames
SURNAMES = [
    'Kumar', 'Singh', 'Sharma', 'Verma', 'Gupta', 'Patel', 'Shah', 'Jain',
    'Agarwal', 'Reddy', 'Rao', 'Nair', 'Iyer', 'Menon', 'Pillai', 'Das',
    'Desai', 'Joshi', 'Mehta', 'Pandey', 'Mishra', 'Trivedi', 'Chaturvedi',
    'Srivastava', 'Shukla', 'Tiwari', 'Dubey', 'Saxena', 'Chopra', 'Malhotra',
    'Kapoor', 'Khanna', 'Bhatia', 'Sethi', 'Arora', 'Bansal', 'Mittal',
    'Agrawal', 'Goyal', 'Jindal', 'Singhal', 'Goel', 'Tandon', 'Sinha',
    'Choudhury', 'Mukherjee', 'Chatterjee', 'Banerjee', 'Bhattacharya'
]

# Indian cities for addresses
CITIES = [
    'Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata',
    'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur',
    'Indore', 'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara', 'Ghaziabad',
    'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut', 'Rajkot'
]

# Area/locality suffixes
LOCALITIES = [
    'Nagar', 'Colony', 'Extension', 'Vihar', 'Puram', 'Enclave',
    'Block', 'Sector', 'Lane', 'Road', 'Market', 'Park'
]


def generate_phone() -> str:
    """Generate a realistic Indian phone number."""
    # Indian mobile numbers: +91 followed by 10 digits starting with 6-9
    first_digit = random.choice(['6', '7', '8', '9'])
    rest_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return f'+91{first_digit}{rest_digits}'


def generate_address(city: str = None) -> str:
    """Generate a realistic Indian address."""
    if city is None:
        city = random.choice(CITIES)

    house_no = random.randint(1, 999)
    locality_name = random.choice(['Rajendra', 'Gandhi', 'Nehru', 'Subhash',
                                  'Ashok', 'Sarojini', 'Karol', 'Green'])
    locality_suffix = random.choice(LOCALITIES)
    pin = random.randint(110001, 855117)

    return f"{house_no}, {locality_name} {locality_suffix}, {city} - {pin}"


def generate_patient(
    patient_id: int = None,
    gender: str = None,
    age_range: Tuple[int, int] = (1, 90)
) -> dict:
    """Generate a single realistic patient.

    Args:
        patient_id: Optional patient ID to use
        gender: Optional gender ('M', 'F', or None for random)
        age_range: Tuple of (min_age, max_age)

    Returns:
        Dict with patient data
    """
    if gender is None:
        gender = random.choice(['M', 'F'])

    if gender == 'M':
        first_name = random.choice(MALE_FIRST_NAMES)
    else:
        first_name = random.choice(FEMALE_FIRST_NAMES)

    surname = random.choice(SURNAMES)
    name = f"{first_name} {surname}"

    age = random.randint(age_range[0], age_range[1])
    phone = generate_phone()
    address = generate_address()

    patient = {
        'name': name,
        'age': age,
        'gender': gender,
        'phone': phone,
        'address': address,
    }

    if patient_id is not None:
        patient['id'] = patient_id

    return patient


def generate_patients(
    count: int,
    start_id: int = 1,
    age_distribution: dict = None,
    gender_ratio: float = 0.5
) -> List[dict]:
    """Generate multiple realistic patients.

    Args:
        count: Number of patients to generate
        start_id: Starting patient ID
        age_distribution: Dict mapping age ranges to probabilities
            e.g., {(0, 18): 0.2, (19, 45): 0.4, (46, 65): 0.3, (66, 90): 0.1}
        gender_ratio: Ratio of male patients (0.5 = 50% male, 50% female)

    Returns:
        List of patient dicts
    """
    if age_distribution is None:
        # Default distribution: more adults, fewer children/elderly
        age_distribution = {
            (0, 12): 0.1,
            (13, 18): 0.05,
            (19, 35): 0.25,
            (36, 50): 0.30,
            (51, 65): 0.20,
            (66, 90): 0.10
        }

    # Calculate cumulative probabilities
    age_ranges = list(age_distribution.keys())
    probabilities = list(age_distribution.values())
    cumulative = []
    total = 0
    for p in probabilities:
        total += p
        cumulative.append(total)

    patients = []
    for i in range(count):
        # Determine gender
        gender = 'M' if random.random() < gender_ratio else 'F'

        # Determine age range based on distribution
        rand = random.random()
        age_range = age_ranges[0]
        for idx, cum_prob in enumerate(cumulative):
            if rand <= cum_prob:
                age_range = age_ranges[idx]
                break

        patient = generate_patient(
            patient_id=start_id + i,
            gender=gender,
            age_range=age_range
        )
        patients.append(patient)

    return patients


def generate_patients_with_conditions(count: int) -> List[dict]:
    """Generate patients with common medical conditions.

    This creates patients with realistic condition distributions:
    - Diabetes: 10%
    - Hypertension: 15%
    - Both: 5%
    - Respiratory issues: 8%
    - Cardiac issues: 7%
    - Other/Healthy: 55%

    Returns:
        List of patient dicts with 'condition' field
    """
    patients = generate_patients(count)

    condition_distribution = [
        ('Diabetes Mellitus Type 2', 0.10),
        ('Hypertension', 0.15),
        ('Diabetes + Hypertension', 0.05),
        ('Asthma/COPD', 0.08),
        ('Coronary Artery Disease', 0.07),
        ('Healthy/Other', 0.55)
    ]

    conditions = []
    cumulative = []
    total = 0
    for condition, prob in condition_distribution:
        total += prob
        cumulative.append((condition, total))

    for patient in patients:
        rand = random.random()
        patient['primary_condition'] = 'Healthy'
        for condition, cum_prob in cumulative:
            if rand <= cum_prob:
                patient['primary_condition'] = condition
                break

    return patients


def generate_heavy_patients(count: int) -> List[dict]:
    """Generate patients with heavy medical history.

    These patients have:
    - Older age (50-80)
    - Multiple chronic conditions
    - Higher visit frequency expected

    Returns:
        List of patient dicts
    """
    patients = []
    for i in range(count):
        gender = random.choice(['M', 'F'])
        age = random.randint(50, 80)

        patient = generate_patient(
            patient_id=i + 1,
            gender=gender,
            age_range=(age, age)
        )

        # Add chronic conditions
        conditions = random.sample([
            'Diabetes Mellitus Type 2',
            'Hypertension',
            'Dyslipidemia',
            'Coronary Artery Disease',
            'Chronic Kidney Disease',
            'COPD',
            'Osteoarthritis',
            'Hypothyroidism'
        ], k=random.randint(2, 4))

        patient['chronic_conditions'] = conditions
        patients.append(patient)

    return patients


if __name__ == '__main__':
    # Test the generator
    print("Testing patient generator...")

    # Generate 10 sample patients
    patients = generate_patients(10)
    print(f"\nGenerated {len(patients)} patients:")
    for p in patients[:3]:
        print(f"  {p['name']} ({p['gender']}, {p['age']}y) - {p['phone']}")

    # Generate patients with conditions
    print("\nPatients with conditions:")
    condition_patients = generate_patients_with_conditions(5)
    for p in condition_patients:
        print(f"  {p['name']} - {p['primary_condition']}")

    # Generate heavy patients
    print("\nHeavy patients:")
    heavy = generate_heavy_patients(3)
    for p in heavy:
        print(f"  {p['name']} ({p['age']}y) - {', '.join(p['chronic_conditions'])}")
