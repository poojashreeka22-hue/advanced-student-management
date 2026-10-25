"""
Automated API Integration Tests: Error Handling, Validation, and HTTP Status Codes (50 cases).
"""

import pytest


# ============================================================================
# 1. Non-existent Resource 404 Tests (25 cases)
# ============================================================================
not_found_endpoints = [
    (f"/students/{80000 + i}", 404) for i in range(1, 11)
] + [
    (f"/api/v1/courses/{90000 + i}", 404) for i in range(1, 9)
] + [
    (f"/api/v1/departments/{70000 + i}", 404) for i in range(1, 9)
]

@pytest.mark.parametrize("endpoint,expected_status", not_found_endpoints, ids=[f"api_404_{i}" for i in range(26)])
def test_api_not_found_endpoints(client, endpoint, expected_status):
    response = client.get(endpoint)
    assert response.status_code == expected_status


# ============================================================================
# 2. Invalid Payload 422 / 400 Validation Error Tests (26 cases)
# ============================================================================
invalid_payloads = [
    # Missing required full_name
    ({"register_number": f"REG_VAL_{i}", "email": f"val_{i}@univ.edu", "phone_number": "9876543210", "department": "CS", "academic_year": "1st Year"}, 422)
    for i in range(1, 7)
] + [
    # Invalid email format
    ({"full_name": f"Student {i}", "register_number": f"REG_EM_{i}", "email": "not-an-email", "phone_number": "9876543210", "department": "CS", "academic_year": "1st Year"}, 422)
    for i in range(1, 7)
] + [
    # Invalid short phone number
    ({"full_name": f"Student {i}", "register_number": f"REG_PH_{i}", "email": f"ph_{i}@univ.edu", "phone_number": "123", "department": "CS", "academic_year": "1st Year"}, 422)
    for i in range(1, 7)
] + [
    # Empty string name
    ({"full_name": "   ", "register_number": f"REG_SP_{i}", "email": f"sp_{i}@univ.edu", "phone_number": "9876543210", "department": "CS", "academic_year": "1st Year"}, 422)
    for i in range(1, 7)
]

@pytest.mark.parametrize("payload,expected_status", invalid_payloads, ids=[f"api_val_err_{i}" for i in range(24)])
def test_api_payload_validation_errors(client, payload, expected_status):
    response = client.post("/students", json=payload)
    assert response.status_code == expected_status
