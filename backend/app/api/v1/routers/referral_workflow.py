from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.auth import AuthUser, get_current_user, require_admin
from app.core.rate_limit import rate_limit
from app.db.models import CentreModel, ReferralRequestModel, get_session
from app.services.schemas import (
    ReferralAcceptRequest,
    ReferralCompleteRequest,
    ReferralRequestCreate,
    ReferralRequestResponse,
    ReferralTransitionRequest,
)

router = APIRouter(tags=["referral-workflow"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_response(row: ReferralRequestModel) -> ReferralRequestResponse:
    return ReferralRequestResponse(
        id=row.id,
        patient_id=row.patient_id,
        source_id=row.source_id,
        needed_speciality=row.needed_speciality,
        severity=row.severity,
        proposed_dest_id=row.proposed_dest_id,
        accepted_dest_id=row.accepted_dest_id,
        status=row.status,
        notes=row.notes,
        feedback_diagnosis=row.feedback_diagnosis,
        feedback_treatment=row.feedback_treatment,
        feedback_followup=row.feedback_followup,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
        closed_at=row.closed_at,
    )


@router.get("/referrals/requests", response_model=list[ReferralRequestResponse])
def list_referral_requests(
    status_filter: str | None = None,
    source_id: str | None = None,
    _: AuthUser = Depends(get_current_user),
) -> list[ReferralRequestResponse]:
    with get_session() as session:
        query = select(ReferralRequestModel).order_by(ReferralRequestModel.id.desc())
        if status_filter:
            query = query.where(ReferralRequestModel.status == status_filter)
        if source_id:
            query = query.where(ReferralRequestModel.source_id == source_id)
        rows = session.scalars(query).all()
    return [_to_response(row) for row in rows]


@router.post("/referrals/requests", response_model=ReferralRequestResponse, status_code=status.HTTP_201_CREATED)
def create_referral_request(
    payload: ReferralRequestCreate,
    user: AuthUser = Depends(get_current_user),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferralRequestResponse:
    with get_session() as session:
        src = session.get(CentreModel, payload.source_id)
        if not src:
            raise HTTPException(status_code=400, detail="source_id does not exist")

        if payload.proposed_dest_id:
            dst = session.get(CentreModel, payload.proposed_dest_id)
            if not dst:
                raise HTTPException(status_code=400, detail="proposed_dest_id does not exist")
            if payload.proposed_dest_id == payload.source_id:
                raise HTTPException(status_code=400, detail="proposed_dest_id must differ from source_id")

        row = ReferralRequestModel(
            patient_id=payload.patient_id,
            source_id=payload.source_id,
            needed_speciality=payload.needed_speciality,
            severity=payload.severity,
            proposed_dest_id=payload.proposed_dest_id,
            status="pending",
            notes=payload.notes,
            created_by=user.username,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_response(row)


@router.post("/referrals/requests/{request_id}/accept", response_model=ReferralRequestResponse)
def accept_referral_request(
    request_id: int,
    payload: ReferralAcceptRequest,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferralRequestResponse:
    with get_session() as session:
        row = session.get(ReferralRequestModel, request_id)
        if not row:
            raise HTTPException(status_code=404, detail="Referral request not found")
        if row.status != "pending":
            raise HTTPException(status_code=409, detail=f"Cannot accept referral in status '{row.status}'")

        dst = session.get(CentreModel, payload.accepted_dest_id)
        if not dst:
            raise HTTPException(status_code=400, detail="accepted_dest_id does not exist")
        if payload.accepted_dest_id == row.source_id:
            raise HTTPException(status_code=400, detail="accepted_dest_id must differ from source_id")

        row.accepted_dest_id = payload.accepted_dest_id
        row.status = "accepted"
        row.notes = payload.notes or row.notes
        row.updated_at = _utc_now()
        session.commit()
        session.refresh(row)
        return _to_response(row)


@router.post("/referrals/requests/{request_id}/start-transfer", response_model=ReferralRequestResponse)
def start_transfer(
    request_id: int,
    payload: ReferralTransitionRequest,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferralRequestResponse:
    with get_session() as session:
        row = session.get(ReferralRequestModel, request_id)
        if not row:
            raise HTTPException(status_code=404, detail="Referral request not found")
        if row.status != "accepted":
            raise HTTPException(status_code=409, detail=f"Cannot start transfer in status '{row.status}'")

        row.status = "in_transit"
        row.notes = payload.notes or row.notes
        row.updated_at = _utc_now()
        session.commit()
        session.refresh(row)
        return _to_response(row)


@router.post("/referrals/requests/{request_id}/complete", response_model=ReferralRequestResponse)
def complete_referral(
    request_id: int,
    payload: ReferralCompleteRequest,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferralRequestResponse:
    with get_session() as session:
        row = session.get(ReferralRequestModel, request_id)
        if not row:
            raise HTTPException(status_code=404, detail="Referral request not found")
        if row.status != "in_transit":
            raise HTTPException(status_code=409, detail=f"Cannot complete referral in status '{row.status}'")

        row.status = "completed"
        row.feedback_diagnosis = payload.diagnosis
        row.feedback_treatment = payload.treatment
        row.feedback_followup = payload.followup
        row.notes = payload.notes or row.notes
        row.closed_at = _utc_now()
        row.updated_at = _utc_now()
        session.commit()
        session.refresh(row)
        return _to_response(row)


@router.post("/referrals/requests/{request_id}/reject", response_model=ReferralRequestResponse)
def reject_referral(
    request_id: int,
    payload: ReferralTransitionRequest,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferralRequestResponse:
    with get_session() as session:
        row = session.get(ReferralRequestModel, request_id)
        if not row:
            raise HTTPException(status_code=404, detail="Referral request not found")
        if row.status not in {"pending", "accepted"}:
            raise HTTPException(status_code=409, detail=f"Cannot reject referral in status '{row.status}'")

        row.status = "rejected"
        row.notes = payload.notes or row.notes
        row.closed_at = _utc_now()
        row.updated_at = _utc_now()
        session.commit()
        session.refresh(row)
        return _to_response(row)


@router.post("/referrals/requests/{request_id}/cancel", response_model=ReferralRequestResponse)
def cancel_referral(
    request_id: int,
    payload: ReferralTransitionRequest,
    _: AuthUser = Depends(require_admin),
    __: None = Depends(rate_limit("admin_write", limit=60, window_seconds=60)),
) -> ReferralRequestResponse:
    with get_session() as session:
        row = session.get(ReferralRequestModel, request_id)
        if not row:
            raise HTTPException(status_code=404, detail="Referral request not found")
        if row.status in {"completed", "rejected", "cancelled"}:
            raise HTTPException(status_code=409, detail=f"Cannot cancel referral in status '{row.status}'")

        row.status = "cancelled"
        row.notes = payload.notes or row.notes
        row.closed_at = _utc_now()
        row.updated_at = _utc_now()
        session.commit()
        session.refresh(row)
        return _to_response(row)
