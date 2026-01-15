from __future__ import annotations

import os
import subprocess
from typing import Optional, Literal, Tuple, Iterable, Any

import numpy as np
from faster_whisper import WhisperModel

TaskType = Literal["transcribe", "translate"]

_MODEL: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    model_name = os.getenv("ASR_MODEL", "small")
    device = os.getenv("ASR_DEVICE", "cpu")
    compute_type = os.getenv("ASR_COMPUTE_TYPE", "int8")
    model_dir = os.getenv("ASR_MODEL_DIR", None)

    _MODEL = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        download_root=model_dir,
    )
    return _MODEL


def ffmpeg_to_wav16k_mono(in_path: str, out_wav_path: str, max_seconds: int | None = None) -> None:
    # ffmpeg -i input -ac 1 -ar 16000 -c:a pcm_s16le output.wav
    cmd = ["ffmpeg", "-y", "-i", in_path]
    if max_seconds is not None:
        cmd += ["-t", str(max_seconds)]
    cmd += ["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", out_wav_path]

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {p.stderr.decode('utf-8', errors='ignore')}")


def transcribe_file(
    path: str,
    task: TaskType = "transcribe",
    language: Optional[str] = None,
    vad_filter: bool = False,
    word_timestamps: bool = False,
):
    model = _get_model()
    segments, info = model.transcribe(
        path,
        task=task,
        language=language,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
    )
    # faster-whisper returns a generator; materialize to re-use
    segments = list(segments)
    return segments, info


def transcribe_pcm_f32le_16k_mono(
    audio_f32: np.ndarray,
    task: TaskType = "transcribe",
    language: Optional[str] = None,
    vad_filter: bool = False,
    word_timestamps: bool = False,
):
    """
    Strict native-only input: float32 mono 16kHz
    """
    if audio_f32.dtype != np.float32:
        audio_f32 = audio_f32.astype(np.float32, copy=False)

    model = _get_model()
    segments, info = model.transcribe(
        audio_f32,
        task=task,
        language=language,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
    )
    segments = list(segments)
    return segments, info


# ----------------------
# Formatting helpers
# ----------------------

def segments_to_text(segments) -> str:
    return "".join(s.text for s in segments).strip()


def _fmt_ts_vtt(seconds: float) -> str:
    # VTT: hh:mm:ss.mmm
    ms = int(round(seconds * 1000.0))
    hh = ms // 3600000
    ms -= hh * 3600000
    mm = ms // 60000
    ms -= mm * 60000
    ss = ms // 1000
    ms -= ss * 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d}.{ms:03d}"


def _fmt_ts_srt(seconds: float) -> str:
    # SRT: hh:mm:ss,mmm
    ms = int(round(seconds * 1000.0))
    hh = ms // 3600000
    ms -= hh * 3600000
    mm = ms // 60000
    ms -= mm * 60000
    ss = ms // 1000
    ms -= ss * 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def segments_to_vtt(segments) -> str:
    lines = ["WEBVTT", ""]
    for i, s in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{_fmt_ts_vtt(float(s.start))} --> {_fmt_ts_vtt(float(s.end))}")
        lines.append((s.text or "").strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def segments_to_srt(segments) -> str:
    lines = []
    for i, s in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{_fmt_ts_srt(float(s.start))} --> {_fmt_ts_srt(float(s.end))}")
        lines.append((s.text or "").strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def segments_to_tsv(segments) -> str:
    # simple TSV: start\tend\ttext
    lines = ["start\tend\ttext"]
    for s in segments:
        lines.append(f"{float(s.start):.3f}\t{float(s.end):.3f}\t{(s.text or '').strip()}")
    return "\n".join(lines).strip() + "\n"
