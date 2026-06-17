"""
app/services/ai_service.py
---------------------------
All OpenAI API integrations:
  - GPT-4o-mini: AI tutor chat with streaming
  - Whisper:     speech-to-text transcription
  - GPT-4o-mini: analytics-based recommendations

COST CONTROLS:
  - Model: gpt-4o-mini (~10x cheaper than gpt-4o)
  - History: max 10 messages (5 exchanges) in context
  - Max tokens: 1024 per response
  - System prompt: scoped to DS/AI-ML only (prevents off-topic usage)
"""

import io
from typing import AsyncGenerator, Optional

from fastapi import HTTPException, status
from openai import AsyncOpenAI, OpenAIError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.analytics import TopicStat

logger = get_logger(__name__)
settings = get_settings()

# Single AsyncOpenAI client — reused across all requests
# AsyncOpenAI uses connection pooling internally
_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """
    Return a cached AsyncOpenAI client.
    Created once on first call, reused thereafter.
    """
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured.",
            )
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


# ── System prompt ──────────────────────────────────────────────────────────

TUTOR_SYSTEM_PROMPT = """You are AICA (AI Course Assistant), an expert AI tutor 
specialising in Data Science and AI/ML topics. You help students understand:
- Python for Data Science (NumPy, Pandas, Matplotlib)
- Machine Learning (supervised, unsupervised, reinforcement learning)
- Deep Learning and Neural Networks
- Natural Language Processing
- Data preprocessing and feature engineering
- Model evaluation and metrics
- Statistics and probability for ML

Guidelines:
- Give clear, concise explanations with examples
- Use simple analogies for complex concepts
- Provide Python code snippets when helpful
- If asked about unrelated topics, politely redirect to DS/AI-ML
- Keep responses focused and educational
- Encourage the student when they make progress"""


# ── Chat ───────────────────────────────────────────────────────────────────

async def chat_with_ai(
    message: str,
    history: list[dict],
) -> AsyncGenerator[str, None]:
    """
    Stream a GPT-4o-mini response to a student's question.

    Uses Server-Sent Events (SSE) streaming — words appear one by one
    in the frontend as they're generated, like ChatGPT.

    Args:
        message: the student's current question
        history: list of {"role": "user"|"assistant", "content": "..."}
                 max 10 items enforced by schema

    Yields:
        String chunks of the response as they stream in.
        Router wraps these in StreamingResponse.

    Raises:
        HTTPException 503: OpenAI API error
    """
    client = get_openai_client()

    # Build message list: system prompt + history + new message
    messages = [{"role": "system", "content": TUTOR_SYSTEM_PROMPT}]

    # Add conversation history (already validated max 10 by schema)
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add the current message
    messages.append({"role": "user", "content": message})

    try:
        # stream=True — response comes back in chunks
        stream = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,        # 0=deterministic, 1=creative, 0.7=balanced
            stream=True,
        )

        # Yield each chunk as it arrives
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    except OpenAIError as e:
        logger.error("OpenAI chat error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {str(e)}",
        )


