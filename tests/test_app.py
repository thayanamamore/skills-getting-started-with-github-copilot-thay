import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    expected_location = "/static/index.html"

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data():
    expected_activity = "Chess Club"

    response = client.get("/activities")

    assert response.status_code == 200
    assert expected_activity in response.json()
    assert {"description", "schedule", "max_participants", "participants"} <= set(
        response.json()[expected_activity]
    )


def test_signup_adds_student_to_activity():
    activity_name = "Art Club"
    email = "student@mergington.edu"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"


def test_signup_rejects_unknown_activity():
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_student():
    activity_name = "Art Club"
    email = "student@mergington.edu"
    activities[activity_name]["participants"].append(email)

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_requires_email():
    activity_name = "Art Club"

    response = client.post(f"/activities/{activity_name}/signup")

    assert response.status_code == 422


def test_unregister_removes_student_from_activity():
    activity_name = "Art Club"
    email = "student@mergington.edu"
    activities[activity_name]["participants"].append(email)

    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"


def test_unregister_rejects_unknown_activity():
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_student_not_signed_up():
    activity_name = "Art Club"
    email = "student@mergington.edu"

    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_requires_email():
    activity_name = "Art Club"

    response = client.delete(f"/activities/{activity_name}/unregister")

    assert response.status_code == 422