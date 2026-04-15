"""
Field Normalization Module
==========================
Transforms raw HR data fields into a canonical ADP-compatible format.

Rules applied:
  1. Full Name → Legal First / Middle / Last Name split
  2. Gender → MALE / FEMALE
  3. Hire Date → MM/DD/YYYY
  4. Birth Date → MM/DD/YYYY
  5. FLSA Status → S (Salary) or H (Hourly)
  6. State Filing / Marital Status → SINGLE / MARRIED
  7. SSN → XXX-XX-XXXX (with dashes)
"""

import re
import pandas as pd
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(v) -> str:
    """Return stripped string or empty string for None/NaN/Series."""
    # If a duplicate column caused a Series to be returned, extract first non-null value
    if isinstance(v, pd.Series):
        v = v.dropna().iloc[0] if not v.dropna().empty else ""
    try:
        if pd.isna(v) or str(v).strip() in ("nan", "NaT", "None", ""):
            return ""
    except (TypeError, ValueError):
        return ""
    return str(v).strip()


# ---------------------------------------------------------------------------
# Rule 1 – Full Name Split
# ---------------------------------------------------------------------------

def normalize_full_name(full_name: str) -> tuple[str, str, str]:
    """
    Split a full name into (first, middle, last).
    Handles common formats:
      "Last, First Middle"
      "First Middle Last"
      "First Last"
    """
    name = _safe(full_name)
    if not name:
        return "", "", ""

    # Handle "Last, First Middle" (comma-separated)
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip().title()
        rest = parts[1].strip().split()
        first = rest[0].title() if len(rest) > 0 else ""
        middle = rest[1].title() if len(rest) > 1 else ""
        return first, middle, last

    # Handle "First [Middle] Last"
    parts = name.split()
    if len(parts) == 1:
        return parts[0].title(), "", ""
    if len(parts) == 2:
        return parts[0].title(), "", parts[1].title()
    # 3+ parts: first, middle(s joined), last
    first = parts[0].title()
    last = parts[-1].title()
    middle = " ".join(p.title() for p in parts[1:-1])
    return first, middle, last


# ---------------------------------------------------------------------------
# Rule 2 – Gender Standardization
# ---------------------------------------------------------------------------

GENDER_MAP = {
    "m": "MALE", "male": "MALE",
    "f": "FEMALE", "female": "FEMALE",
}

def normalize_gender(v: str) -> str:
    return GENDER_MAP.get(_safe(v).lower(), _safe(v).upper())


# ---------------------------------------------------------------------------
# Rule 3 & 4 – Date Normalization → MM/DD/YYYY
# ---------------------------------------------------------------------------

DATE_FORMATS = [
    "%m/%d/%Y", "%d/%m/%Y",
    "%m-%d-%Y", "%d-%m-%Y",
    "%Y-%m-%d", "%Y/%m/%d",
    "%m/%d/%y", "%d/%m/%y",
]

def normalize_date(v) -> str:
    # Handle pandas/python datetime objects directly
    if hasattr(v, "strftime"):
        return v.strftime("%m/%d/%Y")
    
    raw = _safe(v)
    if not raw:
        return ""
        
    # Handle ISO-like strings with timestamps (e.g. 1979-03-18 00:00:00)
    if " " in raw:
        raw_date = raw.split(" ")[0]
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
            try:
                dt = datetime.strptime(raw_date, fmt)
                return dt.strftime("%m/%d/%Y")
            except ValueError:
                continue

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%m/%d/%Y")
        except ValueError:
            continue
    return raw


# ---------------------------------------------------------------------------
# Rule 5 – FLSA / Pay Rate Code
# ---------------------------------------------------------------------------

def normalize_flsa(v: str) -> str:
    raw = _safe(v).lower()
    if not raw:
        return ""
    if raw == "e" or any(k in raw for k in ["salary", "exempt", "s"]):
        if "non" not in raw and "hourly" not in raw:
            return "Salary Exempt"
    if raw == "n" or any(k in raw for k in ["hourly", "non exempt", "h"]):
        return "Hourly Non Exempt"
    return _safe(v)

def normalize_job_title(v: str) -> str:
    raw = _safe(v)
    if not raw:
        return ""
    if " - " in raw:
        # e.g., "PLNTMGR2 - PLANT MANAGER 2" -> "PLANT MANAGER 2"
        return raw.split(" - ", 1)[-1].strip()
    return raw


# ---------------------------------------------------------------------------
# Rule 6 – Marital / Filing Status
# ---------------------------------------------------------------------------

MARITAL_MAP = {
    "s": "SINGLE", 
    "single": "SINGLE",
    "single or married filing separately": "SINGLE",
    "m": "MARRIED", 
    "married": "MARRIED",
    "married filing jointly or married filing jointly": "MARRIED",
    "h": "HEAD OF HOUSEHOLD",
    "head of household": "HEAD OF HOUSEHOLD",
}

def normalize_marital(v: str) -> str:
    """Standardize marital and filing status records."""
    raw = _safe(v).lower()
    if not raw:
        return ""
    
    # Check for direct matches in the map
    if raw in MARITAL_MAP:
        return MARITAL_MAP[raw]
    
    # Fuzzy match for common phrases
    if "single" in raw:
        return "SINGLE"
    if "jointly" in raw or ("married" in raw and "joint" in raw):
        return "MARRIED"
    if "widow" in raw or "surviving" in raw:
        return "MARRIED"
    if "head" in raw:
        return "HEAD OF HOUSEHOLD"
        
    return _safe(v).upper()


# ---------------------------------------------------------------------------
# Rule 7 – SSN Formatting → XXX-XX-XXXX
# ---------------------------------------------------------------------------

def normalize_ssn(v: str) -> str:
    raw = _safe(v)
    if not raw:
        return ""
    # Extract only digits
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    
    # If 7-8 digits, it's likely leading zeros were dropped by Excel
    if 1 <= len(digits) <= 9:
        digits = digits.zfill(9)
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    
    # Return as-is if it's completely non-standard (e.g. 10+ digits)
    return raw


