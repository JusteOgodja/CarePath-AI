import sys
from pathlib import Path

import httpx

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from app.integrations.who_gho_client import WhoGhoClient


def test_select_country_value_uses_latest_when_year_not_provided(monkeypatch) -> None:
    def fake_fetch(self, indicator: str, timeout: float = 20.0):
        return [
            {"SpatialDim": "CM", "TimeDim": 2018, "NumericValue": 12.5},
            {"SpatialDim": "CM", "TimeDim": 2020, "NumericValue": 16.0},
            {"SpatialDim": "FR", "TimeDim": 2020, "NumericValue": 20.0},
        ]

    monkeypatch.setattr(WhoGhoClient, "fetch_indicator_data", fake_fetch)
    client = WhoGhoClient()
    point = client.select_country_value(indicator="HWF_0000", country="CM", year=None)
    assert point.country == "CM"
    assert point.year == 2020
    assert point.numeric_value == 16.0


def test_fetch_indicator_data_with_mocked_http(monkeypatch) -> None:
    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str, params: dict):
            payload = {"value": [{"SpatialDim": "CM", "TimeDim": 2021, "NumericValue": 14.0}]}
            request = httpx.Request("GET", url, params=params)
            return httpx.Response(status_code=200, json=payload, request=request)

    monkeypatch.setattr(httpx, "Client", DummyClient)
    client = WhoGhoClient(base_url="https://ghoapi.azureedge.net")
    rows = client.fetch_indicator_data("HWF_0000")
    assert len(rows) == 1
    assert rows[0]["SpatialDim"] == "CM"
