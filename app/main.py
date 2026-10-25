"""
FastAPI Enterprise Application: EduTrack Student Information and Academic Management Platform.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DomainException
from app.database.init_db import init_db
from app.database.session import get_db
from app.middleware.error_handler import domain_exception_handler
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.api_router import api_router

# Direct legacy endpoints support
from app.api.v1.students import (
    create_student,
    get_students,
    get_student,
    update_student,
    delete_student
)
from app.api.v1.analytics import get_stats
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.schemas.analytics import StatsResponse
from app.schemas.common import MessageResponse

# Initialize database schema and default records
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Student Information and Academic Management Platform"
)

# Exception handlers
app.add_exception_handler(DomainException, domain_exception_handler)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

# Mount API V1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount legacy/root endpoints for full backward compatibility
app.add_api_route("/students", create_student, methods=["POST"], response_model=StudentResponse, status_code=status.HTTP_201_CREATED, tags=["Students Legacy"])
app.add_api_route("/students", get_students, methods=["GET"], response_model=List[StudentResponse], tags=["Students Legacy"])
app.add_api_route("/students/{student_id}", get_student, methods=["GET"], response_model=StudentResponse, tags=["Students Legacy"])
app.add_api_route("/students/{student_id}", update_student, methods=["PUT"], response_model=StudentResponse, tags=["Students Legacy"])
app.add_api_route("/students/{student_id}", delete_student, methods=["DELETE"], response_model=MessageResponse, tags=["Students Legacy"])
app.add_api_route("/stats", get_stats, methods=["GET"], response_model=StatsResponse, tags=["Analytics Legacy"])

# Resolve path to static assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serve the modern administration GUI dashboard."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "EduTrack API is running. GUI files not found."}
