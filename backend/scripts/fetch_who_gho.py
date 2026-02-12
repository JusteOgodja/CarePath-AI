from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.integrations.who_gho_client import WhoGhoClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch WHO GHO indicator value for a country/year")
    parser.add_argument("--indicator", required=True, type=str, help="WHO indicator code, e.g. HWF_0000")
    parser.add_argument("--country", required=True, type=str, help="ISO-2 country code, e.g. CM")
    parser.add_argument("--year", type=int, default=None, help="Optional exact year")
    parser.add_argument("--base-url", type=str, default="https://ghoapi.azureedge.net")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = WhoGhoClient(base_url=args.base_url)
    try:
        point = client.select_country_value(
            indicator=args.indicator,
            country=args.country,
            year=args.year,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": "Retry later or pass --beds-per-10000 directly to calibrate_capacity.py while WHO API is unavailable.",
                },
                indent=2,
            )
        )
        raise SystemExit(2) from exc
    print(
        json.dumps(
            {
                "indicator": args.indicator,
                "country": point.country,
                "year": point.year,
                "numeric_value": point.numeric_value,
                "base_url": args.base_url,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
