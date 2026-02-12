from fastapi import FastAPI

from app.api.routes import router
from app.db.models import init_db


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(
        title="CarePath AI",
        description="MVP for patient referral path recommendation",
        version="0.1.0",
    )
    app.include_router(router)
    return app


app = create_app()
