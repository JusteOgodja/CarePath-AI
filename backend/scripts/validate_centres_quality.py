from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, get_session, init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate centres data quality")
    parser.add_argument("--output", type=str, default="docs/centres_quality_report.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_db()

    with get_session() as session:
        centres = session.scalars(select(CentreModel)).all()

    level_counts = Counter((c.level or "").strip().lower() for c in centres)
    speciality_counts: Counter[str] = Counter()
    for c in centres:
        speciality_counts.update([s.strip() for s in c.specialities.split(",") if s.strip()])

    missing_coords = [c.id for c in centres if c.lat is None or c.lon is None]
    missing_osm_identity = [c.id for c in centres if not c.osm_type or not c.osm_id]

    suspicious = {
        "dispensary_not_primary": [],
        "referral_not_tertiary": [],
        "hospital_primary": [],
    }
    for c in centres:
        name_l = (c.name or "").lower()
        lvl = (c.level or "").lower()
        if "dispensary" in name_l and lvl != "primary":
            suspicious["dispensary_not_primary"].append(c.id)
        if "referral" in name_l and lvl != "tertiary":
            suspicious["referral_not_tertiary"].append(c.id)
        if "hospital" in name_l and lvl == "primary":
            suspicious["hospital_primary"].append(c.id)

    payload = {
        "centres_total": len(centres),
        "level_counts": dict(level_counts),
        "speciality_counts": dict(speciality_counts),
        "missing_coords_count": len(missing_coords),
        "missing_osm_identity_count": len(missing_osm_identity),
        "suspicious_mapping_counts": {k: len(v) for k, v in suspicious.items()},
        "samples": {
            "missing_coords": missing_coords[:20],
            "missing_osm_identity": missing_osm_identity[:20],
            "dispensary_not_primary": suspicious["dispensary_not_primary"][:20],
            "referral_not_tertiary": suspicious["referral_not_tertiary"][:20],
            "hospital_primary": suspicious["hospital_primary"][:20],
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
