import time
import asyncio
import uuid
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from real_estate_backend.core.logging import logger

router = APIRouter(prefix="/ai", tags=["AI"])


# ── Job store — in memory ──────────────────────────────────────
# Tracks background job status
# In production this would be Redis or DB
jobs: dict[str, dict] = {}


# ── PHASE 1 — The broken endpoint ─────────────────────────────
@router.get("/analyze/slow")
def analyze_slow():
    """
    Simulates a slow AI model call.
    Takes 130 seconds → times out through Cloudflare tunnel.
    This is the BROKEN version — do not use in production.
    """
    logger.info("Slow AI endpoint called — will timeout")

    # Fake slow AI model
    time.sleep(130)

    return {
        "result": "AI analysis complete"
    }
    
    
@router.post("/analyze/stream")
async def analyze_stream():
    async def generate_chunks():
        logger.info("Streaming AI response started")

        ai_chunks = [
            "Analyzing property data...",
            "Processing lead history...",
            "Running sentiment analysis on notes...",
            "Calculating conversion probability...",
            "Generating recommendations...",
            "Cross-referencing market data...",
            "Finalizing report...",
            '{"result":"complete","score":0.87,"recommendation":"High priority lead"}',
        ]

        # Send immediately so the stream opens without waiting.
        yield "event: connected\ndata: stream started\n\n"

        for index, chunk in enumerate(ai_chunks, start=1):
            await asyncio.sleep(15)

            logger.info(
                "Streaming AI chunk",
                extra={
                    "chunk_number": index,
                    "total_chunks": len(ai_chunks),
                },
            )

            yield f"event: progress\ndata: {chunk}\n\n"

        yield "event: complete\ndata: analysis completed\n\n"

        logger.info("Streaming AI response completed")

    return StreamingResponse(
        generate_chunks(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )