"""
Global error handlers for FastAPI application
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors (422)"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "message": "Please check your request parameters"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions (500)"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )
