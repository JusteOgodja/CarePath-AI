from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select

from app.core.auth import AuthUser, require_admin
from app.core.rate_limit import rate_limit
from app.db.models import CentreModel, ReferenceModel, get_session
from app.services.schemas import CentreCreate, CentreResponse, CentreUpdate

router = APIRouter(tags=["centres"])


def _split_specialities(specialities: str) -> list[str]:
    return [item.strip() for item in specialities.split(",") if item.strip()]


def _join_specialities(specialities: list[str]) -> str:
    cleaned = [item.strip() for item in specialities if item.strip()]
    if not cleaned:
        raise ValueError("specialities cannot be empty")
    return ",".join(cleaned)


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
def create_centre(
    payload: CentreCreate,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> CentreResponse:
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
def update_centre(
    centre_id: str,
    payload: CentreUpdate,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> CentreResponse:
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
def delete_centre(
    centre_id: str,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> None:
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
