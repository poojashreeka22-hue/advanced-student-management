"""
Performance and Reliability Benchmark Test Suite.
Tests query efficiency, large-dataset search latency, pagination across records, and analytics aggregation throughput.
"""

import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.base import Base
from app.models import Student
from app.services.student_service import StudentService
from app.services.analytics_service import AnalyticsService

BENCHMARK_DATASET_SIZE = 1000


@pytest.fixture(scope="module")
def perf_session():
    """Isolated in-memory database with synthetic dataset of 1,000 students."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Bulk insert synthetic students
    students = [
        Student(
            register_number=f"PERF_{i:05d}",
            full_name=f"Performance Student {i}",
            email=f"perf_student_{i}@test.edu",
            phone_number=f"98765{i:05d}",
            department="Computer Science" if i % 2 == 0 else "Information Technology",
            academic_year="1st Year" if i % 4 == 0 else "2nd Year",
            semester=(i % 8) + 1,
            status="active" if i % 5 != 0 else "graduated",
            gpa=round(2.0 + ((i % 20) * 0.1), 2)
        )
        for i in range(1, BENCHMARK_DATASET_SIZE + 1)
    ]
    session.bulk_save_objects(students)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


def test_perf_search_latency(perf_session):
    """Benchmark student search query execution time under 1,000 records."""
    service = StudentService(perf_session)

    start = time.perf_counter()
    results, total = service.search_students(search="Student 500")
    duration = time.perf_counter() - start

    assert total >= 1
    assert duration < 0.15, f"Search took {duration:.4f}s, expected < 0.15s"
    print(f"\n[PERF BENCHMARK] Search query took: {duration * 1000:.2f}ms")


def test_perf_pagination_latency(perf_session):
    """Benchmark deep pagination across dataset."""
    service = StudentService(perf_session)

    start = time.perf_counter()
    results, total = service.search_students(skip=800, limit=50)
    duration = time.perf_counter() - start

    assert len(results) == 50
    assert duration < 0.10, f"Pagination took {duration:.4f}s, expected < 0.10s"
    print(f"\n[PERF BENCHMARK] Deep pagination (offset 800) took: {duration * 1000:.2f}ms")


def test_perf_analytics_rollup_latency(perf_session):
    """Benchmark analytics department rollup aggregation time."""
    service = AnalyticsService(perf_session)

    start = time.perf_counter()
    stats = service.get_legacy_stats()
    duration = time.perf_counter() - start

    assert stats.total_students == BENCHMARK_DATASET_SIZE
    assert duration < 0.10, f"Analytics rollup took {duration:.4f}s, expected < 0.10s"
    print(f"\n[PERF BENCHMARK] Analytics rollup took: {duration * 1000:.2f}ms")
