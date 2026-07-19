from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from real_estate_backend.core.exceptions import (
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    AppException,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitExceededError,
    TokenExpiredError,
    WebhookSignatureError
)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        location = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": location,
            "message": error["msg"],
            "invalid_value": error.get("input"),
        })
    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )
  
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": exc.message}
    )


async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=409,
        content={"error": "Conflict", "message": exc.message}
    )


async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(
        status_code=403,
        content={"error": "Permission Denied", "message": exc.message}
    )


async def app_exception_handler(request: Request, exc: AppException):
    # Fallback for any unhandled AppException
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Error", "message": exc.message}
    )
    
async def invalid_credentials_handler(request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "message": exc.message}
    )


async def invalid_token_handler(request, exc: InvalidTokenError):
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "message": exc.message}
    )


async def token_expired_handler(request, exc: TokenExpiredError):
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "message": exc.message}
    )
    
    
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(
        status_code=429,
        headers={
            "Retry-After": str(exc.retry_after),
        },
        content={
            "error": "Too Many Requests",
            "message": exc.message,
            "retry_after": exc.retry_after,
        }
    )

async def webhook_signature_handler(request: Request, exc: WebhookSignatureError):
    return JSONResponse(
        status_code=401,
        content={
            "error": "Unauthorized",
            "message": exc.message,
        }
    )