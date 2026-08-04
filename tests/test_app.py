from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)
initial_activities = deepcopy(activities)


@pytest.fixture(autouse=True)
def restore_activities():
    activities.clear()
    activities.update(deepcopy(initial_activities))

    yield

    activities.clear()
    activities.update(deepcopy(initial_activities))


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activities = deepcopy(initial_activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    encoded_activity_name = quote(activity_name, safe="")
    initial_participants = deepcopy(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities[activity_name]["participants"] == initial_participants


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    email = "new.student@mergington.edu"
    encoded_activity_name = quote(activity_name, safe="")
    expected_activities = deepcopy(activities)

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == expected_activities


def test_unregister_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    encoded_activity_name = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/participants/{encoded_email}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"
    encoded_activity_name = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/participants/{encoded_email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unknown_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "unknown.student@mergington.edu"
    encoded_activity_name = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")
    initial_participants = deepcopy(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/participants/{encoded_email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}
    assert activities[activity_name]["participants"] == initial_participants