# ---------------------------------------------------------------------------
# Rule 8 – Zip Code Normalization (xxxxx-xxxx)
# ---------------------------------------------------------------------------

def normalize_zip(v: str) -> str:
    """Normalize zip codes to xxxxx-xxxx (5-4 format)."""
    raw = _safe(v)
    if not raw:
        return ""
    
    # Extract only digits
    digits = re.sub(r"\D", "", raw)
    
    # If 9 digits, format as xxxxx-xxxx
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    
    # If 5 digits, return as-is
    if len(digits) == 5:
        return digits
        
    # Otherwise return as-is (e.g. non-US or partial)
    return raw.strip()


# ---------------------------------------------------------------------------
# Rule 19 – State Normalization (Full Name → 2-Letter Code)
# ---------------------------------------------------------------------------

STATE_MAP = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "american samoa": "AS", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "district of columbia": "DC",
    "florida": "FL", "georgia": "GA", "guam": "GU", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
    "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "northern mariana islands": "MP", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "puerto rico": "PR",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "trust territories": "TT",
    "utah": "UT", "vermont": "VT", "virginia": "VA",
    "virgin islands": "VI", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY"
}

def normalize_state(v: str) -> str:
    """Normalize state names or codes to 2-letter uppercase codes."""
    raw = _safe(v).strip()
    if not raw:
        return ""
    
    # If already a 2-letter code that exists in values of STATE_MAP
    if len(raw) == 2 and raw.upper() in STATE_MAP.values():
        return raw.upper()
    
    # If it's a full name match
    if raw.lower() in STATE_MAP:
        return STATE_MAP[raw.lower()]
    
    # If it's something like "OH-30" or "Ohio - 30", extract the prefix
    # Try splitting by space or dash
    prefix = re.split(r'[\s\-]', raw)[0].strip()
    if prefix.lower() in STATE_MAP:
        return STATE_MAP[prefix.lower()]
    if len(prefix) == 2 and prefix.upper() in STATE_MAP.values():
        return prefix.upper()
        
    return raw.upper()


# ---------------------------------------------------------------------------
# Rule 18 – Phone Number Normalization ((xxx) xxx-xxxx)
# ---------------------------------------------------------------------------

def normalize_phone(v: str) -> str:
    """Normalize phone numbers to (xxx) xxx-xxxx format."""
    raw = _safe(v)
    if not raw:
        return ""
    
    # Extract only digits
    digits = re.sub(r"\D", "", raw)
    
    # Handle US country code if present (11 digits starting with 1)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
        
    # Standard US 10-digit format
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # If it doesn't match 10 digits, just return the digits for consistency
    # or return as-is if no digits were found
    return digits if digits else raw.strip()


def normalize_account(v: str) -> str:
    """Normalize account numbers by removing .0 decimals and leading/trailing whitespace."""
    raw = _safe(v)
    if not raw:
        return ""
    # Remove .0 if it's there (common Excel issue)
    if raw.endswith(".0"):
        raw = raw[:-2]
    # Simple strip for now
    return raw.strip()


# ---------------------------------------------------------------------------
# Rule 12 – Ethnicity / Race Normalization
# ---------------------------------------------------------------------------

ETHNICITY_MAP = {
    "hispanic or latino": "Hispanic or Latino",
    "not hispanic or latino": "Not Hispanic or Latino",
    "hispanic": "Hispanic or Latino",
    "latino": "Hispanic or Latino",
    "h": "Hispanic or Latino",
    "n": "Not Hispanic or Latino",
}

RACE_MAP = {
    "white": "White (Not Hispanic or Latino)",
    "black": "Black or African American (Not Hispanic or Latino)",
    "asian": "Asian (Not Hispanic or Latino)",
    "american indian": "American Indian or Alaska Native (Not Hispanic or Latino)",
    "native hawaiian": "Native Hawaiian or Other Pacific Islander (Not Hispanic or Latino)",
    "two or more": "Two or More Races (Not Hispanic or Latino)",
    "caucasian": "White (Not Hispanic or Latino)",
    "african american": "Black or African American (Not Hispanic or Latino)",
    "pacific islander": "Native Hawaiian or Other Pacific Islander (Not Hispanic or Latino)",
    "indian": "American Indian or Alaska Native (Not Hispanic or Latino)",
}

def normalize_ethnicity(v: str) -> str:
    val = _safe(v).lower()
    return ETHNICITY_MAP.get(val, _safe(v))

def normalize_race(v: str) -> str:
    val = _safe(v).lower()
    for key, mapped in RACE_MAP.items():
        # Use regex to match only full words
        if re.search(r'\b' + re.escape(key) + r'\b', val):
            return mapped
    return _safe(v)


# ---------------------------------------------------------------------------
# Rule 13 – EEOC Job Classification Normalization
# ---------------------------------------------------------------------------

EEOC_JOB_MAP = {
    "1.1": "1.1 - Executive/Senior Level Officials and Managers",
    "1.2": "1.2 - First/Mid Level Officials and Managers",
    "2": "2 - Professionals",
    "3": "3 - Technicians",
    "4": "4 - Sales Workers",
    "5": "5 - Administrative Support Workers",
    "6": "6 - Craft Workers",
    "7": "7 - Operatives",
    "8": "8 - Laborers and Helpers",
    "9": "9 - Service Workers",
}

def normalize_eeoc(v: str) -> str:
    val = _safe(v).strip()
    # If it's just the number, map it
    if val in EEOC_JOB_MAP:
        return EEOC_JOB_MAP[val]
    # If it starts with the number followed by a dot or space, map it
    for code, full in EEOC_JOB_MAP.items():
        if val.startswith(code):
            return full
    return val


# ---------------------------------------------------------------------------
# Rule 14 – US Work Authorization Normalization
# ---------------------------------------------------------------------------

def normalize_auth(v: str) -> str:
    val = _safe(v).lower()
    if any(x in val for x in ["authorized", "yes", "citizen", "permanent", "resident", "green card"]):
        return "Authorized"
    if any(x in val for x in ["not authorized", "no", "unauthorized"]):
        return "Not Authorized"
    return _safe(v)


