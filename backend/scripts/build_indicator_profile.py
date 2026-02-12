from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CountryIndicatorModel, get_session, init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build simulation profile from country indicators")
    parser.add_argument("--country-code", type=str, default="KEN")
    parser.add_argument("--output", type=str, default="docs/indicator_profile.json")
    return parser.parse_args()


def _latest(country_code: str) -> dict[str, CountryIndicatorModel]:
    with get_session() as session:
        rows = session.scalars(
            select(CountryIndicatorModel).where(CountryIndicatorModel.country_code == country_code.upper())
        ).all()
    out: dict[str, CountryIndicatorModel] = {}
    for row in rows:
        cur = out.get(row.indicator_code)
        if cur is None or row.year > cur.year:
            out[row.indicator_code] = row
    return out


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def build_profile(indicators: dict[str, CountryIndicatorModel]) -> dict:
    beds_per_1000 = float(indicators.get("SH.MED.BEDS.ZS").value) if indicators.get("SH.MED.BEDS.ZS") else None
    physicians_per_1000 = (
        float(indicators.get("SH.MED.PHYS.ZS").value) if indicators.get("SH.MED.PHYS.ZS") else None
    )
    maternal_mortality = float(indicators.get("SH.STA.MMRT").value) if indicators.get("SH.STA.MMRT") else None
    child_u5_mortality = float(indicators.get("SH.DYN.MORT").value) if indicators.get("SH.DYN.MORT") else None

    beds_per_10000 = beds_per_1000 * 10.0 if beds_per_1000 is not None else None

    maternal_ratio = 0.35
    pediatric_ratio = 0.25
    if maternal_mortality is not None:
        maternal_ratio = _clamp(0.25 + (maternal_mortality / 1000.0), 0.2, 0.6)
    if child_u5_mortality is not None:
        pediatric_ratio = _clamp(0.2 + (child_u5_mortality / 200.0), 0.15, 0.55)
    general_ratio = _clamp(1.0 - maternal_ratio - pediatric_ratio, 0.05, 0.7)

    total_mix = maternal_ratio + pediatric_ratio + general_ratio
    maternal_ratio /= total_mix
    pediatric_ratio /= total_mix
    general_ratio /= total_mix

    severity_high = 0.12
    severity_medium = 0.33
    if maternal_mortality is not None and child_u5_mortality is not None:
        severity_high = _clamp(0.05 + (maternal_mortality / 2000.0) + (child_u5_mortality / 500.0), 0.08, 0.45)
    if physicians_per_1000 is not None:
        deficit = max(0.0, 1.0 - physicians_per_1000)
        severity_medium = _clamp(0.25 + 0.3 * deficit, 0.2, 0.6)
    severity_low = _clamp(1.0 - severity_medium - severity_high, 0.05, 0.75)
    total_sev = severity_low + severity_medium + severity_high
    severity_low /= total_sev
    severity_medium /= total_sev
    severity_high /= total_sev

    return {
        "beds_per_1000": beds_per_1000,
        "beds_per_10000": beds_per_10000,
        "physicians_per_1000": physicians_per_1000,
        "maternal_mortality_ratio": maternal_mortality,
        "under5_mortality_rate": child_u5_mortality,
        "recommended_case_mix": {
            "maternal_ratio": round(maternal_ratio, 4),
            "pediatric_ratio": round(pediatric_ratio, 4),
            "general_ratio": round(general_ratio, 4),
        },
        "recommended_severity_mix": {
            "severity_low_ratio": round(severity_low, 4),
            "severity_medium_ratio": round(severity_medium, 4),
            "severity_high_ratio": round(severity_high, 4),
        },
    }


def main() -> None:
    args = parse_args()
    init_db()
    indicators = _latest(args.country_code)
    profile = build_profile(indicators)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "country_code": args.country_code.upper(),
        "profile": profile,
        "cli_examples": {
            "calibrate_capacity": (
                f"python scripts/calibrate_capacity.py --beds-per-10000 {profile['beds_per_10000']:.3f} --availability-ratio 0.8"
                if profile["beds_per_10000"] is not None
                else "beds_per_10000 unavailable in indicators"
            ),
            "simulate_batch": (
                "python scripts/simulate_batch.py --case-mix-mode mixed --severity-mode mixed "
                f"--maternal-ratio {profile['recommended_case_mix']['maternal_ratio']} "
                f"--pediatric-ratio {profile['recommended_case_mix']['pediatric_ratio']} "
                f"--general-ratio {profile['recommended_case_mix']['general_ratio']} "
                f"--severity-low-ratio {profile['recommended_severity_mix']['severity_low_ratio']} "
                f"--severity-medium-ratio {profile['recommended_severity_mix']['severity_medium_ratio']} "
                f"--severity-high-ratio {profile['recommended_severity_mix']['severity_high_ratio']}"
            ),
        },
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
