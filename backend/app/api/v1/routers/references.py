from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.auth import AuthUser, require_admin
from app.core.rate_limit import rate_limit
from app.db.models import CentreModel, ReferenceModel, get_session
from app.services.schemas import ReferenceCreate, ReferenceResponse, ReferenceUpdate

router = APIRouter(tags=["references"])


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
def create_reference(
    payload: ReferenceCreate,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferenceResponse:
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
def update_reference(
    reference_id: int,
    payload: ReferenceUpdate,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferenceResponse:
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
def delete_reference(
    reference_id: int,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> None:
    with get_session() as session:
        ref = session.get(ReferenceModel, reference_id)
        if not ref:
            raise HTTPException(status_code=404, detail=f"Reference '{reference_id}' not found")

        session.delete(ref)
        session.commit()
