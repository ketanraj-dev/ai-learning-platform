"""
app/api/v1/ai.py
----------------
AI endpoints — chat (streaming), transcription, recommendations.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.deps import DB, CurrentUser
from app.repositories import analytics_repo
from app.schemas.analytics import ChatRequest, TranscribeResponse
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    current_user: CurrentUser,
    db: DB,
):
    """
    Stream an AI tutor response to a student question.

    Uses Server-Sent Events (SSE) — the frontend receives words
    one by one as they're generated, exactly like ChatGPT.

    FRONTEND USAGE:
        const response = await fetch('/api/v1/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message, history })
        });
        const reader = response.body.getReader();
        // Read chunks and append to message display

    history format: [{"role": "user"|"assistant", "content": "..."}]
    Max 10 history items (enforced by schema).
    """
    # Log AI chat activity (don't await — fire and forget for performance)
    history_dicts = [{"role": m.role, "content": m.content} for m in payload.history]

    async def stream_and_log():
        """Generator that streams AI response and logs activity after."""
        full_response = []
        async for chunk in ai_service.chat_with_ai(payload.message, history_dicts):
            full_response.append(chunk)
            yield chunk

        # Log after streaming completes
        await analytics_repo.log_activity(
            db=db,
            user_id=current_user.id,
            action_type="ai_chat",
            metadata={"message_length": len(payload.message)},
        )

    return StreamingResponse(
        stream_and_log(),
        media_type="text/plain",
        headers={
            # Allow frontend to read the streaming response
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    current_user: CurrentUser,
    db: DB,
    audio: UploadFile = File(..., description="Audio file from microphone (webm/wav/mp3)"),
):
    """
    Transcribe speech to text using OpenAI Whisper.

    Frontend records audio using MediaRecorder API and sends
    the resulting Blob as multipart/form-data.

    Supported formats: webm, wav, mp3, mp4, m4a
    Max recommended size: 25MB (Whisper API limit)
    """
    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio data received.",
        )

    # Get filename for format hint to Whisper
    filename = audio.filename or "audio.webm"
    text = await ai_service.transcribe_audio(audio_bytes, filename)

    # Log voice query activity
    await analytics_repo.log_activity(
        db=db,
        user_id=current_user.id,
        action_type="voice_query",
        metadata={"audio_size_bytes": len(audio_bytes)},
    )

    return TranscribeResponse(text=text)


@router.get("/recommend")
async def get_recommendations(current_user: CurrentUser, db: DB):
    """
    Get AI-generated personalised study recommendations.
    Based on the student's analytics — weak topics, accuracy trends.

    Returns a recommendation paragraph + list of topics to focus on.
    Calls GPT-4o-mini — response takes 2-4 seconds.
    """
    from app.services import analytics_service
    return await analytics_service.get_recommendations(db, current_user.id)