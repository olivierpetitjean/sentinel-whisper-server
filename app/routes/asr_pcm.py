from __future__ import annotations

from typing import Optional, Literal

from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from ..asr_engine import (
    transcribe_pcm_f32le_16k_mono,
    segments_to_text,
    segments_to_vtt,
    segments_to_srt,
    segments_to_tsv,
)
from ..utils.pcm import (
    EXPECTED_AUDIO_FORMAT,
    require_octet_stream,
    optional_validate_x_audio_format,
    enforce_max_bytes,
    read_f32le_mono_16k_strict,
)
from ..utils.serialize import serialize_words

OutputFormat = Literal["text", "json", "vtt", "srt", "tsv"]
TaskType = Literal["transcribe", "translate"]

router = APIRouter()


@router.post("/asr/pcm")
async def asr_pcm(
    request: Request,
    output: OutputFormat = Query("text"),
    task: TaskType = Query("transcribe"),
    language: Optional[str] = Query(None),
    word_timestamps: bool = Query(False),
    vad_filter: bool = Query(False),
):
    """
    STRICT native-only Whisper input:
    - Content-Type: application/octet-stream
    - Body: float32 little-endian PCM, mono, 16kHz
    - No ffmpeg, no resample, no downmix
    """
    require_octet_stream(request)
    optional_validate_x_audio_format(request)

    body = await request.body()
    enforce_max_bytes(len(body))

    audio = read_f32le_mono_16k_strict(body, clamp=True)

    segments, info = transcribe_pcm_f32le_16k_mono(
        audio,
        task=task,
        language=language,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
    )

    if output == "text":
        return PlainTextResponse(segments_to_text(segments))

    if output == "vtt":
        return PlainTextResponse(segments_to_vtt(segments), media_type="text/vtt")

    if output == "srt":
        return PlainTextResponse(segments_to_srt(segments), media_type="application/x-subrip")

    if output == "tsv":
        return PlainTextResponse(segments_to_tsv(segments), media_type="text/tab-separated-values")

    # json
    return JSONResponse(
        {
            "text": segments_to_text(segments),
            "language": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None),
            "segments": [
                {
                    "id": i,
                    "start": float(s.start),
                    "end": float(s.end),
                    "text": s.text,
                    "words": serialize_words(getattr(s, "words", None)),
                }
                for i, s in enumerate(segments)
            ],
        }
    )


@router.post("/detect-language/pcm")
async def detect_language_pcm(request: Request):
    """
    STRICT native-only Whisper input for language detection:
    - Content-Type: application/octet-stream
    - Body: float32 little-endian PCM, mono, 16kHz
    """
    require_octet_stream(request)
    optional_validate_x_audio_format(request)

    body = await request.body()
    enforce_max_bytes(len(body))

    audio = read_f32le_mono_16k_strict(body, clamp=True)

    segments, info = transcribe_pcm_f32le_16k_mono(
        audio,
        task="transcribe",
        language=None,
        vad_filter=False,
        word_timestamps=False,
    )
    _ = segments  # force run

    return {
        "detected_language": getattr(info, "language", None),
        "language_code": getattr(info, "language", None),
        "confidence": float(getattr(info, "language_probability", 0.0) or 0.0),
        "expected": EXPECTED_AUDIO_FORMAT,
    }
