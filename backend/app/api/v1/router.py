from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.centres import router as centres_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.indicators import router as indicators_router
from app.api.v1.routers.recommendation import router as recommendation_router
from app.api.v1.routers.referral_workflow import router as referral_workflow_router
from app.api.v1.routers.references import router as references_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(health_router)
router.include_router(recommendation_router)
router.include_router(centres_router)
router.include_router(references_router)
router.include_router(indicators_router)
router.include_router(referral_workflow_router)