# ---------------------------------------------------------------------------
# Column name sets to match canonical fields
# ---------------------------------------------------------------------------

# Full-name single-column aliases (Paycor format)
FULL_NAME_FIELDS   = {"employee name", "full name", "name", "employee full name", "ee name", "associate name", "worker", "person", "employee", "payroll name"}
# Split-name column aliases (ADP Variant 1)
FIRST_NAME_FIELDS  = {"first name", "emp first name", "employee first name"}
MIDDLE_NAME_FIELDS = {"middle name", "emp middle name", "employee middle name", "middle initial"}
LAST_NAME_FIELDS   = {"last name", "emp last name", "employee last name", "surname"}
# Legal split-name aliases (ADP Variant 2)
LEGAL_FIRST_FIELDS = {"legal first name", "legal first", "first name", "first_name", "first", "fname", "given name", "emp first name", "employee first name", "first_name", "legal_firstname"}
LEGAL_MID_FIELDS   = {"legal middle name", "legal middle", "legal middle initial", "mname", "middle_name", "legal_middle_name"}
LEGAL_LAST_FIELDS  = {"legal last name", "legal last", "last name", "last_name", "last", "lname", "surname", "emp last name", "employee last name", "last_name", "legal_lastname"}

SSN_FIELDS         = {"ssn", "tax id", "social security number", "tax ssn", "ss_number", "tax ssn#", "ss#", "tax(ssn)", "tax id (ssn)", "ee ssn", "employee ssn", "emp ssn", "ss_number"}
GENDER_FIELDS      = {"gender", "sex", "gender (self-id)", "gender for insurance coverage"}
BIRTH_DATE_FIELDS  = {"birth date", "date of birth", "dob", "birthdate", "birth_date", "birth_date_(mm/dd/yyyy)"}
MARITAL_FIELDS     = {"state filing status", "marital status", "w4 marital status", "federal marital status", "filing status"}
EMAIL_FIELDS       = {"personal email", "work email", "email address", "personal_email", "work_email"}
PHONE_FIELDS       = {"cell/mobile phone", "home phone", "work phone", "phone number", "primary_phone/secondary_phone?"}
ZIP_FIELDS         = {"legal / preferred address: zip / postal code", "zip", "zip code", "postal code", "zip/postal", "zip_code", "postal_code", "primary_zip/postal_code"}
ADDRESS_FIELDS     = {
    "legal / preferred address: address line 1",
    "legal / preferred address: address line 2",
    "legal / preferred address: city",
    "legal / preferred address: state / territory code",
    "legal / preferred address: zip / postal code",
    "primary_address_line_1",
    "primary_address_line_2",
    "primary_city/municipality",
    "primary_state/province"
}
# ---------------------------------------------------------------------------
# Rule 21 – Employment Status Normalization
# ---------------------------------------------------------------------------

def normalize_status(v: str) -> str:
    """Standardize employee status. Maps 'Inactive' and 'Terminated' as same."""
    raw = _safe(v).lower()
    if not raw:
        return ""
    
    # User request: Inactive and Terminated are the same
    if any(k in raw for k in ["term", "inactive", "quit", "sep"]):
        return "Terminated"
    
    if any(k in raw for k in ["act", "active", "online", "employed"]):
        return "Active"
        
    return _safe(v).title()


STATUS_FIELDS      = {"employment/position status", "status", "employment status", "employee_status"}
TOBACCO_FIELDS     = {"tobacco user", "tobacco"}
HIRE_DATE_FIELDS   = {"hire date", "hire_date", "date of hire", "hire_dt", "hire_date_(mm/dd/yyyy)"}
TERM_DATE_FIELDS   = {"termination date", "term date", "term_date", "date of termination", "term_dt", "termination_dt", "status_effective_date"}
REHIRE_DATE_FIELDS = {"rehire date", "rehire_date", "date of rehire", "rehire_dt", "position_start_date"}

# Job Information Fields
JOB_TITLE_FIELDS   = {"job title", "position", "title", "job title description", "job_title", "position_desc"}
DEPT_CODE_FIELDS   = {"home department code", "dept code", "department code", "department code + name", "department"}
DEPT_DESC_FIELDS   = {"home department description", "dept description", "department description", "department", "department name", "department code + name", "department_desc"}
COST_CODE_FIELDS   = {"home cost number code", "cost center code", "cost number code"}
COST_DESC_FIELDS   = {"home cost number description", "cost center description", "cost number description"}
BU_CODE_FIELDS     = {"business unit code", "bu code"}
BU_DESC_FIELDS     = {"business unit description", "bu description", "business unit"}
LOC_CODE_FIELDS    = {"location code", "loc code", "work_location"}
LOC_DESC_FIELDS    = {"location description", "loc description", "location", "work_location"}
WORKER_CAT_FIELDS  = {"worker category", "employment category", "employee category", "worker category description", "status type"}
REPORTS_TO_FIELDS  = {"reports to", "manager", "reports to (manager)", "reports to legal name"}
FLSA_FIELDS        = {"flsa (exempt/non exempt)", "flsa status", "flsa", "flsa description"}
STANDARD_HOURS_FIELDS = {"standard hours", "std hours", "scheduled_pay_period_hours"}
ANNUAL_SALARY_FIELDS  = {"annual salary", "rate #1 annualized", "annual_salary"}
PAY_RATE_FIELDS    = {"regular pay rate amount", "pay rate", "rate", "hourly rate or salary amt", "hourly_rate", "regular_salary_amount"}
RATE_FIELDS        = {"rate 2", "rate 3", "rate 4", "rate 5", "rate 6", "rate 7", "rate 8", "rate 9"}
NAICS_FIELDS       = {"naics workers' comp code", "naics code", "workers comp code", "workers comp: (text)", "workers comp class code (text)", "workers_comp_code"}
BENEFIT_ELIG_FIELDS = {"benefit eligibility class", "benefit class", "benefit eligibiltiy class"}


# ---------------------------------------------------------------------------
# Name column unification helper
# ---------------------------------------------------------------------------

