import asyncio
import httpx
import websockets
import json

BASE_URL = "http://127.0.0.1:8000"
WS_URL = BASE_URL.replace("http://", "ws://")

# ── Config ────────────────────────────────────────────────────
LEAD_ID = 1
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "Admin123"


async def get_token() -> str:
    """Login and get JWT token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        token = response.json()["access_token"]
        print(f"Logged in — token acquired")
        return token


async def trigger_status_change(token: str, lead_id: int, new_status: str) -> None:
    """Trigger a status change via REST."""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/leads/{lead_id}",
            json={"status": new_status},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"REST PATCH /leads/{lead_id} → {response.status_code}")
        print(f"   New status: {response.json().get('status')}")


async def main():
    print("\n🔌 Connecting to WebSocket...")

    token = await get_token()

    async with websockets.connect(
        f"{WS_URL}/leads/ws/{LEAD_ID}"
    ) as websocket:
        print(f"Connected to ws://localhost:8000/leads/ws/{LEAD_ID}")

        # Receive connection confirmation
        confirmation = await websocket.recv()
        print(f"\nConfirmation received:")
        print(f"   {json.loads(confirmation)}")

        print(f"\nTriggering status change via REST...")

        # Trigger status change in background
        asyncio.create_task(
            trigger_status_change(token, LEAD_ID, "contacted")
        )

        print(f"\nWaiting for WebSocket push...")

        # Wait for push message
        try:
            message = await asyncio.wait_for(
                websocket.recv(),
                timeout=35.0  # wait max 5 seconds
            )
            data = json.loads(message)
            print(f"\n WEBSOCKET PUSH RECEIVED:")
            print(f"   type:       {data.get('type')}")
            print(f"   lead_id:    {data.get('lead_id')}")
            print(f"   old_status: {data.get('old_status')}")
            print(f"   new_status: {data.get('new_status')}")
            print(f"\nWebSocket live updates working correctly!")

        except asyncio.TimeoutError:
            print(f"\nNo message received within 5 seconds")
            print(f"   Check that event bus listener is registered")


if __name__ == "__main__":
    asyncio.run(main())