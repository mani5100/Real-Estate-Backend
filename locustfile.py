import random
import requests
from locust import HttpUser, task, between, events
import urllib3

urllib3.disable_warnings()

# ── Auth token fetched once at startup ────────────────────────
AUTH_TOKEN = None
HOST = "http://127.0.0.1:8000"


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Runs once before load test starts.
    Uses requests library directly — no user class needed.
    """
    global AUTH_TOKEN

    print("\n[Locust] Fetching auth token...")

    response = requests.post(
        f"{HOST}/auth/login",
        json={
            "email": "admin@test.com",
            "password": "Admin123",
        }
    )

    if response.status_code == 200:
        AUTH_TOKEN = response.json()["access_token"]
        print(f"[Locust] Token acquired: {AUTH_TOKEN[:20]}...")
    else:
        print(f"[Locust] Login failed: {response.status_code} {response.text}")


class RealEstateUser(HttpUser):
    wait_time = between(1, 3)
    host = HOST

    def on_start(self):
        self.headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        self.lead_id = random.randint(1, 10)

    @task(1)
    def update_lead_status(self):
        statuses = ["new", "contacted", "qualified"]
        new_status = random.choice(statuses)

        with self.client.patch(
            f"/leads/{self.lead_id}",
            json={"status": new_status},
            headers=self.headers,
            name="PATCH /leads/{id} (status update)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [404, 429, 403]:
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")

    @task(2)
    def get_single_lead(self):
        with self.client.get(
            f"/leads/{self.lead_id}",
            headers=self.headers,
            name="GET /leads/{id} (nested)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "customer" not in data or "property" not in data:
                    response.failure("Missing nested objects")
                else:
                    response.success()
            elif response.status_code in [404, 429, 403]:
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")

    @task(2)
    def list_properties(self):
        with self.client.get(
            "/properties/",
            params={"limit": 3},
            name="GET /properties/ (public)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")
    @task(3)
    def list_leads_paginated(self):
        params = {"limit": 3}

        with self.client.get(
            "/leads/",
            params=params,
            headers=self.headers,
            name="GET /leads/ (paginated)",
            catch_response=True,
        ) as response:
            # Print actual response for debugging
            print(f"Status: {response.status_code}, Body: {response.text[:200]}")

            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Status {response.status_code}: {response.text[:100]}")