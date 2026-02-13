from fastapi import APIRouter
from sqlalchemy import select

from app.db.models import CountryIndicatorModel, get_session
from app.services.schemas import IndicatorResponse

router = APIRouter(tags=["indicators"])


@router.get("/indicators", response_model=list[IndicatorResponse])
def list_indicators(country_code: str | None = None, indicator_code: str | None = None) -> list[IndicatorResponse]:
    with get_session() as session:
        query = select(CountryIndicatorModel)
        if country_code:
            query = query.where(CountryIndicatorModel.country_code == country_code.upper())
        if indicator_code:
            query = query.where(CountryIndicatorModel.indicator_code == indicator_code)
        rows = session.scalars(
            query.order_by(
                CountryIndicatorModel.country_code,
                CountryIndicatorModel.indicator_code,
                CountryIndicatorModel.year,
            )
        ).all()

    return [
        IndicatorResponse(
            country_code=row.country_code,
            indicator_code=row.indicator_code,
            indicator_name=row.indicator_name,
            year=row.year,
            value=row.value,
            source_file=row.source_file,
        )
        for row in rows
    ]


@router.get("/indicators/latest", response_model=list[IndicatorResponse])
def list_latest_indicators(country_code: str = "KEN") -> list[IndicatorResponse]:
    country = country_code.upper()
    with get_session() as session:
        rows = session.scalars(
            select(CountryIndicatorModel).where(CountryIndicatorModel.country_code == country)
        ).all()

    latest_by_indicator: dict[str, CountryIndicatorModel] = {}
    for row in rows:
        current = latest_by_indicator.get(row.indicator_code)
        if current is None or row.year > current.year:
            latest_by_indicator[row.indicator_code] = row

    latest_rows = sorted(latest_by_indicator.values(), key=lambda x: x.indicator_code)
    return [
        IndicatorResponse(
            country_code=row.country_code,
            indicator_code=row.indicator_code,
            indicator_name=row.indicator_name,
            year=row.year,
            value=row.value,
            source_file=row.source_file,
        )
        for row in latest_rows
    ]
