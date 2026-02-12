from fastapi.testclient import TestClient

from app.services.recommender import CandidateScore


def _create_centre(
    client: TestClient,
    *,
    centre_id: str,
    specialities: list[str],
    capacity_available: int,
    estimated_wait_minutes: int,
) -> None:
    payload = {
        "id": centre_id,
        "name": f"Centre {centre_id}",
        "level": "secondary",
        "specialities": specialities,
        "capacity_available": capacity_available,
        "estimated_wait_minutes": estimated_wait_minutes,
    }
    response = client.post("/centres", json=payload)
    assert response.status_code == 201


def _create_reference(client: TestClient, source_id: str, dest_id: str, travel_minutes: int) -> None:
    response = client.post(
        "/references",
        json={
            "source_id": source_id,
            "dest_id": dest_id,
            "travel_minutes": travel_minutes,
        },
    )
    assert response.status_code == 201


def test_candidate_score_formula_regression() -> None:
    candidate = CandidateScore(
        node_id="H1",
        path=["C1", "H1"],
        travel_minutes=30.0,
        wait_minutes=20.0,
        capacity=5,
        severity="medium",
    )
    assert candidate.score == 13.0


def test_recommender_prefers_higher_capacity_when_costs_close(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=3,
        estimated_wait_minutes=10,
    )
    _create_centre(
        client,
        centre_id="H_DISTRICT_1",
        specialities=["maternal"],
        capacity_available=2,
        estimated_wait_minutes=30,
    )
    _create_centre(
        client,
        centre_id="H_REGIONAL_1",
        specialities=["maternal"],
        capacity_available=6,
        estimated_wait_minutes=45,
    )

    _create_reference(client, "C_LOCAL_A", "H_DISTRICT_1", 20)  # score = (20 + 30) / 2 = 25
    _create_reference(client, "C_LOCAL_A", "H_REGIONAL_1", 30)  # score = (30 + 45) / 6 = 12.5

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P100",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "medium",
        },
    )

    assert response.status_code == 200
    assert response.json()["destination_centre_id"] == "H_REGIONAL_1"


def test_recommender_prefers_lower_wait_when_travel_equal_and_capacity_equal(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=3,
        estimated_wait_minutes=10,
    )
    _create_centre(
        client,
        centre_id="H_DISTRICT_1",
        specialities=["maternal"],
        capacity_available=4,
        estimated_wait_minutes=50,
    )
    _create_centre(
        client,
        centre_id="H_REGIONAL_1",
        specialities=["maternal"],
        capacity_available=4,
        estimated_wait_minutes=20,
    )

    _create_reference(client, "C_LOCAL_A", "H_DISTRICT_1", 20)  # score = (20 + 50) / 4 = 17.5
    _create_reference(client, "C_LOCAL_A", "H_REGIONAL_1", 20)  # score = (20 + 20) / 4 = 10

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P101",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "medium",
        },
    )

    assert response.status_code == 200
    assert response.json()["destination_centre_id"] == "H_REGIONAL_1"


def test_recommender_ignores_current_centre_as_destination(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=3,
        estimated_wait_minutes=10,
    )

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P102",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "low",
        },
    )

    assert response.status_code == 400
    assert "No available destination" in response.json()["detail"]
