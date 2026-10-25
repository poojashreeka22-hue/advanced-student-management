"""
Validation utilities for student admissions and domain rules.
"""

import re
from typing import Optional, Dict, Any, List

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def validate_email(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_phone(phone: str) -> bool:
    if not phone:
        return False
    cleaned = re.sub(r"[\s\-\+\(\)]", "", phone.strip())
    return cleaned.isdigit() and len(cleaned) >= 7


def validate_phone_10_digits(phone: str) -> bool:
    """Validate that phone number contains exactly 10 numeric digits."""
    if not phone:
        return False
    cleaned = re.sub(r"[\s\-\+\(\)]", "", phone.strip())
    return cleaned.isdigit() and len(cleaned) == 10


def normalize_register_number(reg_num: str) -> str:
    """Normalize register number to uppercase trimmed string."""
    return reg_num.strip().upper()


def check_duplicate_candidate(
    new_candidate: Dict[str, Any],
    existing_students: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Check if a candidate matches any existing student based on:
    1. Exact normalized register number
    2. Exact email (case-insensitive)
    3. Exact (first_name, last_name, date_of_birth) tuple
    """
    new_reg = normalize_register_number(new_candidate.get("register_number", ""))
    new_email = (new_candidate.get("email") or "").strip().lower()
    new_fn = (new_candidate.get("first_name") or "").strip().lower()
    new_ln = (new_candidate.get("last_name") or "").strip().lower()
    new_dob = (new_candidate.get("date_of_birth") or "").strip()

    for s in existing_students:
        ex_reg = normalize_register_number(s.get("register_number", ""))
        if new_reg and ex_reg and new_reg == ex_reg:
            return f"Duplicate register number: {new_reg}"

        ex_email = (s.get("email") or "").strip().lower()
        if new_email and ex_email and new_email == ex_email:
            return f"Duplicate email address: {new_email}"

        ex_fn = (s.get("first_name") or "").strip().lower()
        ex_ln = (s.get("last_name") or "").strip().lower()
        ex_dob = (s.get("date_of_birth") or "").strip()
        if new_fn and new_ln and new_dob and ex_fn and ex_ln and ex_dob:
            if (new_fn, new_ln, new_dob) == (ex_fn, ex_ln, ex_dob):
                return f"Duplicate student identity: {new_fn} {new_ln} born on {new_dob}"

    return None
