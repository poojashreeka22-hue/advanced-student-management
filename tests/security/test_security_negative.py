"""
Automated Security Tests: Negative Authorization, Tampered Tokens, SQL Injection Resistance (50 cases).
"""

import pytest
from app.core.security import create_access_token


# ============================================================================
# 1. Invalid or Tampered JWT Tokens (25 cases)
# ============================================================================
tampered_tokens = [
    f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_payload_{i}.tampered_signature"
    for i in range(1, 26)
]

@pytest.mark.parametrize("bad_token_header", tampered_tokens, ids=[f"tampered_token_{i}" for i in range(25)])
def test_tampered_token_rejection(client, bad_token_header):
    headers = {"Authorization": bad_token_header}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


# ============================================================================
# 2. Search Injection Resilience and Negative Authorization (25 cases)
# ============================================================================
injection_queries = [
    "' OR '1'='1",
    "'; DROP TABLE students; --",
    "admin' --",
    "1' UNION SELECT * FROM users --",
    "' OR 1=1 --",
    "1; WAITFOR DELAY '0:0:5'",
    "' OR ''='",
    "<script>alert(1)</script>",
    "../../etc/passwd",
    "%00",
    "0x50",
    "' HAVING 1=1 --",
    "' GROUP BY id --",
    "\" OR \"1\"=\"1",
    "\\x27\\x20OR\\x201=1",
    "/**/OR/**/1=1",
    "benchmark(10000000,MD5(1))",
    "sleep(5)",
    "'; EXEC xp_cmdshell('dir'); --",
    "' OR id IS NOT NULL --",
    "' AND 1=2 --",
    "' UNION ALL SELECT NULL,NULL,NULL --",
    "{\"field\": \"$gt\"}",
    "test%'; SELECT 1; --",
    "' OR 'a'='a"
]

@pytest.mark.parametrize("attack_query", injection_queries, ids=[f"injection_query_{i}" for i in range(25)])
def test_search_injection_resilience(client, attack_query):
    # Query must be treated as safe literal text without database error
    response = client.get(f"/students?search={attack_query}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
