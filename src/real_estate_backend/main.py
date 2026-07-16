from fastapi import FastAPI
from real_estate_backend.customers.router import router as customers_router
from real_estate_backend.properties.router import router as properties_router
from real_estate_backend.leads.router import router as leads_router
from fastapi.exceptions import RequestValidationError
from real_estate_backend.core.exceptions import (
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    AppException,
)
from real_estate_backend.core.exception_handlers import (
    not_found_handler,
    conflict_handler,
    permission_denied_handler,
    app_exception_handler,
    validation_exception_handler
)
from real_estate_backend.core.middleware import RequestLoggingMiddleware

app = FastAPI(title="Real Estate Backend")

app.add_middleware(RequestLoggingMiddleware)

app.include_router(customers_router)
app.include_router(properties_router)
app.include_router(leads_router)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(ConflictError, conflict_handler)
app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
app.add_exception_handler(AppException, app_exception_handler)


@app.get("/")
def root():
    return {"message": "Real Estate API is running"}