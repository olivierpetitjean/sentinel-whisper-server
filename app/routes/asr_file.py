from __future__ import annotations

from typing import Optional, Literal

from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from ..asr_engine import (
    ffmpeg_to_wav16k_mono,
    transcribe_file,
    segments_to_text,
    segments_to_vtt,
    segments_to_srt,
    segments_to_tsv,
)
from ..utils.tempfiles import save_upload_to_temp, new_temp_path, cleanup_paths
from ..utils.serialize import serialize_words

OutputFormat = Literal["text", "json", "vtt", "srt", "tsv"]
TaskType = Literal["transcribe", "translate"]

router = APIRouter()


@router.post("/asr")
async def asr(
    audio_file: UploadFile = File(...),
    output: OutputFormat = Query("text"),
    task: TaskType = Query("transcribe"),
    language: Optional[str] = Query(None),
    word_timestamps: bool = Query(False),
    vad_filter: bool = Query(False),
    encode: bool = Query(True),
):
    in_path = await save_upload_to_temp(audio_file, suffix="_in")
    path_for_model = in_path
    wav_path = None

    try:
        if encode:
            wav_path = new_temp_path(suffix=".wav")
            ffmpeg_to_wav16k_mono(in_path, wav_path)
            path_for_model = wav_path

        segments, info = transcribe_file(
            path_for_model,
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
            return PlainTextResponse(
                segments_to_srt(segments), media_type="application/x-subrip"
            )

        if output == "tsv":
            return PlainTextResponse(
                segments_to_tsv(segments), media_type="text/tab-separated-values"
            )

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
    finally:
        cleanup_paths(in_path, wav_path)


@router.post("/detect-language")
async def detect_language(
    audio_file: UploadFile = File(...),
    encode: bool = Query(True),
):
    in_path = await save_upload_to_temp(audio_file, suffix="_in")
    path_for_model = in_path
    wav_path = None

    try:
        if encode:
            wav_path = new_temp_path(suffix=".wav")
            # On tronque à 30s (détection langue suffisante + rapide)
            ffmpeg_to_wav16k_mono(in_path, wav_path, max_seconds=30)
            path_for_model = wav_path

        segments, info = transcribe_file(
            path_for_model,
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
        }
    finally:
        cleanup_paths(in_path, wav_path)
