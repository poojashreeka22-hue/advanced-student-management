"""
Global exception handling middleware.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import DomainException
from app.core.logging import logger


async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(f"Domain exception: {exc.message} (status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "status_code": exc.status_code}
    )
