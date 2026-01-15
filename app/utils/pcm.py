from __future__ import annotations

import os
import numpy as np
from fastapi import HTTPException, Request

EXPECTED_AUDIO_FORMAT = "audio/x-f32le;rate=16000;channels=1"


def require_octet_stream(request: Request) -> None:
    ct = (request.headers.get("content-type") or "").lower()
    if not ct.startswith("application/octet-stream"):
        raise HTTPException(
            status_code=415,
            detail={
                "error": "UNSUPPORTED_MEDIA_TYPE",
                "expected": "application/octet-stream",
            },
        )


def optional_validate_x_audio_format(request: Request) -> None:
    hdr = request.headers.get("x-audio-format")
    if hdr is None:
        return
    if hdr.strip().lower() != EXPECTED_AUDIO_FORMAT.lower():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNSUPPORTED_AUDIO_FORMAT",
                "expected": EXPECTED_AUDIO_FORMAT,
                "got": hdr,
            },
        )


def enforce_max_bytes(body_len: int) -> None:
    # Optional hard limit (bytes). Set env to disable or tune.
    # Example: 60s @ 16kHz float32 mono => 16_000 * 60 * 4 = 3_840_000 bytes
    max_bytes_s = os.getenv("MAX_PCM_BYTES", "").strip()
    if not max_bytes_s:
        return

    try:
        max_bytes = int(max_bytes_s)
    except ValueError:
        return

    if max_bytes > 0 and body_len > max_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "PAYLOAD_TOO_LARGE",
                "max_bytes": max_bytes,
                "got_bytes": body_len,
                "expected": EXPECTED_AUDIO_FORMAT,
            },
        )


def read_f32le_mono_16k_strict(body: bytes, clamp: bool = True) -> np.ndarray:
    if not body:
        raise HTTPException(
            status_code=400,
            detail={"error": "EMPTY_BODY", "expected": EXPECTED_AUDIO_FORMAT},
        )

    if (len(body) % 4) != 0:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_LENGTH", "expected": EXPECTED_AUDIO_FORMAT},
        )

    # Little-endian float32
    audio = np.frombuffer(body, dtype="<f4")

    if clamp:
        np.clip(audio, -1.0, 1.0, out=audio)

    return audio