def _normalize_name_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect any of the three name format variants and produce canonical
    'Legal First Name', 'Legal Middle Name', 'Legal Last Name' columns.

    Variant A – Paycor: single 'Full Name' column → split into Legal F/M/L
    Variant B – ADP 1:  'First Name', 'Middle Name', 'Last Name' → rename
    Variant C – ADP 2:  'Legal First Name', 'Legal Middle Name', 'Legal Last Name' → keep as-is
    """
    col_lower = {c.lower(): c for c in df.columns}

    def _get_best_col(aliases):
        """Find the alias that exists and has the most non-empty values."""
        # Ensure aliases themselves are checked in lowercase
        lower_aliases = {str(a).lower() for a in aliases}
        found = [col_lower[a] for a in lower_aliases if a in col_lower]
        if not found: return None
        if len(found) == 1: return found[0]
        # Evaluate occupancy
        best_col = found[0]
        max_count = -1
        for c in found:
            count = df[c].apply(lambda x: _safe(x) != "").sum()
            if count > max_count:
                max_count = count
                best_col = c
        return best_col

    # ── Variant C: already has Legal First/Last ─────────────────────────────
    # FIX: Even if columns exist, if Last is empty and First contains a comma, split it.
    leg_f_col = _get_best_col(LEGAL_FIRST_FIELDS)
    leg_l_col = _get_best_col(LEGAL_LAST_FIELDS)
    
    if leg_f_col and leg_l_col:
        # Check if we need to split a full name from the First Name column
        first_vals = df[leg_f_col].apply(_safe)
        last_vals  = df[leg_l_col].apply(_safe)
        needs_split = (first_vals.str.contains(",").any() and (last_vals == "").all())
        
        if needs_split:
            parsed = [normalize_full_name(v) for v in first_vals]
            idx = df.index
            df[leg_f_col] = pd.Series([r[0] for r in parsed], index=idx)
            if "Legal Middle Name" not in df.columns:
                df["Legal Middle Name"] = pd.Series([r[1] for r in parsed], index=idx)
            else:
                df["Legal Middle Name"] = pd.Series([r[1] or v for r, v in zip(parsed, df["Legal Middle Name"])], index=idx)
            df[leg_l_col] = pd.Series([r[2] for r in parsed], index=idx)
            return df

        # Otherwise just ensure canonical names
        rename_map = {leg_f_col: "Legal First Name", leg_l_col: "Legal Last Name"}
        leg_m_col = _get_best_col(LEGAL_MID_FIELDS)
        if leg_m_col: rename_map[leg_m_col] = "Legal Middle Name"
        
        df = df.rename(columns=rename_map)
        return df

    # ── Variant B: separate First / Last columns ─────────────────────────────
    has_first = _get_best_col(FIRST_NAME_FIELDS)
    has_last  = _get_best_col(LAST_NAME_FIELDS)
    if has_first and has_last:
        rename_map = {has_first: "Legal First Name", has_last: "Legal Last Name"}
        has_mid = _get_best_col(MIDDLE_NAME_FIELDS)
        if has_mid: rename_map[has_mid] = "Legal Middle Name"
        df = df.rename(columns=rename_map)
        return df

    # ── Variant A: single full-name column → split ───────────────────────────
    best_full_col = _get_best_col(FULL_NAME_FIELDS)
    if best_full_col:
        parsed = [normalize_full_name(_safe(v)) for v in df[best_full_col]]
        idx = df.index
        df["Legal First Name"]  = pd.Series([r[0] for r in parsed], index=idx)
        df["Legal Middle Name"] = pd.Series([r[1] for r in parsed], index=idx)
        df["Legal Last Name"]   = pd.Series([r[2] for r in parsed], index=idx)

    return df


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Required Field Groups
# ---------------------------------------------------------------------------

PERSONAL_FIELDS = [
    "SSN",
    "Employment/Position Status",
    "Hire Date",
    "Termination Date",
    "Legal First Name",
    "Legal Middle Name",
    "Legal Last Name",
    "Birth Date",
    "Gender",
    "Personal Email",
    "Work Email",
    "Cell/Mobile Phone",
    "Home Phone",
    "Work Phone",
    "Legal / Preferred Address: Address Line 1",
    "Legal / Preferred Address: Address Line 2",
    "Legal / Preferred Address: City",
    "Legal / Preferred Address: State / Territory Code",
    "Legal / Preferred Address: Zip / Postal Code",
    "Marital Status",
    "Tobacco User"
]

JOB_FIELDS = [
    "SSN",
    "Employee Full Name",
    "Hire Date",
    "Rehire Date",
    "Termination Date",
    "Regular Pay Rate Amount",
    "Rate 2",
    "Rate 3",
    "Rate 4",
    "Rate 5",
    "Rate 6",
    "Rate 7",
    "Rate 8",
    "Rate 9",
    "FLSA (Exempt/Non Exempt)",
    "Annual Salary",
    "Standard Hours",
    "Job Title",
    "Home Department Code",
    "Home Department Description",
    "Home Cost Number Code",
    "Home Cost Number Description",
    "Business Unit Code",
    "Business Unit Description",
    "Location Code",
    "Location Description",
    "NAICS Workers' Comp Code",
    "Benefit Eligibility Class",
    "Worker Category (FT, PT, TEMP, etc.)",
    "Reports To (Manager)",
    "Employment/Position Status"
]

TAX_FIELDS = [
    "SSN",
    "Employee Full Name",
    "Hire Date",
    "Termination Date",
    "Employment/Position Status",
    "Do not Calculate F.U.T.A. Taxable?",
    "Do Not Calculate Federal Income Tax?",
    "Do Not Calculate Federal Taxable?",
    "Do not calculate Medicare?",
    "Do not calculate Social Security?",
    "Federal/W4 Marital Status Description",
    "Federal/W4 Exemptions",
    "Federal Additional Tax Amount",
    "Deductions",
    "Dependents",
    "Other Income",
    "Multiple Jobs",
    "Lived in Local Jurisdiction Code",
    "Worked in Local Jurisdiction Code",
    "Local 4 Tax Code",
    "Do not calculate State Tax?",
    "Do not calculate State Taxable?",
    "Lived in State Code",
    "Worked in State Code",
    "SUI/SDI Tax Code",
    "State Marital Status Code",
    "State Exemptions/Allowances",
    "State Additional Tax Amount",
    "State Additional Tax Amount Percentage",
]

COMPLIANCE_FIELDS = [
    "SSN",
    "Employee Full Name",
    "Hire Date",
    "Termination Date",
    "Employment/Position Status",
    "Ethnicity",
    "Race",
    "EEOC Job Classification",
    "US Work Authorization Status",
    "I-9 Eligibility Review Date",
]

DIRECT_DEPOSIT_FIELDS = [
    "EE SSN",
    "EE Name",
    "Status",
    "Hire Date",
    "Termination Date",
    "Routing Number",
    "Account Number"
]

DEDUCTION_FIELDS = [
    "SSN",
    "Full Name",
    "Code_ID",
    "Deduction Code",
    "Deduction Description",
    "Deduction Amount",
    "Deduction Rate",
]

# ── Tax field alias sets ───────────────────────────────────────────────────
# Boolean "Do not calculate" fields
FUTA_FIELDS           = {"do not calculate f.u.t.a. taxable?", "futa taxable", "exempt from futa", "do not calc futa", "do not calculate f.u.t.a. taxable", "block_futa?"}
FED_INC_TAX_FIELDS    = {"do not calculate federal income tax?", "exempt from federal income tax", "do not calc federal income tax", "do not calculate federal income tax", "block_fit?"}
FED_TAX_FIELDS        = {"do not calculate federal taxable?", "exempt from federal taxable", "do not calc fed taxable", "do not calculate federal taxable", "block_federal_tax?"}
MEDICARE_FIELDS       = {"do not calculate medicare?", "exempt from medicare", "do not calc medicare", "do not calculate medicare", "block_medicare?"}
SOC_SEC_FIELDS        = {"do not calculate social security?", "exempt from social security", "do not calc social security", "do not calculate social security", "block_ss?"}
STATE_TAX_FIELDS      = {"do not calculate state tax?", "exempt from state tax", "do not calc state tax", "do not calculate state tax", "block_state_tax?"}
STATE_TAXABLE_FIELDS  = {"do not calculate state taxable?", "exempt from state taxable", "do not calc state taxable", "do not calculate state taxable"}

# Federal / W4
FED_MARITAL_FIELDS    = {"federal/w4 marital status description", "federal marital status", "w4 marital status", "fed marital status", "federal filing status", "filing status", "fed_filing_status"}
FED_EXEMPT_FIELDS     = {"federal/w4 exemptions", "federal exemptions", "w4 exemptions", "fed exemptions", "federal exemptions (w4s saved after 2019 are based on filing status)", "number of exemptions (w4s saved after 2019 are based on filing status)", "fed_exemptions"}
FED_ADD_TAX_FIELDS    = {"federal additional tax amount", "additional federal tax", "extra federal tax", "fed additional tax", "federal additional amount", "additional amount withheld", "fed_addl_$"}
DEDUCTIONS_FIELDS     = {"deductions", "additional deductions", "fed_deductions_$"}
DEPENDENTS_FIELDS     = {"dependents", "number of dependents", "dependents amount", "dependents amount and other dependents amount", "fed_dependents_$"}
OTHER_INCOME_FIELDS   = {"other income", "additional income", "fed_other_income_$"}
MULTIPLE_JOBS_FIELDS  = {"multiple jobs", "multiple jobs indicator", "two jobs", "has two incomes", "fed_multiple_jobs?", "multiple jobs indicator"}

# Local tax
LIVED_LOCAL_FIELDS    = {"lived in local jurisdiction code", "local lived jurisdiction", "local residence code"}
WORKED_LOCAL_FIELDS   = {"worked in local jurisdiction code", "local worked jurisdiction", "local work code"}
LOCAL4_TAX_FIELDS     = {"local 4 tax code", "local tax code 4", "local4 tax code"}

# State tax
LIVED_STATE_FIELDS    = {"lived in state code", "state lived code", "state of residence", "resident state", "lived in/worked in indicator", "lives-in_state"}
WORKED_STATE_FIELDS   = {"worked in state code", "state worked code", "state of employment", "work state", "lived in/worked in indicator", "works-in_state"}
SUI_SDI_FIELDS        = {"sui/sdi tax code", "sui sdi tax code", "sdi tax code", "sui tax code", "sui_state"}
STATE_MARITAL_FIELDS  = {"state marital status code", "state marital status", "state filing status code", "state filing status", "filing status", "state_filing_status"}
STATE_EXEMPT_FIELDS   = {"state exemptions/allowances", "state exemptions", "state allowances", "number of exemptions (w4s saved after 2019 are based on filing status)", "#state_exemptions/allowances"}
STATE_ADD_TAX_FIELDS  = {"state additional tax amount", "additional state tax", "extra state tax", "state additional amount", "additional amount withheld", "state_addl_$"}
STATE_ADD_PCT_FIELDS  = {"state additional tax amount percentage", "state additional tax %", "state add tax pct", "state add tax percent", "state additional percent", "additional percent withheld", "state_addl_%"}

# Compliance Information aliases
ETHNICITY_FIELDS      = {"ethnicity", "ethnic group", "hispanic/latino", "hispanic or latino"}
RACE_FIELDS           = {"race", "racial group", "race/ethnicity", "race category"}
EEOC_FIELDS           = {"eeoc job classification", "eeo-1 job category", "eeo classification", "eeo category", "eeoc job category"}
WORK_AUTH_FIELDS      = {"us work authorization status", "work authorization", "i-9 status", "work eligible", "us work authorization"}
I9_DATE_FIELDS        = {"i-9 eligibility review date", "i9 review date", "i-9 date", "i-9 eligibility review"}

# Direct Deposit aliases
DD_ACCOUNT_FIELDS     = {"direct deposit account number", "account number", "account #", "bank account number", "bank account #", "account", "net_acct_code", "dist_1_acct_code", "dist_2_acct_code", "dist_3_acct_code", "dist_4_acct_code", "dist_1_account", "dist_2_account", "bank deposit account number", "accountIdentifier"}
DD_ROUTING_FIELDS     = {"direct deposit routing number", "routing number", "routing #", "bank routing number", "bank routing #", "routing", "aba number", "aba #", "net_rout_code", "dist_1_rout_code", "dist_2_rout_code", "dist_3_rout_code", "dist_4_rout_code", "dist_1_routing", "dist_2_routing", "transit aba number"}
DD_AMOUNT_FIELDS      = {"direct deposit amount", "amount", "deposit amount", "net pay amount"}
DD_AMT_TYPE_FIELDS    = {"direct deposit amount type", "amount type", "deposit type"}
DD_FREQ_FIELDS        = {"direct deposit frequency", "frequency", "deposit frequency"}

# Deduction Information aliases
DED_CODE_FIELDS       = {"deduction code", "ded code", "deduction cd", "ded cd", "deduction type code", "deduction id", "code", "deduction code [all deductions]", "deduction code [all]", "deduction code"}
DED_DESC_FIELDS       = {"deduction description", "ded description", "deduction name", "ded name", "deduction type description", "deduction type", "deduction desc", "deduction plan", "plan name", "deduction long name"}
DED_AMT_FIELDS        = {"deduction amount", "ded amount", "amount", "deduction $"}
DED_PCT_FIELDS        = {"deduction %", "deduction percent", "deduction rate", "ded rate", "rate", "percent"}
CODE_ID_FIELDS        = {"code_id", "code id", "common code", "id", "deduction id"}

# Backwards compatibility
REQUIRED_FIELDS = PERSONAL_FIELDS


# ---------------------------------------------------------------------------
# Rule 9 – Boolean / Yes-No Normalization
# ---------------------------------------------------------------------------

BOOLEAN_TRUE  = {"yes", "true", "1", "y", "x", "checked", "on"}
BOOLEAN_FALSE = {"no", "false", "0", "n", "", "unchecked", "off"}

def normalize_boolean(v: str) -> str:
    """Normalize boolean-like values to Yes / No."""
    raw = _safe(v).lower()
    if raw in BOOLEAN_TRUE:
        return "Yes"
    if raw in BOOLEAN_FALSE or raw == "":
        return "No"
    return _safe(v)   # preserve unexpected values as-is


# ---------------------------------------------------------------------------
# Rule 10 – Numeric Cleaning (no $ or commas, valid numbers only)
# ---------------------------------------------------------------------------

def normalize_numeric(v: str) -> str:
    """Strip currency symbols and commas; return clean numeric string or empty. Standardizes 0 to empty."""
    raw = _safe(v)
    if not raw:
        return ""
    cleaned = raw.replace("$", "").replace(",", "").strip()
    try:
        f = float(cleaned)
        # Standardize: 0, 0.0, 0.00 all become empty string to match ADP blanks
        if f == 0:
            return ""
        # Unify float strings (e.g. "10.00" -> "10", "10.50" -> "10.5")
        if f == int(f):
            return str(int(f))
        return str(f)
    except ValueError:
        return raw   # preserve non-numeric text as-is (e.g., state codes)


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def normalize_dataframe(df: pd.DataFrame, target_fields: list = None) -> pd.DataFrame:
    """
    Apply all normalization rules to a DataFrame.
    Columns are matched case-insensitively against known field sets.
    Filters the result to only include target_fields (defaults to PERSONAL_FIELDS).
    """
    if df.empty:
        return df

    if target_fields is None:
        target_fields = PERSONAL_FIELDS

    df = df.copy()

    # 1. Clean column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Robust Deduplication: Keep only the first occurrence of each column name (case-insensitive)
    cols_seen = {}
    indices_to_keep = []
    for i, col in enumerate(df.columns):
        lower_col = col.lower()
        if lower_col not in cols_seen:
            cols_seen[lower_col] = i
            indices_to_keep.append(i)
    
    # Force unique columns by positional selection
    df = df.iloc[:, indices_to_keep]
    
    # Update our mapping of lowered names to actual names
    col_lower = {c.lower(): c for c in df.columns}

    # ── Rule 7: SSN ──────────────────────────────────────────────────────────
    for key in SSN_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_ssn(_safe(v)))

    # ── Rule 8: Zip Code ─────────────────────────────────────────────────────
    for key in ZIP_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_zip(_safe(v)))

    # ── Rule 1: Name Unification (all 3 variants → Legal First/Middle/Last) ──
    df = _normalize_name_columns(df)
    
    # CRITICAL: Post-Rule-1, refresh column caches because columns were renamed!
    col_lower = {str(c).lower(): str(c) for c in df.columns}

    # ── Rule 2: Gender ───────────────────────────────────────────────────────
    # Identify all columns that match any gender alias
    gender_candidates = []
    for c in df.columns:
        if str(c).lower() in GENDER_FIELDS:
            gender_candidates.append(c)
    
    if gender_candidates:
        # If any of the candidates are NOT called exactly "Gender", we will consolidate.
        # Actually, even if there's only one, we want to normalize it.
        # If there are multiple, we pick the first non-empty normalized value.
        def get_best_gender(row):
            for col in gender_candidates:
                val = normalize_gender(_safe(row[col]))
                if val:
                    return val
            return ""
        
        # Build the consolidated series
        best_gender = df.apply(get_best_gender, axis=1)
        
        # Drop all old gender candidates to avoid duplicates or confusion
        df = df.drop(columns=gender_candidates)
        
        # Add the new canonical "Gender" column
        df["Gender"] = best_gender

    # ── Rule 4: Birth Date ───────────────────────────────────────────────────
    for key in BIRTH_DATE_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_date(_safe(v)))

    # ── Rule 5: Hire, Rehire & Termination Date ──────────────────────────────
    for field_set in [HIRE_DATE_FIELDS, TERM_DATE_FIELDS, REHIRE_DATE_FIELDS]:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                df[col] = df[col].apply(lambda v: normalize_date(_safe(v)))

    # ── Rule 6: Marital Status ────────────────────────────────────────────────
    for key in MARITAL_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_marital(_safe(v)))

    # ── Rule 21: Employment Status ──────────────────────────────────────────
    for key in STATUS_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(normalize_status)

    # ── Additional Fields ─────────────────────────────────────────────────────
    job_field_sets = [
        DEPT_CODE_FIELDS, DEPT_DESC_FIELDS, COST_CODE_FIELDS,
        COST_DESC_FIELDS, BU_CODE_FIELDS, BU_DESC_FIELDS, LOC_CODE_FIELDS,
        LOC_DESC_FIELDS, WORKER_CAT_FIELDS, REPORTS_TO_FIELDS,
        STANDARD_HOURS_FIELDS, ANNUAL_SALARY_FIELDS, PAY_RATE_FIELDS,
        NAICS_FIELDS, BENEFIT_ELIG_FIELDS
    ]
    
    # Pre-process fields that have specific formatting needs
    for key in JOB_TITLE_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(normalize_job_title)

    for key in FLSA_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(normalize_flsa)
            
    for field_set in job_field_sets:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                df[col] = df[col].apply(_safe)

    # Rates 2-9
    for key in RATE_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_numeric(_safe(v)))

    # Deduction Fields
    for key in DED_CODE_FIELDS | DED_DESC_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(_safe)

    for key in DED_AMT_FIELDS | DED_PCT_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_numeric(_safe(v)))

    # ── Rule 15: Account Number ──────────────────────────────────────────────
    for key in DD_ACCOUNT_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_account(_safe(v)))

    # ── Rule 9: Tax Boolean Fields (Do not calculate …) ─────────────────────
    tax_boolean_sets = [
        FUTA_FIELDS, FED_INC_TAX_FIELDS, FED_TAX_FIELDS,
        MEDICARE_FIELDS, SOC_SEC_FIELDS, STATE_TAX_FIELDS, STATE_TAXABLE_FIELDS,
        MULTIPLE_JOBS_FIELDS,
    ]
    for field_set in tax_boolean_sets:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                df[col] = df[col].apply(lambda v: normalize_boolean(_safe(v)))

    # ── Rule 10: Tax Numeric Fields ──────────────────────────────────────────
    tax_numeric_sets = [
        FED_ADD_TAX_FIELDS, DEDUCTIONS_FIELDS, DEPENDENTS_FIELDS,
        OTHER_INCOME_FIELDS, STATE_ADD_TAX_FIELDS, STATE_ADD_PCT_FIELDS,
        FED_EXEMPT_FIELDS, STATE_EXEMPT_FIELDS,
    ]
    for field_set in tax_numeric_sets:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                df[col] = df[col].apply(lambda v: normalize_numeric(_safe(v)))

    # ── Rule 11: Tax Code / Text Fields (special handling for States) ───────
    tax_text_sets = [
        LIVED_LOCAL_FIELDS, WORKED_LOCAL_FIELDS,
        LOCAL4_TAX_FIELDS, LIVED_STATE_FIELDS, WORKED_STATE_FIELDS,
        SUI_SDI_FIELDS,
    ]
    state_field_sets = [LIVED_STATE_FIELDS, WORKED_STATE_FIELDS, SUI_SDI_FIELDS]
    
    for field_set in tax_text_sets:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                if field_set in state_field_sets:
                    df[col] = df[col].apply(normalize_state)
                else:
                    df[col] = df[col].apply(_safe)

    # ── Special Case: Tax Marital / Filing Status ───────────────────────────
    for field_set in [FED_MARITAL_FIELDS, STATE_MARITAL_FIELDS]:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                df[col] = df[col].apply(lambda v: normalize_marital(_safe(v)))

    # ── Rule 12: Ethnicity / Race ──────────────────────────────────────────
    ethnicity_cols = [ETHNICITY_FIELDS, RACE_FIELDS]
    for field_set in ethnicity_cols:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                if field_set == ETHNICITY_FIELDS:
                    df[col] = df[col].apply(lambda v: normalize_ethnicity(_safe(v)))
                else:
                    df[col] = df[col].apply(lambda v: normalize_race(_safe(v)))

    # ── Rule 13: EEOC / Work Auth ──────────────────────────────────────────
    compliance_text_cols = [EEOC_FIELDS, WORK_AUTH_FIELDS]
    for field_set in compliance_text_cols:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                if field_set == EEOC_FIELDS:
                    df[col] = df[col].apply(lambda v: normalize_eeoc(_safe(v)))
                else:
                    df[col] = df[col].apply(lambda v: normalize_auth(_safe(v)))

    # ── Rule 14: I-9 Date ───────────────────────────────────────────────────
    for key in I9_DATE_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_date(_safe(v)))

    # ── Rule 18: Phone Numbers ──────────────────────────────────────────────
    for key in PHONE_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(lambda v: normalize_phone(_safe(v)))

    # ── Rule 16 & 17: Deduction Formatting ───────────────────────────────────
    for key in DED_CODE_FIELDS:
        if key in col_lower:
            col = col_lower[key]
            df[col] = df[col].apply(_safe)

    for field_set in [DED_AMT_FIELDS, DED_PCT_FIELDS]:
        for key in field_set:
            if key in col_lower:
                col = col_lower[key]
                df[col] = df[col].apply(lambda v: normalize_numeric(_safe(v)))

    # 3. Final Step: Filter for target fields only
    # Match existing columns against target_fields case-insensitively
    # and rename them to the EXACT casing expected.
    final_cols = []
    found_cols_lower = {str(c).lower().strip(): str(c) for c in df.columns}
    rename_final = {}
    
    # Special handling for "Tax ID (SSN)" and "Employee Full Name"
    # Mapping for target fields to their aliases (using lists to prioritize exact/best matches)
    FIELD_TO_ALIASES = {
        "Tax ID (SSN)": ["ssn"] + list(SSN_FIELDS - {"ssn"}),
        "Employee Full Name": list(FULL_NAME_FIELDS),
        "SSN": ["ssn"] + list(SSN_FIELDS - {"ssn"}),
        "Hire Date": list(HIRE_DATE_FIELDS),
        "Termination Date": list(TERM_DATE_FIELDS),
        "Rehire Date": list(REHIRE_DATE_FIELDS),
        "Employment/Position Status": list(STATUS_FIELDS),
        "Worker Category (FT, PT, TEMP, etc.)": list(WORKER_CAT_FIELDS),
        # Tax Information aliases
        "Do not Calculate F.U.T.A. Taxable?": list(FUTA_FIELDS),
        "Do Not Calculate Federal Income Tax?": list(FED_INC_TAX_FIELDS),
        "Do Not Calculate Federal Taxable?": list(FED_TAX_FIELDS),
        "Do not calculate Medicare?": list(MEDICARE_FIELDS),
        "Do not calculate Social Security?": list(SOC_SEC_FIELDS),
        "Federal/W4 Marital Status Description": list(FED_MARITAL_FIELDS),
        "Federal/W4 Exemptions": list(FED_EXEMPT_FIELDS),
        "Federal Additional Tax Amount": list(FED_ADD_TAX_FIELDS),
        "Deductions": list(DEDUCTIONS_FIELDS),
        "Dependents": list(DEPENDENTS_FIELDS),
        "Other Income": list(OTHER_INCOME_FIELDS),
        "Multiple Jobs": list(MULTIPLE_JOBS_FIELDS),
        "Lived in Local Jurisdiction Code": list(LIVED_LOCAL_FIELDS),
        "Worked in Local Jurisdiction Code": list(WORKED_LOCAL_FIELDS),
        "Local 4 Tax Code": list(LOCAL4_TAX_FIELDS),
        "Do not calculate State Tax?": list(STATE_TAX_FIELDS),
        "Do not calculate State Taxable?": list(STATE_TAXABLE_FIELDS),
        "Lived in State Code": list(LIVED_STATE_FIELDS),
        "Worked in State Code": list(WORKED_STATE_FIELDS),
        "SUI/SDI Tax Code": list(SUI_SDI_FIELDS),
        "State Marital Status Code": list(STATE_MARITAL_FIELDS),
        "State Exemptions/Allowances": list(STATE_EXEMPT_FIELDS),
        "State Additional Tax Amount": list(STATE_ADD_TAX_FIELDS),
        "State Additional Tax Amount Percentage": list(STATE_ADD_PCT_FIELDS),
        # Compliance Information aliases
        "Ethnicity": list(ETHNICITY_FIELDS),
        "Race": list(RACE_FIELDS),
        "EEOC Job Classification": list(EEOC_FIELDS),
        "US Work Authorization Status": list(WORK_AUTH_FIELDS),
        "I-9 Eligibility Review Date": list(I9_DATE_FIELDS),
        # Direct Deposit aliases
        "Account Number": list(DD_ACCOUNT_FIELDS),
        "Routing Number": list(DD_ROUTING_FIELDS),
        "Status": list(STATUS_FIELDS),
        "EE SSN": ["ssn"] + list(SSN_FIELDS - {"ssn"}),
        "EE Name": list(FULL_NAME_FIELDS),
        # Deduction Information aliases
        "SSN": list(SSN_FIELDS),
        "Full Name": list(FULL_NAME_FIELDS),
        "Deduction Code": list(DED_CODE_FIELDS),
        "Deduction Amount": list(DED_AMT_FIELDS),
        "Deduction Rate": list(DED_PCT_FIELDS),
    }

    # If Employee Full Name or EE Name is requested, ensure it's populated (reconstructing from parts if needed)
    if "Employee Full Name" in target_fields or "EE Name" in target_fields:
        efn_target = "EE Name" if "EE Name" in target_fields else "Employee Full Name"
        efn_lower = efn_target.lower()
        column_missing = efn_lower not in [c.lower() for c in df.columns]
        
        has_split = "Legal First Name" in df.columns and "Legal Last Name" in df.columns
        
        if column_missing and has_split:
            def build_full_name(row):
                fn = _safe(row.get('Legal First Name', ''))
                mn = _safe(row.get('Legal Middle Name', ''))
                ln = _safe(row.get('Legal Last Name', ''))
                if fn and ln:
                    return f"{ln}, {fn} {mn}".strip()
                return fn or ln or mn
            df[efn_target] = df.apply(build_full_name, axis=1)
        elif not column_missing and has_split:
            actual_col = next(c for c in df.columns if c.lower() == efn_lower)
            # Create a combined series that fills holes in actual_col from split names
            def heal_row(row):
                orig = _safe(row[actual_col])
                if orig: return orig
                fn = _safe(row.get('Legal First Name', ''))
                mn = _safe(row.get('Legal Middle Name', ''))
                ln = _safe(row.get('Legal Last Name', ''))
                if fn and ln:
                    return f"{ln}, {fn} {mn}".strip()
                return fn or ln or mn
            
            df[actual_col] = df.apply(heal_row, axis=1)
            if actual_col != efn_target:
                df = df.rename(columns={actual_col: efn_target})

    # 3. Final Step: Building the final DataFrame based on target_fields
    final_df = pd.DataFrame(index=df.index)
    found_cols_lower = {str(c).lower().strip(): str(c) for c in df.columns}
    
    for req in target_fields:
        req_lower = req.lower()
        found = False
        
        # 1. Direct match (case-insensitive)
        if req_lower in found_cols_lower:
            orig_col = found_cols_lower[req_lower]
            final_df[req] = df[orig_col]
            found = True
            
        # 3. Final mapping
        if not found:
            aliases = FIELD_TO_ALIASES.get(req)
            if aliases:
                for alias in aliases:
                    if alias in found_cols_lower:
                        orig_col = found_cols_lower[alias]
                        final_df[req] = df[orig_col]
                        found = True
                        break
        
        # 4. If still not found, add as empty column to prevent downstream KeyErrors
        if not found:
            final_df[req] = ""
                    
    return final_df
