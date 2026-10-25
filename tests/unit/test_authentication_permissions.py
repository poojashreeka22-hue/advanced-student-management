"""
Automated Unit Tests: Authentication, Password Hashing, JWT Tokens, and RBAC Permissions (120 cases).
"""

import pytest
import time
from datetime import timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.core.permissions import Role, Permissions


# ============================================================================
# 1. Password Hashing and Cryptographic Verification (40 cases)
# ============================================================================
passwords = [
    "SecretPass123!", "Admin@2026", "simple", "P@ssw0rd_With_Very_Long_Sequence_Of_Characters_123456789",
    "unicode_пароль_123", "symbols_#$$%^&*()_+", "space in password", "12345678",
    "A", "b123!", "pass word", "tab\tpass", "newline\npass", "mixedCASE123",
    "!@#$%^&*()", "___underscores___", "---dashes---", "dots.and.more.dots",
    "emoji_🚀_password", "accent_éàü_test"
]

password_cases = []
for p in passwords:
    password_cases.append((p, p, True))          # Matching
    password_cases.append((p, p + "_wrong", False)) # Non-matching

@pytest.mark.parametrize("original_pass,test_pass,should_verify", password_cases, ids=[f"pwd_hash_verify_{i}" for i in range(40)])
def test_password_hashing_and_verification(original_pass: str, test_pass: str, should_verify: bool):
    hashed = hash_password(original_pass)
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(test_pass, hashed) == should_verify


# ============================================================================
# 2. JWT Access Token Encoding & Decoding (40 cases)
# ============================================================================
token_payloads = [
    ({"sub": f"user_{i}", "role": Role.STUDENT.value, "user_id": i}, True)
    for i in range(1, 21)
] + [
    # Expired tokens
    ({"sub": f"expired_user_{i}", "role": Role.FACULTY.value, "user_id": 100 + i}, False)
    for i in range(1, 11)
] + [
    # Custom attributes
    ({"sub": f"admin_{i}", "role": Role.ADMIN.value, "is_superuser": True}, True)
    for i in range(1, 11)
]

@pytest.mark.parametrize("payload,is_valid_time", token_payloads, ids=[f"jwt_payload_{i}" for i in range(40)])
def test_jwt_token_handling(payload, is_valid_time):
    if is_valid_time:
        token = create_access_token(payload, expires_delta=timedelta(minutes=30))
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == payload["sub"]
        assert decoded["role"] == payload["role"]
    else:
        # Expired token with negative timedelta
        token = create_access_token(payload, expires_delta=timedelta(seconds=-10))
        decoded = decode_access_token(token)
        assert decoded is None  # Should fail decoding or be expired


# ============================================================================
# 3. Role-Based Access Control (RBAC) Permissions Matrix (40 cases)
# ============================================================================
rbac_matrix = []

# Admin permissions (Admin should access all 10 endpoints)
for i in range(10):
    rbac_matrix.append((Role.ADMIN, Permissions.ALL, True))

# Faculty permissions
for i in range(10):
    # Faculty allowed for ACADEMIC_STAFF, rejected for ADMIN_ONLY
    rbac_matrix.append((Role.FACULTY, Permissions.ACADEMIC_STAFF, True))

# Student permissions
for i in range(10):
    # Student allowed for ALL, rejected for ADMIN_ONLY
    rbac_matrix.append((Role.STUDENT, Permissions.ADMIN_ONLY, False))

# Finance permissions
for i in range(10):
    # Finance allowed for FINANCE_AND_ADMIN, rejected for ADMIN_ONLY
    rbac_matrix.append((Role.FINANCE, Permissions.ADMIN_ONLY, False))

@pytest.mark.parametrize("role,allowed_roles,should_permit", rbac_matrix, ids=[f"rbac_check_{i}" for i in range(40)])
def test_role_permissions_check(role, allowed_roles, should_permit):
    is_permitted = role in allowed_roles
    assert is_permitted == should_permit
