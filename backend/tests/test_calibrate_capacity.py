import sys
from pathlib import Path

from app.db.models import CentreModel, get_session

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from calibrate_capacity import calibrated_capacity
from calibrate_capacity import resolve_beds_per_10000
from app.integrations.who_gho_client import GhoPoint, WhoGhoClient


def test_capacity_calibration_logic_known_input() -> None:
    assert calibrated_capacity(10000, 20.0) == 20
    assert calibrated_capacity(5000, 20.0) == 10


def test_capacity_calibration_persistence() -> None:
    with get_session() as session:
        centre = CentreModel(
            id="CAL_TEST",
            name="Cal Test",
            lat=6.0,
            lon=3.0,
            osm_type="node",
            osm_id="cal_test",
            level="primary",
            specialities="general",
            raw_tags_json="{}",
            capacity_max=10,
            capacity_available=10,
            estimated_wait_minutes=15,
            catchment_population=25000,
        )
        session.add(centre)
        session.commit()

        centre.capacity_max = calibrated_capacity(centre.catchment_population or 0, 20.0)
        centre.capacity_available = int(centre.capacity_max * 0.8)
        session.commit()

        refreshed = session.get(CentreModel, "CAL_TEST")
        assert refreshed is not None
        assert refreshed.capacity_max == 50
        assert refreshed.capacity_available == 40


def test_resolve_beds_manual_source() -> None:
    class Args:
        beds_per_10000 = 18.0
        who_indicator = None
        who_country = None
        who_year = None
        who_base_url = "https://ghoapi.azureedge.net"

    value, source = resolve_beds_per_10000(Args)
    assert value == 18.0
    assert source["source"] == "manual"


def test_resolve_beds_who_source(monkeypatch) -> None:
    def fake_select(self, *, indicator: str, country: str, year: int | None = None):
        return GhoPoint(country=country, year=2021, numeric_value=14.5)

    monkeypatch.setattr(WhoGhoClient, "select_country_value", fake_select)

    class Args:
        beds_per_10000 = None
        who_indicator = "HWF_0000"
        who_country = "CM"
        who_year = None
        who_base_url = "https://ghoapi.azureedge.net"

    value, source = resolve_beds_per_10000(Args)
    assert value == 14.5
    assert source["source"] == "who_gho"
    assert source["indicator"] == "HWF_0000"
