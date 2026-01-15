from __future__ import annotations

import os
import tempfile
from typing import Optional
from fastapi import UploadFile


async def save_upload_to_temp(audio_file: UploadFile, suffix: str = "_in") -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f_in:
        f_in.write(await audio_file.read())
        return f_in.name


def new_temp_path(suffix: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        return f.name


def cleanup_paths(*paths: Optional[str]) -> None:
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
