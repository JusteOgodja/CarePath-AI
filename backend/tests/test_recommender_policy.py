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


def test_recommander_rl_policy_falls_back_to_heuristic_when_model_missing(
    client: TestClient, monkeypatch
) -> None:
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

    monkeypatch.setenv("RL_MODEL_PATH", "does_not_exist_model.zip")

    response = client.post(
        "/recommander",
        json={
            "patient_id": "P_RL_FALLBACK",
            "current_centre_id": "C_LOCAL_A",
            "needed_speciality": "maternal",
            "severity": "medium",
            "routing_policy": "rl",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["policy_used"] == "heuristic"
    assert "fallback" in body["fallback_reason"].lower()

