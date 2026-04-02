import pandas as pd
import re

# Standard Fields
PERSONAL_FIELDS = [
    "Gender", "Legal Full Name: Last Name", "Legal Full Name: First Name", 
    "Legal Full Name: Middle Name", "Preferred Name", "Birth Date",
    "Personal Email", "Work Email", "Mobile Phone", "Home Phone", "Work Phone",
    "Marital Status", "Legal / Preferred Address: Address Line 1", 
    "Legal / Preferred Address: City", "Legal / Preferred Address: State", 
    "Legal / Preferred Address: Zip / Postal Code"
]

JOB_FIELDS = [
    "Job Title", "Business Unit Description", "Home Department Description",
    "Location Description", "Worker Category (FT, PT, TEMP, etc.)",
    "Reports To (Manager)", "FLSA (Exempt/Non Exempt)", "Annual Salary",
    "Employment Status", "Hire Date", "Termination Date"
]

TAX_FIELDS = [
    "Federal Tax Status", "Federal Allowances", "Federal Additional Amount",
    "State Tax Code", "State Tax Status", "State Allowances", "State Additional Amount",
    "Lived In State", "Worked In State"
]

COMPLIANCE_FIELDS = [
    "Ethnicity", "Race", "EEOC Job Classification", "Gender",
    "US Work Authorization Status", "I-9 Eligibility Review Date"
]

FIELD_TO_ALIASES = {
    "Gender": ["Gender", "Sex"],
    "Legal Full Name: First Name": ["First Name", "Legal First Name"],
    "Legal Full Name: Last Name": ["Last Name", "Legal Last Name"],
    "Birth Date": ["Birth Date", "DOB"],
    "Hire Date": ["Hire Date", "Adjusted Hire Date"],
    "SSN": ["SSN", "Tax ID (SSN)", "Social Security Number"],
    # ... more aliases
}

def normalize_dataframe(df, fields):
    # Core normalization logic
    for col in df.columns:
        if col in fields:
            # handle types etc
            pass
    return df

def clean_ssn(val):
    if not val: return ""
    digits = re.sub(r'\D', '', str(val))
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return digits
