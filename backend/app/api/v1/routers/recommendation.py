from fastapi import APIRouter, HTTPException

from app.services.recommender import Recommender
from app.services.schemas import RecommandationRequest, RecommandationResponse

router = APIRouter(tags=["recommendation"])
_recommender: Recommender | None = None


def get_recommender() -> Recommender:
    global _recommender
    if _recommender is None:
        _recommender = Recommender()
    return _recommender


@router.post("/recommander", response_model=RecommandationResponse)
def recommander(payload: RecommandationRequest) -> RecommandationResponse:
    try:
        return get_recommender().recommend(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
