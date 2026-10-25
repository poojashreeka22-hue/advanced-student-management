"""
Application Configuration and Environment Settings.
"""

import os
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    PROJECT_NAME: str = "EduTrack Enterprise Student Management System"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENV: str = Field(default_factory=lambda: os.getenv("ENV", "development"))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "True").lower() in ("true", "1", "yes"))

    # Database
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./student_management.db")
    )

    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "edutrack-enterprise-secret-key-change-in-production-2026")
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "*"
    ]

    # Academic Rules
    MIN_ATTENDANCE_PERCENTAGE: float = 75.0
    DEFAULT_COURSE_CAPACITY: int = 60
    PASSING_GRADE_POINT: float = 2.0

    # Rate Limiting
    RATE_LIMIT_LOGIN_MAX: int = 30
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60


settings = Settings()
