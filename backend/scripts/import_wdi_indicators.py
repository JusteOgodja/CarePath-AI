from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CountryIndicatorModel, get_session, init_db

YEAR_RE = re.compile(r"^\d{4}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import WDI indicator CSV files into country_indicators table")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/kenya",
        help="Root folder containing WDI API_*.csv files",
    )
    parser.add_argument("--country-code", type=str, default="KEN")
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Store only the most recent non-empty year per indicator",
    )
    return parser.parse_args()


def find_wdi_files(input_dir: Path) -> list[Path]:
    return sorted(input_dir.rglob("API_*_DS2_en_csv_*.csv"))


def parse_wdi_file(path: Path, country_code: str) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    header_idx = None
    for i, row in enumerate(rows[:20]):
        if len(row) >= 4 and row[:4] == ["Country Name", "Country Code", "Indicator Name", "Indicator Code"]:
            header_idx = i
            break
    if header_idx is None:
        return []

    header = rows[header_idx]
    year_indexes: list[tuple[int, int]] = []
    for idx, col in enumerate(header):
        col_s = str(col).strip()
        if YEAR_RE.match(col_s):
            year_indexes.append((idx, int(col_s)))

    target = country_code.upper()
    out: list[dict] = []
    for row in rows[header_idx + 1 :]:
        if len(row) < 4:
            continue
        if str(row[1]).strip().upper() != target:
            continue
        indicator_name = str(row[2]).strip()
        indicator_code = str(row[3]).strip()
        if not indicator_code:
            continue
        for idx, year in year_indexes:
            raw = row[idx] if idx < len(row) else ""
            value_text = str(raw).strip()
            if value_text == "":
                continue
            try:
                value = float(value_text)
            except ValueError:
                continue
            out.append(
                {
                    "country_code": target,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "year": year,
                    "value": value,
                    "source_file": path.name,
                }
            )
    return out


def reduce_latest_only(points: list[dict]) -> list[dict]:
    latest: dict[tuple[str, str], dict] = {}
    for point in points:
        key = (point["country_code"], point["indicator_code"])
        current = latest.get(key)
        if current is None or point["year"] > current["year"]:
            latest[key] = point
    return list(latest.values())


def upsert_points(points: list[dict]) -> tuple[int, int]:
    inserted = 0
    updated = 0
    with get_session() as session:
        for point in points:
            existing = session.scalar(
                select(CountryIndicatorModel).where(
                    CountryIndicatorModel.country_code == point["country_code"],
                    CountryIndicatorModel.indicator_code == point["indicator_code"],
                    CountryIndicatorModel.year == point["year"],
                )
            )
            if existing is None:
                session.add(
                    CountryIndicatorModel(
                        country_code=point["country_code"],
                        indicator_code=point["indicator_code"],
                        indicator_name=point["indicator_name"],
                        year=point["year"],
                        value=point["value"],
                        source_file=point["source_file"],
                        metadata_json=json.dumps({"importer": "wdi_csv"}, ensure_ascii=False),
                    )
                )
                inserted += 1
            else:
                existing.indicator_name = point["indicator_name"]
                existing.value = point["value"]
                existing.source_file = point["source_file"]
                existing.metadata_json = json.dumps({"importer": "wdi_csv"}, ensure_ascii=False)
                updated += 1
        session.commit()
    return inserted, updated


def main() -> None:
    args = parse_args()
    init_db()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir not found: {input_dir}")

    files = find_wdi_files(input_dir)
    all_points: list[dict] = []
    for path in files:
        all_points.extend(parse_wdi_file(path, args.country_code))

    points = reduce_latest_only(all_points) if args.latest_only else all_points
    inserted, updated = upsert_points(points)
    print(
        json.dumps(
            {
                "files": len(files),
                "parsed_points": len(all_points),
                "stored_points": len(points),
                "inserted": inserted,
                "updated": updated,
                "country_code": args.country_code.upper(),
                "latest_only": args.latest_only,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
