from fastapi.testclient import TestClient


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


def test_recommander_returns_best_destination(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=3,
        estimated_wait_minutes=20,
    )
    _create_centre(
        client,
        centre_id="H_DISTRICT_1",
        specialities=["maternal"],
        capacity_available=2,
        estimated_wait_minutes=40,
    )
    _create_centre(
        client,
        centre_id="H_REGIONAL_1",
        specialities=["maternal"],
        capacity_available=6,
        estimated_wait_minutes=35,
    )

    _create_reference(client, "C_LOCAL_A", "H_DISTRICT_1", 20)
    _create_reference(client, "C_LOCAL_A", "H_REGIONAL_1", 60)

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P001",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "medium",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["destination_centre_id"] == "H_REGIONAL_1"
    assert body["path"][0]["centre_id"] == "C_LOCAL_A"
    assert body["path"][-1]["centre_id"] == "H_REGIONAL_1"
    assert "selected because it matches speciality" in body["explanation"]


def test_recommander_empty_network_returns_400(client: TestClient) -> None:
    response = client.post(
        "/recommander",
        json={
            "patient_id": "P002",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "medium",
        },
    )
    assert response.status_code == 400
    assert "Referral network is empty" in response.json()["detail"]


def test_recommander_speciality_unavailable_returns_400(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general"],
        capacity_available=3,
        estimated_wait_minutes=20,
    )
    _create_centre(
        client,
        centre_id="H_DISTRICT_1",
        specialities=["general"],
        capacity_available=2,
        estimated_wait_minutes=40,
    )
    _create_reference(client, "C_LOCAL_A", "H_DISTRICT_1", 20)

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P003",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "pediatric",
            "severity": "high",
        },
    )
    assert response.status_code == 400
    assert "No available destination" in response.json()["detail"]


def test_recommander_unreachable_destination_returns_400(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=3,
        estimated_wait_minutes=20,
    )
    _create_centre(
        client,
        centre_id="H_DISTRICT_1",
        specialities=["maternal"],
        capacity_available=4,
        estimated_wait_minutes=30,
    )
    # No reference edge between C_LOCAL_A and H_DISTRICT_1.

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P004",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "low",
        },
    )
    assert response.status_code == 400
    assert "No reachable destination" in response.json()["detail"]
