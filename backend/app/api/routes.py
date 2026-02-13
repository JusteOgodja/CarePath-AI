from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select

from app.db.models import CountryIndicatorModel, CentreModel, ReferenceModel, get_session
from app.services.recommender import Recommender
from app.services.schemas import (
    CentreCreate,
    CentreResponse,
    CentreUpdate,
    IndicatorResponse,
    RecommandationRequest,
    RecommandationResponse,
    ReferenceCreate,
    ReferenceResponse,
    ReferenceUpdate,
)

router = APIRouter()
_recommender: Recommender | None = None


def get_recommender() -> Recommender:
    global _recommender
    if _recommender is None:
        _recommender = Recommender()
    return _recommender


def _split_specialities(specialities: str) -> list[str]:
    return [item.strip() for item in specialities.split(",") if item.strip()]


def _join_specialities(specialities: list[str]) -> str:
    cleaned = [item.strip() for item in specialities if item.strip()]
    if not cleaned:
        raise ValueError("specialities cannot be empty")
    return ",".join(cleaned)


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/recommander", response_model=RecommandationResponse)
def recommander(payload: RecommandationRequest) -> RecommandationResponse:
    try:
        return get_recommender().recommend(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/centres", response_model=list[CentreResponse])
def list_centres() -> list[CentreResponse]:
    with get_session() as session:
        rows = session.scalars(select(CentreModel).order_by(CentreModel.id)).all()

    return [
        CentreResponse(
            id=row.id,
            name=row.name,
            level=row.level,
            specialities=_split_specialities(row.specialities),
            capacity_max=row.capacity_max,
            capacity_available=row.capacity_available,
            estimated_wait_minutes=row.estimated_wait_minutes,
            lat=row.lat,
            lon=row.lon,
            catchment_population=int(row.catchment_population or 0),
        )
        for row in rows
    ]


@router.post("/centres", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
def create_centre(payload: CentreCreate) -> CentreResponse:
    try:
        specialities = _join_specialities(payload.specialities)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with get_session() as session:
        existing = session.get(CentreModel, payload.id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Centre '{payload.id}' already exists")

        centre = CentreModel(
            id=payload.id,
            name=payload.name,
            level=payload.level,
            specialities=specialities,
            capacity_max=payload.capacity_max,
            capacity_available=payload.capacity_available,
            estimated_wait_minutes=payload.estimated_wait_minutes,
            lat=payload.lat,
            lon=payload.lon,
            catchment_population=payload.catchment_population,
        )
        session.add(centre)
        session.commit()

    return CentreResponse(
        id=payload.id,
        name=payload.name,
        level=payload.level,
        specialities=_split_specialities(specialities),
        capacity_max=payload.capacity_max,
        capacity_available=payload.capacity_available,
        estimated_wait_minutes=payload.estimated_wait_minutes,
        lat=payload.lat,
        lon=payload.lon,
        catchment_population=payload.catchment_population,
    )


@router.put("/centres/{centre_id}", response_model=CentreResponse)
def update_centre(centre_id: str, payload: CentreUpdate) -> CentreResponse:
    try:
        specialities = _join_specialities(payload.specialities)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with get_session() as session:
        centre = session.get(CentreModel, centre_id)
        if not centre:
            raise HTTPException(status_code=404, detail=f"Centre '{centre_id}' not found")

        centre.name = payload.name
        centre.level = payload.level
        centre.specialities = specialities
        centre.capacity_max = payload.capacity_max
        centre.capacity_available = payload.capacity_available
        centre.estimated_wait_minutes = payload.estimated_wait_minutes
        centre.lat = payload.lat
        centre.lon = payload.lon
        centre.catchment_population = payload.catchment_population
        session.commit()

        return CentreResponse(
            id=centre.id,
            name=centre.name,
            level=centre.level,
            specialities=_split_specialities(centre.specialities),
            capacity_max=centre.capacity_max,
            capacity_available=centre.capacity_available,
            estimated_wait_minutes=centre.estimated_wait_minutes,
            lat=centre.lat,
            lon=centre.lon,
            catchment_population=int(centre.catchment_population or 0),
        )


@router.delete("/centres/{centre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_centre(centre_id: str) -> None:
    with get_session() as session:
        centre = session.get(CentreModel, centre_id)
        if not centre:
            raise HTTPException(status_code=404, detail=f"Centre '{centre_id}' not found")

        refs_count = len(
            session.scalars(
                select(ReferenceModel).where(
                    or_(ReferenceModel.source_id == centre_id, ReferenceModel.dest_id == centre_id)
                )
            ).all()
        )
        if refs_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Centre '{centre_id}' is referenced by {refs_count} links. Delete links first.",
            )

        session.delete(centre)
        session.commit()


@router.get("/references", response_model=list[ReferenceResponse])
def list_references() -> list[ReferenceResponse]:
    with get_session() as session:
        rows = session.scalars(select(ReferenceModel).order_by(ReferenceModel.id)).all()

    return [
        ReferenceResponse(
            id=row.id,
            source_id=row.source_id,
            dest_id=row.dest_id,
            travel_minutes=row.travel_minutes,
        )
        for row in rows
    ]


@router.post("/references", response_model=ReferenceResponse, status_code=status.HTTP_201_CREATED)
def create_reference(payload: ReferenceCreate) -> ReferenceResponse:
    if payload.source_id == payload.dest_id:
        raise HTTPException(status_code=400, detail="source_id and dest_id must be different")

    with get_session() as session:
        src = session.get(CentreModel, payload.source_id)
        dst = session.get(CentreModel, payload.dest_id)
        if not src or not dst:
            raise HTTPException(status_code=400, detail="source_id or dest_id does not exist")

        ref = ReferenceModel(
            source_id=payload.source_id,
            dest_id=payload.dest_id,
            travel_minutes=payload.travel_minutes,
        )
        session.add(ref)
        session.commit()
        session.refresh(ref)

        return ReferenceResponse(
            id=ref.id,
            source_id=ref.source_id,
            dest_id=ref.dest_id,
            travel_minutes=ref.travel_minutes,
        )


@router.put("/references/{reference_id}", response_model=ReferenceResponse)
def update_reference(reference_id: int, payload: ReferenceUpdate) -> ReferenceResponse:
    if payload.source_id == payload.dest_id:
        raise HTTPException(status_code=400, detail="source_id and dest_id must be different")

    with get_session() as session:
        ref = session.get(ReferenceModel, reference_id)
        if not ref:
            raise HTTPException(status_code=404, detail=f"Reference '{reference_id}' not found")

        src = session.get(CentreModel, payload.source_id)
        dst = session.get(CentreModel, payload.dest_id)
        if not src or not dst:
            raise HTTPException(status_code=400, detail="source_id or dest_id does not exist")

        ref.source_id = payload.source_id
        ref.dest_id = payload.dest_id
        ref.travel_minutes = payload.travel_minutes
        session.commit()

        return ReferenceResponse(
            id=ref.id,
            source_id=ref.source_id,
            dest_id=ref.dest_id,
            travel_minutes=ref.travel_minutes,
        )


@router.delete("/references/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reference(reference_id: int) -> None:
    with get_session() as session:
        ref = session.get(ReferenceModel, reference_id)
        if not ref:
            raise HTTPException(status_code=404, detail=f"Reference '{reference_id}' not found")

        session.delete(ref)
        session.commit()


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
