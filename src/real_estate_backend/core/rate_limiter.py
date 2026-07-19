from fastapi import Request, Depends
from real_estate_backend.core.rate_limit_store import rate_limit_store
from real_estate_backend.core.exceptions import RateLimitExceededError
from real_estate_backend.auth.dependencies import get_current_user
from real_estate_backend.users.model import User

# Configuration
RATE_LIMIT = 5          # max requests
WINDOW_SECONDS = 60     # per 60 seconds


def get_client_key(request: Request, current_user: User | None) -> str:
    """
    Build identity key for rate limiting.
    Logged in  → keyed by user_id (fair per user)
    Not logged in → keyed by IP (fallback)
    """
    if current_user:
        return f"user:{current_user.id}"

    # Extract real IP — handles proxies
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host

    return f"ip:{ip}"


def make_rate_limiter(limit: int = RATE_LIMIT, window_seconds: int = WINDOW_SECONDS):

    def rate_limiter(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> None:
        key = get_client_key(request, current_user)

        is_allowed, retry_after = rate_limit_store.is_allowed(
            key, limit, window_seconds
        )

        remaining = rate_limit_store.get_remaining(key, limit)
        reset_time = rate_limit_store.get_reset_time(key, window_seconds)

        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if not is_allowed:
            raise RateLimitExceededError(retry_after)

    return rate_limiter


rate_limiter = make_rate_limiter()