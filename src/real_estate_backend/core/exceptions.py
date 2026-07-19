# No FastAPI imports here — pure Python only


class AppException(Exception):
    """Base exception for all app errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ── 404 Not Found ───────────────────────────────────────
class NotFoundError(AppException):
    """Base for all not found errors."""
    pass


class CustomerNotFoundError(NotFoundError):
    def __init__(self, customer_id: int):
        super().__init__(f"Customer with id {customer_id} not found")


class PropertyNotFoundError(NotFoundError):
    def __init__(self, property_id: int):
        super().__init__(f"Property with id {property_id} not found")


class LeadNotFoundError(NotFoundError):
    def __init__(self, lead_id: int):
        super().__init__(f"Lead with id {lead_id} not found")


# ── 409 Conflict ─────────────────────────────────────────
class ConflictError(AppException):
    """Base for all conflict errors."""
    pass


class EmailAlreadyExistsError(ConflictError):
    def __init__(self, email: str):
        super().__init__(f"Email {email} is already registered")


class CustomerHasLeadsError(ConflictError):
    def __init__(self, customer_id: int):
        super().__init__(f"Customer {customer_id} has existing leads and cannot be deleted")


class PropertyHasLeadsError(ConflictError):
    def __init__(self, property_id: int):
        super().__init__(f"Property {property_id} has existing leads and cannot be deleted")


# ── 403 Permission Denied ────────────────────────────────
class PermissionDeniedError(AppException):
    def __init__(self, action: str):
        super().__init__(f"Permission denied: {action}")
        
        
class NoPropertiesFoundError(NotFoundError):
    def __init__(self, bedrooms: int):
        super().__init__(f"No properties found with {bedrooms} bedrooms")
        
# ── User Exceptions ────────────────────────────────   
class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: int):
        super().__init__(f"User with id {user_id} not found")


class InvalidCredentialsError(AppException):
    def __init__(self):
        super().__init__("Invalid email or password")


class TokenExpiredError(AppException):
    def __init__(self):
        super().__init__("Token has expired, please login again")


class InvalidTokenError(AppException):
    def __init__(self):
        super().__init__("Invalid token")
        
# Rate Limiting Exceptions
class RateLimitExceededError(AppException):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Try again in {retry_after} seconds.")

# Webhook Signature Exception
class WebhookSignatureError(AppException):
    def __init__(self, message: str = "Invalid webhook signature"):
        super().__init__(message)