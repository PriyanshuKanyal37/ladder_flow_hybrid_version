"""LadderFlow unified backend entry point."""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.services.neo4j_service import close_driver, init_constraints

logger = logging.getLogger(__name__)
WORKER_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_worker.py")

_RESTART_DELAYS = [5, 15, 30]


async def _spawn_worker() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, WORKER_SCRIPT, "start"],
        env=os.environ.copy(),
        stdout=None,
        stderr=None,
    )


async def _monitor_and_restart(app: FastAPI) -> None:
    attempt = 0
    proc: subprocess.Popen = app.state.voice_worker_proc

    while True:
        await asyncio.sleep(5)
        ret = proc.poll()
        if ret is None:
            attempt = 0  # still alive — reset restart counter
            continue

        # Worker died
        app.state.voice_worker_alive = False
        if ret != 0:
            logger.error(f"LiveKit worker exited unexpectedly (code {ret})")
        else:
            logger.warning("LiveKit worker exited cleanly — restarting")

        if attempt >= len(_RESTART_DELAYS):
            logger.error("LiveKit worker failed 3 restart attempts. Giving up.")
            break

        delay = _RESTART_DELAYS[attempt]
        attempt += 1
        logger.info(f"Restarting LiveKit worker in {delay}s (attempt {attempt}/{len(_RESTART_DELAYS)})")
        await asyncio.sleep(delay)

        try:
            proc = await _spawn_worker()
            app.state.voice_worker_proc = proc
            app.state.voice_worker_alive = True
            logger.info(f"LiveKit worker restarted (PID {proc.pid})")
        except Exception as exc:
            logger.error(f"Failed to restart LiveKit worker: {exc}", exc_info=True)
            break


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.voice_worker_proc = None
    app.state.voice_worker_alive = False

    try:
        init_constraints()
        logger.info("Neo4j constraints initialized")
    except Exception as exc:
        logger.warning(f"Neo4j init skipped: {exc}")

    monitor_task = None

    try:
        logger.info(f"Starting LiveKit agent worker: {WORKER_SCRIPT}")
        proc = await _spawn_worker()
        app.state.voice_worker_proc = proc
        app.state.voice_worker_alive = True
        logger.info(f"LiveKit worker started (PID {proc.pid})")
        monitor_task = asyncio.create_task(_monitor_and_restart(app), name="worker-monitor")
    except Exception as exc:
        app.state.voice_worker_alive = False
        logger.error(f"Failed to start LiveKit worker: {exc}", exc_info=True)
        logger.warning("Server running WITHOUT voice agent. Check agent_worker.py.")

    yield

    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

    worker_proc = app.state.voice_worker_proc
    if worker_proc and worker_proc.poll() is None:
        logger.info(f"Stopping LiveKit worker (PID {worker_proc.pid})...")
        try:
            if sys.platform == "win32":
                worker_proc.terminate()
            else:
                worker_proc.send_signal(signal.SIGTERM)
            try:
                worker_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker_proc.kill()
                worker_proc.wait()
        except Exception as exc:
            logger.warning(f"Error stopping worker: {exc}")

    app.state.voice_worker_alive = False
    app.state.voice_worker_proc = None

    # Close shared Neo4j driver so connections shut down cleanly.
    try:
        close_driver()
    except Exception as exc:
        logger.warning(f"Neo4j driver close error during shutdown: {exc}")


_allowed_origins = [o.strip() for o in settings.FRONTEND_URL.split(",") if o.strip()]

app = FastAPI(title="LadderFlow Podcast API", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    log_payload = {
        "event": "REQUEST_VALIDATION_ERROR",
        "method": request.method,
        "path": request.url.path,
        "errors": jsonable_encoder(exc.errors()),
        "body": body.decode("utf-8", errors="replace"),
    }
    logger.warning(json.dumps(log_payload, ensure_ascii=False, default=str))
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all so internal errors never leak stack traces or library internals
    to the client. Logs full traceback server-side, returns generic 500.
    HTTPException is handled by FastAPI before reaching here, so explicit
    error responses (404, 400, 429, etc.) still pass through unchanged.
    """
    logger.exception(
        "Unhandled exception on %s %s", request.method, request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    proc = getattr(app.state, "voice_worker_proc", None)
    alive = bool(proc and proc.poll() is None and getattr(app.state, "voice_worker_alive", False))
    return {
        "status": "ok" if alive else "degraded",
        "voice_agent": "ladderflow-host",
        "voice_worker_alive": alive,
    }


@app.get("/ready")
def ready():
    proc = getattr(app.state, "voice_worker_proc", None)
    alive = bool(proc and proc.poll() is None and getattr(app.state, "voice_worker_alive", False))
    if not alive:
        return JSONResponse(status_code=503, content={"status": "not_ready", "voice_worker_alive": False})
    return {"status": "ready", "voice_worker_alive": True}


app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
