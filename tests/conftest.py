"""
Pytest configuration, shared fixtures, in-memory database engine, and TestClient.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models import User, Department, Course, Faculty, Student, Classroom
from app.core.security import hash_password, create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def init_test_schema():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient with database dependency overridden to the transactional test session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token() -> str:
    return create_access_token({"sub": "admin", "role": "admin"})


@pytest.fixture
def faculty_token() -> str:
    return create_access_token({"sub": "faculty", "role": "faculty"})


@pytest.fixture
def student_token() -> str:
    return create_access_token({"sub": "student_user", "role": "student"})


@pytest.fixture
def finance_token() -> str:
    return create_access_token({"sub": "finance_user", "role": "finance"})


@pytest.fixture
def sample_department(db_session: Session) -> Department:
    dept = Department(
        code="CS_TEST",
        name="Computer Science Test Dept",
        head_of_department="Dr. Lovelace",
        building="Hall A",
        budget=100000.0
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


@pytest.fixture
def sample_course(db_session: Session, sample_department: Department) -> Course:
    course = Course(
        code="CS101_TEST",
        title="Intro to Computing",
        credits=3,
        department_id=sample_department.id,
        max_capacity=50,
        semester=1,
        academic_year="2026-2027"
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


@pytest.fixture
def sample_student(db_session: Session, sample_department: Department) -> Student:
    student = Student(
        register_number="REG_TEST_001",
        full_name="Grace Hopper",
        first_name="Grace",
        last_name="Hopper",
        email="grace.hopper@test.edu",
        phone_number="9876543210",
        department="Computer Science Test Dept",
        department_id=sample_department.id,
        academic_year="1st Year",
        semester=1,
        status="active"
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student
