"""
Database initialization and default seeding.
"""

from app.database.session import engine, SessionLocal
from app.database.base import Base
from app.models.user import User
from app.models.department import Department
from app.models.timetable import Classroom
from app.core.security import hash_password
from app.core.logging import logger


def init_db() -> None:
    """Create all database tables and seed baseline admin user and baseline departments if empty."""
    Base.metadata.create_all(bind=engine)

    # Ensure schema migrations for existing databases
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info(departments)")).fetchall()
            cols = [r[1] for r in res]
            if cols and "hod_faculty_id" not in cols:
                conn.execute(text("ALTER TABLE departments ADD COLUMN hod_faculty_id INTEGER REFERENCES faculty(id)"))
                conn.commit()
    except Exception as e:
        logger.warning(f"Schema migration warning: {e}")

    db = SessionLocal()
    try:
        # Seed default admin user if none exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@university.edu",
                hashed_password=hash_password("Admin@12345"),
                full_name="System Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)

        # Seed default faculty user if none exists
        faculty_user = db.query(User).filter(User.username == "faculty").first()
        if not faculty_user:
            faculty_user = User(
                username="faculty",
                email="faculty@university.edu",
                hashed_password=hash_password("Faculty@12345"),
                full_name="Prof. Alan Turing",
                role="faculty",
                is_active=True
            )
            db.add(faculty_user)

        # Seed default finance user if none exists
        finance_user = db.query(User).filter(User.username == "finance").first()
        if not finance_user:
            finance_user = User(
                username="finance",
                email="finance@university.edu",
                hashed_password=hash_password("Finance@12345"),
                full_name="Finance Bursar",
                role="finance",
                is_active=True
            )
            db.add(finance_user)

        # Seed baseline departments if none exist
        if db.query(Department).count() == 0:
            departments = [
                Department(code="CS", name="Computer Science", head_of_department="Dr. Ada Lovelace", building="Turing Hall", budget=500000.0),
                Department(code="IT", name="Information Technology", head_of_department="Dr. Tim Berners-Lee", building="Shannon Wing", budget=450000.0),
                Department(code="ECE", name="Electronics & Communication", head_of_department="Dr. Claude Shannon", building="Maxwell Lab", budget=480000.0),
                Department(code="MECH", name="Mechanical Engineering", head_of_department="Dr. Nikola Tesla", building="Watt Pavilion", budget=520000.0),
                Department(code="CIVIL", name="Civil Engineering", head_of_department="Dr. John Smeaton", building="Brindley Block", budget=420000.0)
            ]
            db.add_all(departments)

        # Seed baseline classrooms if none exist
        if db.query(Classroom).count() == 0:
            classrooms = [
                Classroom(room_number="LH-101", building="Turing Hall", capacity=80, room_type="lecture_hall"),
                Classroom(room_number="LAB-201", building="Shannon Wing", capacity=45, room_type="lab"),
                Classroom(room_number="SEM-301", building="Maxwell Lab", capacity=50, room_type="seminar"),
                Classroom(room_number="LH-102", building="Watt Pavilion", capacity=90, room_type="lecture_hall")
            ]
            db.add_all(classrooms)

        db.commit()
        logger.info("Database initialized with baseline schema and seed data.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()


def get_db():
    from app.database.session import get_db as _get_db
    yield from _get_db()
