from __future__ import annotations

import os
import tempfile
from typing import Optional, Literal

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from .asr_engine import (
    ffmpeg_to_wav16k_mono,
    transcribe_file,
    segments_to_text,
    segments_to_vtt,
    segments_to_srt,
    segments_to_tsv,
)

OutputFormat = Literal["text", "json", "vtt", "srt", "tsv"]
TaskType = Literal["transcribe", "translate"]

app = FastAPI(
    title="sentinel-whisper-server",
    version=os.getenv("APP_VERSION", "0.1.0"),
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/asr")
async def asr(
    audio_file: UploadFile = File(...),
    output: OutputFormat = Query("text"),
    task: TaskType = Query("transcribe"),
    language: Optional[str] = Query(None),
    word_timestamps: bool = Query(False),
    vad_filter: bool = Query(False),
    encode: bool = Query(True),
):
    # Save upload
    with tempfile.NamedTemporaryFile(suffix="_in", delete=False) as f_in:
        f_in.write(await audio_file.read())
        in_path = f_in.name

    path_for_model = in_path
    wav_path = None

    try:
        if encode:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f_wav:
                wav_path = f_wav.name
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
                    "words": _serialize_words(getattr(s, "words", None)),
                }
                for i, s in enumerate(segments)
            ],
        })
    finally:
        # cleanup best effort
        for p in [in_path, wav_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


@app.post("/detect-language")
async def detect_language(
    audio_file: UploadFile = File(...),
    encode: bool = Query(True),
):
    with tempfile.NamedTemporaryFile(suffix="_in", delete=False) as f_in:
        f_in.write(await audio_file.read())
        in_path = f_in.name

    path_for_model = in_path
    wav_path = None

    try:
        if encode:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f_wav:
                wav_path = f_wav.name
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
        for p in [in_path, wav_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

def _serialize_words(words):
    if not words:
        return None
    out = []
    for w in words:
        out.append({
            "start": float(getattr(w, "start", 0.0)),
            "end": float(getattr(w, "end", 0.0)),
            "word": getattr(w, "word", getattr(w, "text", "")),
            "probability": (float(getattr(w, "probability", 0.0))
                            if getattr(w, "probability", None) is not None else None),
        })
    return out