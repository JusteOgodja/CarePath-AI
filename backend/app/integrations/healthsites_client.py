from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class HealthsitesQuery:
    api_key: str
    page: int
    country: str | None = None
    extent: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    flat_properties: bool = True
    tag_format: str = "osm"
    output: str = "json"


class HealthsitesClient:
    def __init__(self, *, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_page(self, query: HealthsitesQuery) -> dict[str, Any]:
        params: dict[str, Any] = {
            "api-key": query.api_key,
            "page": query.page,
            "flat-properties": str(query.flat_properties).lower(),
            "tag-format": query.tag_format,
            "output": query.output,
        }
        if query.country:
            params["country"] = query.country
        if query.extent:
            params["extent"] = query.extent
        if query.date_from:
            params["from"] = query.date_from
        if query.date_to:
            params["to"] = query.date_to

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/api/v3/facilities/", params=params)
            response.raise_for_status()
            return response.json()

    def iter_facilities(
        self,
        *,
        api_key: str,
        country: str | None,
        extent: str | None,
        date_from: str | None,
        date_to: str | None,
        flat_properties: bool,
        tag_format: str,
        output: str,
        max_pages: int | None = None,
    ):
        page = 1
        while True:
            if max_pages is not None and page > max_pages:
                break

            payload = self.fetch_page(
                HealthsitesQuery(
                    api_key=api_key,
                    page=page,
                    country=country,
                    extent=extent,
                    date_from=date_from,
                    date_to=date_to,
                    flat_properties=flat_properties,
                    tag_format=tag_format,
                    output=output,
                )
            )
            items = _extract_results(payload)
            if not items:
                break

            for item in items:
                yield item

            if payload.get("next") in (None, "", False):
                break
            page += 1


def _extract_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("results"), list):
        return payload["results"]
    if isinstance(payload.get("features"), list):
        return payload["features"]
    return []
