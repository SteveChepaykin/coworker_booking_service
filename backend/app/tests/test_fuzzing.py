from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta, timezone
import uuid

from app.core.security import create_access_token, verify_token

safe_text = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122), # a-z
    min_size=5,
    max_size=12
)

# --- Security Function Fuzzing ---

@given(subject=st.text())
@settings(max_examples=10)
def test_token_creation_and_verification(subject: str):
    """
    Tests that token creation and verification can handle a wide range of
    string inputs without crashing.
    """
    token = create_access_token(subject)
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == subject


# --- API Endpoint Fuzzing ---

@given(
    username_part=safe_text,
    email_part=safe_text,
    password=st.text(min_size=8, max_size=30)
)
@settings(max_examples=10)
def test_user_registration_fuzz(client: TestClient, username_part, email_part, password):
    unique_id = uuid.uuid4().hex[:8]
    username = f"{username_part}_{unique_id}"
    email = f"{email_part}_{unique_id}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password}
    )
    assert response.status_code != 500


@given(
    start_time=st.datetimes(
        min_value=datetime(2026, 1, 1),
        max_value=datetime(2027, 1, 1),
        timezones=st.just(timezone.utc)
    ),
    duration=st.timedeltas(
        min_value=timedelta(minutes=30),
        max_value=timedelta(hours=4)
    ),
    purpose=st.text(max_size=100)
)
@settings(max_examples=10, deadline=1000)
def test_booking_creation_fuzz(authenticated_client: TestClient, start_time, duration, purpose):
    room_id = "44444444-4444-4444-4444-444444444444"
    end_time = start_time + duration

    response = authenticated_client.post(
        "/api/v1/bookings/",
        json={
            "room_id": room_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "purpose": purpose,
        }
    )
    assert response.status_code != 500
