"""
Role-Based Access Control (RBAC) and Permission definitions.
"""

from enum import Enum
from typing import List


class Role(str, Enum):
    ADMIN = "admin"
    FACULTY = "faculty"
    STUDENT = "student"
    FINANCE = "finance"


class Permissions:
    ALL = [Role.ADMIN, Role.FACULTY, Role.STUDENT, Role.FINANCE]
    ADMIN_ONLY = [Role.ADMIN]
    FACULTY_AND_ADMIN = [Role.ADMIN, Role.FACULTY]
    FINANCE_AND_ADMIN = [Role.ADMIN, Role.FINANCE]
    ACADEMIC_STAFF = [Role.ADMIN, Role.FACULTY]
