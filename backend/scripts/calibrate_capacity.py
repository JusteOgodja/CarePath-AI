from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, get_session, init_db
from app.integrations.who_gho_client import WhoGhoClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate capacities from beds per 10,000 population")
    parser.add_argument("--beds-per-10000", type=float, default=None)
    parser.add_argument("--who-indicator", type=str, default=None, help="WHO GHO indicator code (e.g. HWF_0000)")
    parser.add_argument("--who-country", type=str, default=None, help="ISO-2 country code (e.g. CM)")
    parser.add_argument("--who-year", type=int, default=None, help="Optional exact year")
    parser.add_argument(
        "--who-base-url",
        type=str,
        default=os.getenv("WHO_GHO_BASE_URL", "https://ghoapi.azureedge.net"),
    )
    parser.add_argument("--availability-ratio", type=float, default=0.8)
    return parser.parse_args()


def calibrated_capacity(population: int, beds_per_10000: float) -> int:
    raw = beds_per_10000 * population / 10000.0
    return max(1, int(round(raw)))


def resolve_beds_per_10000(args: argparse.Namespace) -> tuple[float, dict]:
    if args.beds_per_10000 is not None:
        value = float(args.beds_per_10000)
        if value <= 0:
            raise ValueError("beds-per-10000 must be > 0")
        return value, {"source": "manual"}

    if not args.who_indicator or not args.who_country:
        raise ValueError("Provide --beds-per-10000 or (--who-indicator and --who-country)")

    client = WhoGhoClient(base_url=args.who_base_url)
    try:
        point = client.select_country_value(
            indicator=args.who_indicator,
            country=args.who_country,
            year=args.who_year,
        )
    except Exception as exc:
        raise ValueError(
            f"Unable to fetch WHO GHO value: {exc}. "
            "Use --beds-per-10000 manual fallback if WHO API is unavailable."
        ) from exc
    if point.numeric_value <= 0:
        raise ValueError("WHO numeric value must be > 0")

    return point.numeric_value, {
        "source": "who_gho",
        "indicator": args.who_indicator,
        "country": point.country,
        "year": point.year,
        "base_url": args.who_base_url,
    }


def main() -> None:
    args = parse_args()
    if not (0 < args.availability_ratio <= 1):
        raise ValueError("availability-ratio must be in (0,1]")
    beds_per_10000, source_info = resolve_beds_per_10000(args)

    init_db()

    updated = 0
    with get_session() as session:
        centres = session.scalars(select(CentreModel)).all()
        for centre in centres:
            population = int(centre.catchment_population or 0)
            centre.capacity_max = calibrated_capacity(population, beds_per_10000)
            centre.capacity_available = max(0, int(math.floor(centre.capacity_max * args.availability_ratio)))
            updated += 1

        session.commit()

    print(
        {
            "updated": updated,
            "beds_per_10000": beds_per_10000,
            "availability_ratio": args.availability_ratio,
            "source_info": source_info,
        }
    )


if __name__ == "__main__":
    main()
