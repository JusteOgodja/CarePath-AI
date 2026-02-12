from fastapi.testclient import TestClient

from app.db.models import CountryIndicatorModel, get_session


def test_indicator_endpoints_list_and_latest(client: TestClient) -> None:
    with get_session() as session:
        session.add_all(
            [
                CountryIndicatorModel(
                    country_code="KEN",
                    indicator_code="SH.MED.BEDS.ZS",
                    indicator_name="Hospital beds (per 1,000 people)",
                    year=2022,
                    value=1.25,
                    source_file="beds.csv",
                    metadata_json="{}",
                ),
                CountryIndicatorModel(
                    country_code="KEN",
                    indicator_code="SH.MED.BEDS.ZS",
                    indicator_name="Hospital beds (per 1,000 people)",
                    year=2023,
                    value=1.33,
                    source_file="beds.csv",
                    metadata_json="{}",
                ),
                CountryIndicatorModel(
                    country_code="KEN",
                    indicator_code="SH.STA.MMRT",
                    indicator_name="Maternal mortality ratio",
                    year=2023,
                    value=149.0,
                    source_file="mmr.csv",
                    metadata_json="{}",
                ),
            ]
        )
        session.commit()

    resp_all = client.get("/indicators", params={"country_code": "KEN"})
    assert resp_all.status_code == 200
    all_rows = resp_all.json()
    assert len(all_rows) == 3

    resp_latest = client.get("/indicators/latest", params={"country_code": "KEN"})
    assert resp_latest.status_code == 200
    latest_rows = resp_latest.json()
    assert len(latest_rows) == 2
    beds = [row for row in latest_rows if row["indicator_code"] == "SH.MED.BEDS.ZS"][0]
    assert beds["year"] == 2023
    assert beds["value"] == 1.33
