from __future__ import annotations

import os
from fastapi import FastAPI

from ..routes.health import router as health_router
from ..routes.asr_file import router as asr_file_router
from ..routes.asr_pcm import router as asr_pcm_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="sentinel-whisper-server",
        version=os.getenv("APP_VERSION", "0.1.0"),
    )

    app.include_router(health_router)
    app.include_router(asr_file_router)
    app.include_router(asr_pcm_router)

    return app
