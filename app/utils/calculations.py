"""
Academic, attendance, fee, and scheduling calculation utilities.
"""

from typing import List, Dict, Any, Tuple


def calculate_letter_grade_and_point(percentage: float) -> Tuple[str, float]:
    """
    Standard academic grade conversion.
    Returns (letter_grade, grade_point).
    """
    if percentage >= 90.0:
        return ("A+", 4.0)
    elif percentage >= 80.0:
        return ("A", 3.7)
    elif percentage >= 75.0:
        return ("B+", 3.3)
    elif percentage >= 70.0:
        return ("B", 3.0)
    elif percentage >= 65.0:
        return ("C+", 2.7)
    elif percentage >= 60.0:
        return ("C", 2.3)
    elif percentage >= 50.0:
        return ("D", 2.0)
    else:
        return ("F", 0.0)


def calculate_weighted_marks(examinations_and_grades: List[Dict[str, float]]) -> float:
    """
    examinations_and_grades: list of dicts with 'marks_obtained', 'max_marks', 'weightage_percent'
    Returns overall weighted percentage (0.0 to 100.0).
    """
    if not examinations_and_grades:
        return 0.0

    total_weightage = sum(item.get("weightage_percent", 0.0) for item in examinations_and_grades)
    if total_weightage <= 0.0:
        return 0.0

    weighted_sum = 0.0
    for item in examinations_and_grades:
        obtained = max(0.0, item.get("marks_obtained", 0.0))
        max_m = max(1.0, item.get("max_marks", 100.0))
        weight = max(0.0, item.get("weightage_percent", 0.0))
        weighted_sum += (obtained / max_m) * weight

    # Scale relative to total recorded weightage
    return round((weighted_sum / total_weightage) * 100.0, 2)


def calculate_gpa(courses_data: List[Dict[str, Any]]) -> float:
    """
    courses_data: list of dicts with 'credits' (int) and 'grade_point' (float)
    Returns GPA rounded to 2 decimal places.
    """
    if not courses_data:
        return 0.0

    total_credits = 0
    total_quality_points = 0.0

    for c in courses_data:
        credits = int(c.get("credits", 0))
        gp = float(c.get("grade_point", 0.0))
        if credits > 0:
            total_credits += credits
            total_quality_points += credits * gp

    if total_credits == 0:
        return 0.0

    return round(total_quality_points / total_credits, 2)


def calculate_attendance_percentage(
    records: List[Dict[str, Any]],
    min_threshold: float = 75.0
) -> Dict[str, Any]:
    """
    Calculate attendance percentage.
    Cancelled sessions are completely excluded from total.
    'present' = full credit (1.0)
    'late' = partial credit (0.75)
    'excused' = excused from attendance (not penalizing or counting towards present)
    """
    valid_records = [r for r in records if not r.get("is_cancelled", False)]
    total = len(valid_records)

    if total == 0:
        return {
            "total_sessions": 0,
            "present_count": 0,
            "absent_count": 0,
            "late_count": 0,
            "excused_count": 0,
            "attendance_percentage": 100.0,
            "is_shortage": False,
        }

    present = sum(1 for r in valid_records if r.get("status") == "present")
    late = sum(1 for r in valid_records if r.get("status") == "late")
    excused = sum(1 for r in valid_records if r.get("status") == "excused")
    absent = sum(1 for r in valid_records if r.get("status") == "absent")

    # Evaluated sessions = total sessions - excused sessions
    evaluated_sessions = total - excused
    if evaluated_sessions <= 0:
        percentage = 100.0
    else:
        effective_attended = present + (0.75 * late)
        percentage = round((effective_attended / evaluated_sessions) * 100.0, 2)
        percentage = min(100.0, max(0.0, percentage))

    return {
        "total_sessions": total,
        "present_count": present,
        "absent_count": absent,
        "late_count": late,
        "excused_count": excused,
        "attendance_percentage": percentage,
        "is_shortage": percentage < min_threshold,
    }


def calculate_fee_balance(amount: float, waiver_amount: float, total_paid: float) -> Tuple[float, str]:
    """
    Calculates remaining balance and status.
    Returns (balance_due, status).
    """
    net_payable = max(0.0, amount - waiver_amount)
    balance = max(0.0, round(net_payable - total_paid, 2))

    if net_payable == 0.0 or balance == 0.0:
        status = "paid"
    elif total_paid > 0.0:
        status = "partial"
    else:
        status = "pending"

    return balance, status


def parse_time_minutes(t_str: str) -> int:
    """Parse 'HH:MM' string into minutes from midnight."""
    parts = t_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """Check if two time intervals [start1, end1) and [start2, end2) overlap."""
    s1, e1 = parse_time_minutes(start1), parse_time_minutes(end1)
    s2, e2 = parse_time_minutes(start2), parse_time_minutes(end2)
    return max(s1, s2) < min(e1, e2)
