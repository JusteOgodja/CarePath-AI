from collections import Counter

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


def _get_centre(client: TestClient, centre_id: str) -> dict:
    response = client.get("/centres")
    assert response.status_code == 200
    for centre in response.json():
        if centre["id"] == centre_id:
            return centre
    raise AssertionError(f"Centre '{centre_id}' not found")


def _update_centre(
    client: TestClient,
    centre_id: str,
    *,
    capacity_available: int | None = None,
    estimated_wait_minutes: int | None = None,
) -> None:
    current = _get_centre(client, centre_id)
    payload = {
        "name": current["name"],
        "level": current["level"],
        "specialities": current["specialities"],
        "capacity_available": current["capacity_available"] if capacity_available is None else capacity_available,
        "estimated_wait_minutes": (
            current["estimated_wait_minutes"]
            if estimated_wait_minutes is None
            else estimated_wait_minutes
        ),
    }
    response = client.put(f"/centres/{centre_id}", json=payload)
    assert response.status_code == 200


def _recommend(client: TestClient, patient_id: str) -> dict:
    response = client.post(
        "/recommander",
        json={
            "patient_id": patient_id,
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "medium",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_saturation_forces_reroute_when_primary_center_becomes_full(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=3,
        estimated_wait_minutes=10,
    )
    _create_centre(
        client,
        centre_id="H_PRIMARY",
        specialities=["maternal"],
        capacity_available=4,
        estimated_wait_minutes=20,
    )
    _create_centre(
        client,
        centre_id="H_BACKUP",
        specialities=["maternal"],
        capacity_available=2,
        estimated_wait_minutes=35,
    )

    _create_reference(client, "C_LOCAL_A", "H_PRIMARY", 20)
    _create_reference(client, "C_LOCAL_A", "H_BACKUP", 25)

    first = _recommend(client, "P200")
    assert first["destination_centre_id"] == "H_PRIMARY"

    _update_centre(client, "H_PRIMARY", capacity_available=0)

    second = _recommend(client, "P201")
    assert second["destination_centre_id"] == "H_BACKUP"


def test_dynamic_wait_updates_distribute_referrals_across_centers(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=5,
        estimated_wait_minutes=10,
    )
    _create_centre(
        client,
        centre_id="H_EAST",
        specialities=["maternal"],
        capacity_available=4,
        estimated_wait_minutes=15,
    )
    _create_centre(
        client,
        centre_id="H_WEST",
        specialities=["maternal"],
        capacity_available=4,
        estimated_wait_minutes=18,
    )

    _create_reference(client, "C_LOCAL_A", "H_EAST", 20)
    _create_reference(client, "C_LOCAL_A", "H_WEST", 21)

    assigned = []
    for idx in range(6):
        recommendation = _recommend(client, f"P3{idx:02d}")
        chosen = recommendation["destination_centre_id"]
        assigned.append(chosen)

        centre_state = _get_centre(client, chosen)
        new_wait = centre_state["estimated_wait_minutes"] + 12
        _update_centre(client, chosen, estimated_wait_minutes=new_wait)

    counts = Counter(assigned)
    assert counts["H_EAST"] > 0
    assert counts["H_WEST"] > 0


def test_all_specialized_destinations_with_zero_capacity_return_400(client: TestClient) -> None:
    _create_centre(
        client,
        centre_id="C_LOCAL_A",
        specialities=["general", "maternal"],
        capacity_available=3,
        estimated_wait_minutes=10,
    )
    _create_centre(
        client,
        centre_id="H_FULL_1",
        specialities=["maternal"],
        capacity_available=0,
        estimated_wait_minutes=20,
    )
    _create_centre(
        client,
        centre_id="H_FULL_2",
        specialities=["maternal"],
        capacity_available=0,
        estimated_wait_minutes=25,
    )

    _create_reference(client, "C_LOCAL_A", "H_FULL_1", 10)
    _create_reference(client, "C_LOCAL_A", "H_FULL_2", 15)

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P400",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "high",
        },
    )

    assert response.status_code == 400
    assert "No available destination" in response.json()["detail"]