async def chat_with_ai_simple(
    message: str,
    history: list[dict],
) -> str:
    """
    Non-streaming version of chat — returns full response as string.
    Used internally (e.g. by analytics_service for recommendations).
    Not exposed directly to the frontend.
    """
    client = get_openai_client()

    messages = [{"role": "system", "content": TUTOR_SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    except OpenAIError as e:
        logger.error("OpenAI simple chat error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable.",
        )


# ── Whisper transcription ──────────────────────────────────────────────────

async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribe audio to text using OpenAI Whisper API.

    The browser's MediaRecorder API records audio as .webm format.
    Whisper supports: mp3, mp4, mpeg, mpga, m4a, wav, webm.

    Args:
        audio_bytes: raw audio file bytes from the browser microphone
        filename:    hint for Whisper about the format (default webm)

    Returns:
        Transcribed text string

    Raises:
        HTTPException 400: empty audio or too short
        HTTPException 503: Whisper API error
    """
    if len(audio_bytes) < 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio recording too short. Please speak clearly and try again.",
        )

    client = get_openai_client()

    try:
        # Whisper expects a file-like object with a name attribute
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",          # hint English — improves accuracy
            response_format="text",
        )

        transcribed_text = transcript.strip() if isinstance(transcript, str) else str(transcript)
        logger.info("Transcribed %d bytes → %d chars", len(audio_bytes), len(transcribed_text))
        return transcribed_text

    except OpenAIError as e:
        logger.error("Whisper transcription error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech transcription temporarily unavailable.",
        )


# ── Recommendations ────────────────────────────────────────────────────────

async def get_ai_recommendations(
    weak_topics: list[TopicStat],
    strong_topics: list[TopicStat],
    overall_accuracy: float,
) -> dict:
    """
    Generate a personalised study recommendation using GPT.

    Builds a prompt from the student's analytics data and asks GPT
    to write a specific, actionable improvement plan.

    Args:
        weak_topics:      list of TopicStat with low accuracy
        strong_topics:    list of TopicStat with high accuracy
        overall_accuracy: overall score percentage

    Returns:
        dict with:
            recommendation_text: full paragraph from GPT
            focus_topics:        list of topic_tags to highlight
            suggested_difficulty: "easy" | "medium" | "hard"
    """
    # Build analytics summary for the prompt
    weak_list = ", ".join(
        f"{t.display_name} ({t.accuracy_pct:.0f}%)" for t in weak_topics
    ) or "none identified yet"

    strong_list = ", ".join(
        f"{t.display_name} ({t.accuracy_pct:.0f}%)" for t in strong_topics
    ) or "none identified yet"

    # Determine overall difficulty suggestion
    if overall_accuracy >= 75:
        suggested_difficulty = "hard"
    elif overall_accuracy >= 50:
        suggested_difficulty = "medium"
    else:
        suggested_difficulty = "easy"

    prompt = f"""A Data Science student has the following performance profile:
Overall accuracy: {overall_accuracy:.1f}%
Strong topics: {strong_list}
Weak topics: {weak_list}

Write a short, encouraging, personalised study recommendation (3-4 sentences) that:
1. Acknowledges their strengths
2. Identifies the top 2 areas to improve
3. Suggests a specific study approach for the weak topics
4. Ends with a motivating sentence

Be specific to Data Science and AI/ML. Keep it concise and actionable."""

    try:
        client = get_openai_client()
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful academic advisor for Data Science students."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.8,
        )
        recommendation_text = response.choices[0].message.content or ""

    except OpenAIError as e:
        logger.error("Recommendation generation error: %s", str(e))
        # Don't fail the whole dashboard if recommendation fails
        recommendation_text = (
            "Keep practising consistently! Focus on your weaker topics "
            "by reviewing the course material and attempting more quizzes."
        )

    return {
        "recommendation_text": recommendation_text,
        "focus_topics": [t.topic_tag for t in weak_topics],
        "suggested_difficulty": suggested_difficulty,
    }

# ════════════════════════════════════════════════════════════════════════
# OCR — Extract text from images using GPT-4o Vision
# Add this function to the END of app/services/ai_service.py
# ════════════════════════════════════════════════════════════════════════

import base64


async def extract_text_from_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> str:
    """
    Extract text from an image using GPT-4o Vision (OCR).

    Reads printed text, handwriting, diagrams, equations, and code
    from photos of textbook pages, notes, screenshots, or whiteboards.

    Args:
        image_bytes: raw image file bytes from the upload
        mime_type:   image format (image/jpeg, image/png, image/webp)

    Returns:
        Extracted text as a clean string

    Raises:
        HTTPException 400: empty or invalid image
        HTTPException 503: OpenAI Vision API error
    """
    if len(image_bytes) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image too small or empty. Please upload a valid image.",
        )

    # GPT-4o Vision needs a vision-capable model; gpt-4o-mini supports vision
    client = get_openai_client()

    # Encode image to base64 data URL
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,  # gpt-4o-mini supports vision
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an OCR engine. Extract ALL text from the image "
                        "exactly as written. Preserve line breaks, code formatting, "
                        "equations, and structure. If the image contains a math or "
                        "coding problem, transcribe it precisely. Output ONLY the "
                        "extracted text with no commentary, no markdown fences."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all text from this image:"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            max_tokens=1500,
            temperature=0,  # deterministic — exact transcription
        )
        extracted = response.choices[0].message.content or ""
        logger.info("OCR extracted %d chars from %d byte image", len(extracted), len(image_bytes))
        return extracted.strip()

    except OpenAIError as e:
        logger.error("OCR vision error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text extraction temporarily unavailable.",
        )


async def explain_extracted_text(extracted_text: str) -> str:
    """
    Take OCR-extracted text and have AICA explain or solve it.

    Used right after extract_text_from_image() so the student gets
    both the text AND an explanation in one flow.

    Args:
        extracted_text: the text returned by OCR

    Returns:
        AICA's explanation as a string
    """
    if not extracted_text.strip():
        return "No text was found in the image to explain."

    client = get_openai_client()

    prompt = (
        f"A student scanned this content:\n\n{extracted_text}\n\n"
        "Explain it clearly. If it's a question or problem, solve it step by step. "
        "If it's a concept, explain it simply with an example. "
        "Keep it focused on Data Science / AI-ML learning."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": TUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    except OpenAIError as e:
        logger.error("OCR explain error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI explanation temporarily unavailable.",
        )