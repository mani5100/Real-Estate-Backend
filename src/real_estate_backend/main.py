from fastapi import FastAPI
import time
import asyncio
from real_estate_backend.customers.router import router as customers_router
from real_estate_backend.properties.router import router as properties_router
from real_estate_backend.leads.router import router as leads_router
from real_estate_backend.auth.router import router as auth_router
from fastapi.exceptions import RequestValidationError
from real_estate_backend.core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    AppException,
    RateLimitExceededError,
    TokenExpiredError,
)
from real_estate_backend.core.exception_handlers import (
    invalid_credentials_handler,
    invalid_token_handler,
    not_found_handler,
    conflict_handler,
    permission_denied_handler,
    app_exception_handler,
    rate_limit_exceeded_handler,
    token_expired_handler,
    validation_exception_handler
)
from real_estate_backend.core.middleware import RequestLoggingMiddleware
import real_estate_backend.core.listeners

app = FastAPI(title="Real Estate Backend")
app.add_middleware(RequestLoggingMiddleware)

app.include_router(customers_router)
app.include_router(properties_router)
app.include_router(leads_router)
app.include_router(auth_router)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(ConflictError, conflict_handler)
app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
app.add_exception_handler(InvalidTokenError, invalid_token_handler)
app.add_exception_handler(TokenExpiredError, token_expired_handler)
app.add_exception_handler(RateLimitExceededError, rate_limit_exceeded_handler)


@app.get("/")
def root():
    return {"message": "Real Estate API is running"}


@app.get("/benchmark/blocking")
async def benchmark_blocking():
    time.sleep(1)
    return {"status": "done"}


@app.get("/benchmark/fixed")
async def benchmark_fixed():
    await asyncio.sleep(1)
    return {"status": "done"}