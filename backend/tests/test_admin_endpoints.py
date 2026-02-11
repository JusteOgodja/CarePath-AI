from fastapi.testclient import TestClient


def _create_centre(client: TestClient, centre_id: str) -> None:
    payload = {
        "id": centre_id,
        "name": f"Centre {centre_id}",
        "level": "secondary",
        "specialities": ["general", "maternal"],
        "capacity_available": 5,
        "estimated_wait_minutes": 25,
    }
    response = client.post("/centres", json=payload)
    assert response.status_code == 201


def test_create_and_list_centre(client: TestClient) -> None:
    payload = {
        "id": "H_DISTRICT_2",
        "name": "Hopital District 2",
        "level": "secondary",
        "specialities": ["general", "maternal"],
        "capacity_available": 5,
        "estimated_wait_minutes": 25,
    }

    created = client.post("/centres", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == payload["id"]
    assert body["specialities"] == payload["specialities"]

    listed = client.get("/centres")
    assert listed.status_code == 200
    assert any(item["id"] == payload["id"] for item in listed.json())


def test_duplicate_centre_returns_409(client: TestClient) -> None:
    payload = {
        "id": "H_DISTRICT_2",
        "name": "Hopital District 2",
        "level": "secondary",
        "specialities": ["general"],
        "capacity_available": 5,
        "estimated_wait_minutes": 25,
    }
    first = client.post("/centres", json=payload)
    assert first.status_code == 201

    second = client.post("/centres", json=payload)
    assert second.status_code == 409


def test_delete_centre_with_reference_returns_409(client: TestClient) -> None:
    _create_centre(client, "C_LOCAL_A")
    _create_centre(client, "H_DISTRICT_1")

    ref_response = client.post(
        "/references",
        json={"source_id": "C_LOCAL_A", "dest_id": "H_DISTRICT_1", "travel_minutes": 18},
    )
    assert ref_response.status_code == 201

    delete_response = client.delete("/centres/C_LOCAL_A")
    assert delete_response.status_code == 409


def test_create_reference_requires_existing_nodes(client: TestClient) -> None:
    response = client.post(
        "/references",
        json={"source_id": "MISSING_A", "dest_id": "MISSING_B", "travel_minutes": 20},
    )
    assert response.status_code == 400


def test_reference_crud_flow(client: TestClient) -> None:
    _create_centre(client, "C_LOCAL_A")
    _create_centre(client, "H_DISTRICT_1")
    _create_centre(client, "H_REGIONAL_1")

    created = client.post(
        "/references",
        json={"source_id": "C_LOCAL_A", "dest_id": "H_DISTRICT_1", "travel_minutes": 20},
    )
    assert created.status_code == 201
    created_id = created.json()["id"]

    updated = client.put(
        f"/references/{created_id}",
        json={"source_id": "C_LOCAL_A", "dest_id": "H_REGIONAL_1", "travel_minutes": 45},
    )
    assert updated.status_code == 200
    assert updated.json()["dest_id"] == "H_REGIONAL_1"

    listed = client.get("/references")
    assert listed.status_code == 200
    assert any(item["id"] == created_id for item in listed.json())

    deleted = client.delete(f"/references/{created_id}")
    assert deleted.status_code == 204

    listed_after = client.get("/references")
    assert listed_after.status_code == 200
    assert all(item["id"] != created_id for item in listed_after.json())
