import hmac
import hashlib
from fastapi import Request, Header
from typing import Optional
from real_estate_backend.core.config import settings
from real_estate_backend.core.exceptions import WebhookSignatureError
from real_estate_backend.core.logging import logger


def compute_signature(payload: bytes) -> str:
    """
    Computes HMAC-SHA256 signature from raw payload bytes.
    """
    return hmac.new(
        key=settings.webhook_secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()


async def validate_webhook_signature(
    request: Request,
    x_signature: Optional[str] = Header(default=None),
) -> bytes:
    """
    Dependency that:
    1. Reads raw request body
    2. Checks X-Signature header exists
    3. Computes expected signature
    4. Compares with received signature
    5. Raises 401 if anything is wrong

    Returns raw body so endpoint can parse it.
    """
    raw_body = await request.body()

    if not x_signature:
        logger.warning("Webhook rejected — missing X-Signature header")
        raise WebhookSignatureError("Missing X-Signature header")

    expected = compute_signature(raw_body)
    
    if not hmac.compare_digest(expected, x_signature):
        logger.warning(
            "Webhook rejected — invalid signature",
            extra={
                "expected": expected[:10] + "...",  
                "received": x_signature[:10] + "...",
            }
        )
        raise WebhookSignatureError("Invalid signature")

    logger.info("Webhook signature validated successfully")
    return raw_body