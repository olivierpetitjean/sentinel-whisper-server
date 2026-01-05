from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional, Literal

from faster_whisper import WhisperModel

OutputFormat = Literal["text", "json", "vtt", "srt", "tsv"]
TaskType = Literal["transcribe", "translate"]


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("ASR_MODEL", "small")
    device: str = os.getenv("ASR_DEVICE", "cpu")  # cpu | cuda
    compute_type: str = os.getenv("ASR_COMPUTE_TYPE", "int8")  # int8 | float16 | ...
    model_dir: Optional[str] = os.getenv("ASR_MODEL_DIR")  # e.g. /cache/models
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg")


_model: Optional[WhisperModel] = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        s = Settings()
        _model = WhisperModel(
            s.model,
            device=s.device,
            compute_type=s.compute_type,
            download_root=s.model_dir,
        )
    return _model


def ffmpeg_to_wav16k_mono(input_path: str, output_wav_path: str, max_seconds: Optional[int] = None) -> None:
    s = Settings()
    cmd = [
        s.ffmpeg_path, "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        "-vn",
        "-c:a", "pcm_s16le",
    ]
    if max_seconds is not None:
        cmd.extend(["-t", str(max_seconds)])
    cmd.append(output_wav_path)

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffmpeg failed (code={p.returncode}): {err}")


def segments_to_text(segments) -> str:
    return "".join(seg.text for seg in segments).strip()


def _ts_srt(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")


def segments_to_vtt(segments) -> str:
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_ts_srt(seg.start)} --> {_ts_srt(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def segments_to_srt(segments) -> str:
    out = []
    for i, seg in enumerate(segments, 1):
        out.append(str(i))
        out.append(f"{_ts_srt(seg.start)} --> {_ts_srt(seg.end)}")
        out.append(seg.text.strip())
        out.append("")
    return "\n".join(out)


def segments_to_tsv(segments) -> str:
    lines = ["start\tend\ttext"]
    for seg in segments:
        lines.append(f"{seg.start:.3f}\t{seg.end:.3f}\t{seg.text.strip()}")
    return "\n".join(lines)


def transcribe_file(
    input_path: str,
    task: TaskType,
    language: Optional[str],
    vad_filter: bool,
    word_timestamps: bool,
):
    model = get_model()
    segments, info = model.transcribe(
        input_path,
        task=task,
        language=language,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
        beam_size=5,
    )
    return list(segments), info
