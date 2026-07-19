import hmac
import hashlib
import json
from real_estate_backend.core.config import settings

WEBHOOK_SECRET = settings.webhook_secret

payload = {
    "customer_id": 999,
    "property_id": 1,
    "status": "contacted",
    "agent_id": 1,
    "notes": "Came from external CRM via webhook"
}

raw_body = json.dumps(payload).encode("utf-8")

signature = hmac.new(
    key=WEBHOOK_SECRET.encode("utf-8"),
    msg=raw_body,
    digestmod=hashlib.sha256,
).hexdigest()

print(f"Payload: {json.dumps(payload)}")
print(f"X-Signature: {signature}")