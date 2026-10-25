"""
Core Domain Exceptions and HTTP Error Mappings.
"""

from typing import Any, Optional


class DomainException(Exception):
    """Base exception for all domain logic failures."""
    def __init__(self, message: str, status_code: int = 400, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.detail = message
        self.status_code = status_code
        self.details = details


class EntityNotFoundException(DomainException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(f"{entity_name} with identifier '{identifier}' was not found.", status_code=404)


class DuplicateEntityException(DomainException):
    def __init__(self, entity_name: str, field_name: str, value: Any):
        super().__init__(f"{entity_name} with {field_name} '{value}' already exists.", status_code=400)


class PrerequisiteNotMetException(DomainException):
    def __init__(self, course_code: str, prereq_code: str):
        super().__init__(
            f"Cannot enroll in {course_code}: required prerequisite {prereq_code} has not been completed with passing grade.",
            status_code=400
        )


class CapacityExceededException(DomainException):
    def __init__(self, course_code: str, max_capacity: int):
        super().__init__(
            f"Course {course_code} has reached its maximum capacity of {max_capacity} students.",
            status_code=400
        )


class ScheduleConflictException(DomainException):
    def __init__(self, conflict_details: str):
        super().__init__(f"Schedule conflict detected: {conflict_details}", status_code=409)


class UnauthorizedException(DomainException):
    def __init__(self, message: str = "Invalid credentials or authentication token missing"):
        super().__init__(message, status_code=401)


class ForbiddenException(DomainException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message, status_code=403)


class ValidationException(DomainException):
    def __init__(self, message: str, status_code: int = 400, details: Optional[Any] = None):
        super().__init__(message, status_code=status_code, details=details)


class InvalidPaymentException(DomainException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
