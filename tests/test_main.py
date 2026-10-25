"""
Comprehensive automated test suite for Student Management System.
Tests CRUD operations, search functionality, uniqueness constraints,
validation rules, and analytics endpoints using an isolated SQLite database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models

# Isolated in-memory SQLite database using StaticPool
# Ensures tests run quickly and never modify the production/development database.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency in FastAPI
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh database tables before each test and drop them after."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def sample_students():
    """Seed sample students for search and retrieval tests."""
    students = [
        {
            "full_name": "Chandra Sekhar",
            "register_number": "REG001",
            "email": "chandra@college.edu",
            "phone_number": "9876543210",
            "department": "Computer Science",
            "academic_year": "3rd Year"
        },
        {
            "full_name": "Priya Sharma",
            "register_number": "REG002",
            "email": "priya@college.edu",
            "phone_number": "9876543211",
            "department": "Information Technology",
            "academic_year": "2nd Year"
        },
        {
            "full_name": "Rahul Verma",
            "register_number": "REG003",
            "email": "rahul@college.edu",
            "phone_number": "9876543212",
            "department": "Electronics & Communication",
            "academic_year": "4th Year"
        }
    ]
    created = []
    for s in students:
        res = client.post("/students", json=s)
        assert res.status_code == 201
        created.append(res.json())
    return created


# ============================================================================
# 1. Student Creation & Validation Tests
# ============================================================================

def test_create_student():
    """Test creating a valid student record."""
    payload = {
        "full_name": "Alice Johnson",
        "register_number": "REG101",
        "email": "alice@college.edu",
        "phone_number": "9876543219",
        "department": "Computer Science",
        "academic_year": "1st Year"
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["full_name"] == "Alice Johnson"
    assert data["register_number"] == "REG101"
    assert data["email"] == "alice@college.edu"
    assert data["department"] == "Computer Science"
    assert data["academic_year"] == "1st Year"


def test_create_student_duplicate_register_number():
    """Test rejecting duplicate register numbers with HTTP 400."""
    payload = {
        "full_name": "Bob Smith",
        "register_number": "REG202",
        "email": "bob@college.edu",
        "phone_number": "9876543220",
        "department": "Mechanical Engineering",
        "academic_year": "2nd Year"
    }
    # First creation should succeed
    res1 = client.post("/students", json=payload)
    assert res1.status_code == 201

    # Second creation with identical register number should fail
    duplicate_payload = {
        "full_name": "Robert Smith",
        "register_number": "REG202",
        "email": "robert@college.edu",
        "phone_number": "9876543221",
        "department": "Civil Engineering",
        "academic_year": "2nd Year"
    }
    res2 = client.post("/students", json=duplicate_payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_create_student_case_insensitive_duplicate_register_number():
    """Test duplicate register number rejection is case-insensitive."""
    payload1 = {
        "full_name": "Student A",
        "register_number": "reg303",
        "email": "studenta@college.edu",
        "phone_number": "9876543230",
        "department": "Computer Science",
        "academic_year": "1st Year"
    }
    res1 = client.post("/students", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "full_name": "Student B",
        "register_number": "REG303",  # Uppercase variation
        "email": "studentb@college.edu",
        "phone_number": "9876543231",
        "department": "Computer Science",
        "academic_year": "1st Year"
    }
    res2 = client.post("/students", json=payload2)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_create_student_invalid_input():
    """Test validation errors for missing or invalid inputs (HTTP 422)."""
    # Missing required full_name
    res = client.post("/students", json={
        "register_number": "REG404",
        "email": "test@college.edu",
        "phone_number": "9876543240",
        "department": "Computer Science",
        "academic_year": "1st Year"
    })
    assert res.status_code == 422

    # Invalid email format
    res_bad_email = client.post("/students", json={
        "full_name": "Invalid Email Student",
        "register_number": "REG405",
        "email": "not-an-email",
        "phone_number": "9876543241",
        "department": "Computer Science",
        "academic_year": "1st Year"
    })
    assert res_bad_email.status_code == 422


# ============================================================================
# 2. Student Retrieval & Read Tests
# ============================================================================

def test_get_all_students(sample_students):
    """Test retrieving all students."""
    response = client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_student_by_id(sample_students):
    """Test retrieving a single student by primary key ID."""
    student_id = sample_students[0]["id"]
    response = client.get(f"/students/{student_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_id
    assert data["register_number"] == "REG001"


def test_get_student_by_id_not_found():
    """Test retrieving a nonexistent student ID returns HTTP 404."""
    response = client.get("/students/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# 3. Student Update Tests
# ============================================================================

def test_update_student(sample_students):
    """Test successfully updating student details."""
    student_id = sample_students[0]["id"]
    update_data = {
        "full_name": "Chandra S. Gupta",
        "department": "Data Science & AI",
        "academic_year": "4th Year"
    }
    response = client.put(f"/students/{student_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Chandra S. Gupta"
    assert data["department"] == "Data Science & AI"
    assert data["academic_year"] == "4th Year"
    # Unchanged fields remain preserved
    assert data["register_number"] == "REG001"


def test_update_student_conflict_register_number(sample_students):
    """Test updating to an already taken register number returns HTTP 400."""
    student_id_1 = sample_students[0]["id"]
    student_reg_2 = sample_students[1]["register_number"]

    # Try setting student 1's register number to student 2's register number
    response = client.put(f"/students/{student_id_1}", json={"register_number": student_reg_2})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_update_student_not_found():
    """Test updating a nonexistent student ID returns HTTP 404."""
    response = client.put("/students/88888", json={"full_name": "No Body"})
    assert response.status_code == 404


# ============================================================================
# 4. Student Deletion Tests
# ============================================================================

def test_delete_student(sample_students):
    """Test successfully deleting a student."""
    student_id = sample_students[0]["id"]
    response = client.delete(f"/students/{student_id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify student is no longer in database
    get_res = client.get(f"/students/{student_id}")
    assert get_res.status_code == 404


def test_delete_student_not_found():
    """Test deleting a nonexistent student ID returns HTTP 404."""
    response = client.delete("/students/77777")
    assert response.status_code == 404


# ============================================================================
# 5. Search Functionality Tests (GitHub Issue Implementation)
# ============================================================================

def test_search_by_name(sample_students):
    """Test searching students by partial/full student name."""
    response = client.get("/students?search=Chandra")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["full_name"] == "Chandra Sekhar"


def test_search_by_register_number(sample_students):
    """Test searching students by register number."""
    response = client.get("/students?search=REG002")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["register_number"] == "REG002"
    assert results[0]["full_name"] == "Priya Sharma"


def test_search_case_insensitive(sample_students):
    """Test that student search is completely case-insensitive."""
    # Lowercase search
    res_lower = client.get("/students?search=chandra")
    assert res_lower.status_code == 200
    assert len(res_lower.json()) == 1

    # Uppercase search
    res_upper = client.get("/students?search=CHANDRA")
    assert res_upper.status_code == 200
    assert len(res_upper.json()) == 1

    # Mixed case register number search
    res_reg = client.get("/students?search=reg003")
    assert res_reg.status_code == 200
    assert len(res_reg.json()) == 1
    assert res_reg.json()[0]["full_name"] == "Rahul Verma"


def test_search_empty_query_returns_all(sample_students):
    """Test that an empty or whitespace-only search returns all students."""
    # Empty string
    res_empty = client.get("/students?search=")
    assert res_empty.status_code == 200
    assert len(res_empty.json()) == 3

    # Whitespace only
    res_spaces = client.get("/students?search=   ")
    assert res_spaces.status_code == 200
    assert len(res_spaces.json()) == 3


def test_search_no_match_returns_empty_list(sample_students):
    """Test that a search with no matching records returns an empty list []."""
    response = client.get("/students?search=NonExistentQueryXYZ")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) == 0


# ============================================================================
# 6. Statistics Endpoint Tests
# ============================================================================

def test_get_stats_empty():
    """Test stats endpoint when database has zero students."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 0
    assert data["department_counts"] == {}
    assert data["academic_year_counts"] == {}


def test_get_stats_with_data(sample_students):
    """Test stats endpoint with seeded student records."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 3
    assert data["department_counts"]["Computer Science"] == 1
    assert data["department_counts"]["Information Technology"] == 1
    assert data["department_counts"]["Electronics & Communication"] == 1
    assert data["academic_year_counts"]["3rd Year"] == 1
    assert data["academic_year_counts"]["2nd Year"] == 1
    assert data["academic_year_counts"]["4th Year"] == 1
