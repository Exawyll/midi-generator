"""
main.py — FastAPI application entry point.

Start with:
    cd backend && uvicorn main:app --reload
"""

import base64
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import GenerateRequest, GenerateResponse
from claude_service import generate_arrangement
from midi_engine import arrangement_to_midi
from auth import verify_password, create_token, verify_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MIDI Generator API",
    description="AI-powered MIDI arrangement generator using Claude",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@app.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    """
    Exchange the shared APP_PASSWORD for a signed JWT (valid 24 h).
    Public endpoint — no token required.
    """
    if not verify_password(body.password):
        logger.warning("Failed login attempt")
        raise HTTPException(status_code=401, detail="Invalid password")
    logger.info("Successful login — token issued")
    return LoginResponse(token=create_token())


# ── Public ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ── Protected ─────────────────────────────────────────────────────────────────

@app.post(
    "/api/generate",
    response_model=GenerateResponse,
    dependencies=[Depends(verify_token)],  # 401 if no valid Bearer token
)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Generate a MIDI arrangement from a text description.
    Requires a valid Bearer token from /auth/login.
    """
    logger.info(
        f"POST /api/generate — style={request.style}, bpm={request.bpm}, "
        f'description="{request.description[:60]}..."'
    )

    try:
        arrangement = generate_arrangement(request)
    except ValueError as e:
        logger.error(f"Claude service error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in claude_service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")

    try:
        midi_bytes = arrangement_to_midi(arrangement)
    except ValueError as e:
        logger.error(f"MIDI engine error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in midi_engine: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MIDI generation failed: {e}")

    midi_b64 = base64.b64encode(midi_bytes).decode("utf-8")
    return GenerateResponse(arrangement=arrangement, midi_b64=midi_b64)
