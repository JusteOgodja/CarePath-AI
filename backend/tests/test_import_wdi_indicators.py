import sys
from pathlib import Path

from app.db.models import CountryIndicatorModel, get_session

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from import_wdi_indicators import parse_wdi_file, reduce_latest_only, upsert_points


def test_import_wdi_latest_only(tmp_path: Path) -> None:
    csv_path = tmp_path / "API_SAMPLE.csv"
    csv_path.write_text(
        "\n".join(
            [
                '"Data Source","World Development Indicators",',
                "",
                '"Country Name","Country Code","Indicator Name","Indicator Code","2021","2022","2023"',
                '"Kenya","KEN","Hospital beds (per 1,000 people)","SH.MED.BEDS.ZS","1.20","1.25","1.33"',
                '"Kenya","KEN","Physicians (per 1,000 people)","SH.MED.PHYS.ZS","","0.28","0.289"',
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_wdi_file(csv_path, "KEN")
    latest = reduce_latest_only(parsed)
    inserted, updated = upsert_points(latest)

    assert inserted == 2
    assert updated == 0

    with get_session() as session:
        rows = session.query(CountryIndicatorModel).all()
    assert len(rows) == 2
    codes = {r.indicator_code for r in rows}
    assert "SH.MED.BEDS.ZS" in codes
    assert "SH.MED.PHYS.ZS" in codes
