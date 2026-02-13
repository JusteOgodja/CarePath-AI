from fastapi.testclient import TestClient


def _create_centre(client: TestClient, centre_id: str, specialities: list[str]) -> None:
    payload = {
        "id": centre_id,
        "name": f"Centre {centre_id}",
        "level": "secondary",
        "specialities": specialities,
        "capacity_max": 10,
        "capacity_available": 6,
        "estimated_wait_minutes": 20,
    }
    response = client.post("/centres", json=payload)
    assert response.status_code == 201


def test_referral_workflow_happy_path(client: TestClient) -> None:
    _create_centre(client, "C_SRC", ["general", "maternal"])
    _create_centre(client, "H_DST", ["maternal"])

    created = client.post(
        "/referrals/requests",
        json={
            "patient_id": "P001",
            "source_id": "C_SRC",
            "needed_speciality": "maternal",
            "severity": "high",
            "proposed_dest_id": "H_DST",
            "notes": "Urgent obstetric case",
        },
    )
    assert created.status_code == 201
    rid = created.json()["id"]
    assert created.json()["status"] == "pending"

    accepted = client.post(
        f"/referrals/requests/{rid}/accept",
        json={"accepted_dest_id": "H_DST", "notes": "Destination confirmed"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    started = client.post(
        f"/referrals/requests/{rid}/start-transfer",
        json={"notes": "Ambulance departed"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "in_transit"

    completed = client.post(
        f"/referrals/requests/{rid}/complete",
        json={
            "diagnosis": "Postpartum hemorrhage",
            "treatment": "Transfusion and surgery",
            "followup": "Weekly review",
            "notes": "Patient stabilized",
        },
    )
    assert completed.status_code == 200
    body = completed.json()
    assert body["status"] == "completed"
    assert body["feedback_diagnosis"] == "Postpartum hemorrhage"


def test_referral_accept_wrong_status_returns_409(client: TestClient) -> None:
    _create_centre(client, "C_SRC2", ["general", "maternal"])
    _create_centre(client, "H_DST2", ["maternal"])

    created = client.post(
        "/referrals/requests",
        json={
            "patient_id": "P002",
            "source_id": "C_SRC2",
            "needed_speciality": "maternal",
            "severity": "medium",
            "proposed_dest_id": "H_DST2",
        },
    )
    assert created.status_code == 201
    rid = created.json()["id"]

    first_accept = client.post(f"/referrals/requests/{rid}/accept", json={"accepted_dest_id": "H_DST2"})
    assert first_accept.status_code == 200
    second_accept = client.post(f"/referrals/requests/{rid}/accept", json={"accepted_dest_id": "H_DST2"})
    assert second_accept.status_code == 409


def test_referral_list_requires_auth() -> None:
    from app.main import app

    raw = TestClient(app)
    response = raw.get("/api/v1/referrals/requests")
    assert response.status_code == 401
