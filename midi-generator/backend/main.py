"""
main.py — FastAPI application entry point.

Start with:
    cd backend && uvicorn main:app --reload
"""

import base64
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import GenerateRequest, GenerateResponse
from claude_service import generate_arrangement
from midi_engine import arrangement_to_midi

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

# Allow the Vite dev server (and any localhost port) to call the API
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


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Generate a MIDI arrangement from a text description.

    Returns:
        arrangement — the structured JSON arrangement (phases, tracks, notes)
        midi_b64    — the .mid file encoded as base64 (decode client-side to download)
    """
    logger.info(
        f"POST /api/generate — style={request.style}, bpm={request.bpm}, "
        f'description="{request.description[:60]}..."'
    )

    # 1. Ask Claude to compose the arrangement
    try:
        arrangement = generate_arrangement(request)
    except ValueError as e:
        logger.error(f"Claude service error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in claude_service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")

    # 2. Convert arrangement JSON → .mid bytes
    try:
        midi_bytes = arrangement_to_midi(arrangement)
    except ValueError as e:
        logger.error(f"MIDI engine error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in midi_engine: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MIDI generation failed: {e}")

    # 3. Base64-encode the MIDI file for JSON transport
    midi_b64 = base64.b64encode(midi_bytes).decode("utf-8")

    return GenerateResponse(arrangement=arrangement, midi_b64=midi_b64)
