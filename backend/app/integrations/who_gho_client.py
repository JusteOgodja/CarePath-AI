from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class GhoPoint:
    country: str
    year: int
    numeric_value: float


class WhoGhoClient:
    def __init__(self, base_url: str = "https://ghoapi.azureedge.net") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_indicator_data(self, indicator: str, timeout: float = 20.0) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/IndicatorData"
        errors: list[str] = []
        payload: dict[str, Any] | None = None
        query_variants = [
            {"Indicator": indicator},
            {"$filter": f"Indicator eq '{indicator}'"},
        ]
        for params in query_variants:
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    break
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else "unknown"
                errors.append(f"params={params} -> HTTP {status}")
            except httpx.HTTPError as exc:
                errors.append(f"params={params} -> {exc}")

        if payload is None:
            raise RuntimeError(
                f"WHO GHO API unavailable for indicator '{indicator}'. Attempts: {'; '.join(errors)}"
            )

        items = payload.get("value", [])
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    def select_country_value(
        self,
        *,
        indicator: str,
        country: str,
        year: int | None = None,
    ) -> GhoPoint:
        requested_country = country.strip().upper()
        rows = self.fetch_indicator_data(indicator)

        points: list[GhoPoint] = []
        for row in rows:
            spatial = str(row.get("SpatialDim") or "").strip().upper()
            if spatial != requested_country:
                continue

            raw_value = row.get("NumericValue")
            if raw_value in (None, ""):
                continue
            try:
                numeric_value = float(raw_value)
            except (TypeError, ValueError):
                continue

            raw_year = row.get("TimeDim")
            try:
                point_year = int(raw_year)
            except (TypeError, ValueError):
                continue

            points.append(
                GhoPoint(
                    country=requested_country,
                    year=point_year,
                    numeric_value=numeric_value,
                )
            )

        if not points:
            raise ValueError(
                f"No WHO GHO data found for indicator='{indicator}' and country='{requested_country}'"
            )

        if year is not None:
            exact = [point for point in points if point.year == year]
            if not exact:
                raise ValueError(
                    f"No WHO GHO data found for indicator='{indicator}', country='{requested_country}', year={year}"
                )
            return sorted(exact, key=lambda x: x.year)[-1]

        return sorted(points, key=lambda x: x.year)[-1]
