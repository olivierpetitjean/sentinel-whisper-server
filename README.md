# sentinel-whisper-server

Minimal **Whisper ASR** HTTP server for **Sentinel** (CPU-only), dockerized, with **Swagger/OpenAPI**.

This project is intentionally small and easy to run: it exposes a simple transcription API that Sentinel (or any client) can call.

---

## Features

- **FastAPI** server with **Swagger UI** (`/docs`)
- **CPU-only** inference (no CUDA/GPU setup)
- Uses **faster-whisper** (Whisper via CTranslate2) for good CPU performance on CPU
- **FFmpeg** audio normalization (mono 16kHz PCM) for consistent results
- Dockerized and designed to run on multiple architectures

---

## Supported platforms / architectures

Docker image targets:
- `linux/amd64` (x86_64)
- `linux/arm64` (AArch64 / Raspberry Pi 64-bit)

On **Windows**, run it with Docker Desktop using **Linux containers (WSL2)**.

---

## API

### Swagger / OpenAPI

- Swagger UI: `http://localhost:9000/docs`
- OpenAPI JSON: `http://localhost:9000/openapi.json`

### Health

- `GET /health`  
  Returns: `{ "status": "ok" }`

### Transcription (ASR)

- `POST /asr`

**Multipart form-data**
- `audio_file` (file) — required

**Query params**
- `output` = `text | json | vtt | srt | tsv` (default: `text`)
- `task` = `transcribe | translate` (default: `transcribe`)
- `language` = ISO code (optional, e.g. `fr`, `en`)
- `word_timestamps` = `true|false` (default: `false`)
- `vad_filter` = `true|false` (default: `false`)
- `encode` = `true|false` (default: `true`)  
  When `true`, audio is normalized via FFmpeg before inference.

**Examples**
```bash
curl -X POST -H "content-type: multipart/form-data" \
  -F "audio_file=@/path/to/audio.wav" \
  "http://localhost:9000/asr?output=json&task=transcribe"
```

```bash
curl -X POST -H "content-type: multipart/form-data" \
  -F "audio_file=@/path/to/audio.mp3" \
  "http://localhost:9000/asr?output=text&encode=true"
```

### Language detection

- `POST /detect-language`

**Multipart form-data**
- `audio_file` (file) — required

**Query params**
- `encode` = `true|false` (default: `true`)

**Response (example)**
```json
{
  "detected_language": "fr",
  "language_code": "fr",
  "confidence": 0.98
}
```

**Example**
```bash
curl -X POST -H "content-type: multipart/form-data" \
  -F "audio_file=@/path/to/audio.wav" \
  "http://localhost:9000/detect-language"
```

---

## Model configuration (CPU)

This server loads **one Whisper model at startup** (recommended for simplicity and predictable memory usage).

Environment variables:
- `ASR_MODEL` (default: `small`)  
  Examples: `tiny`, `base`, `small`, `medium`, `large-v3`
- `ASR_DEVICE` (default: `cpu`)
- `ASR_COMPUTE_TYPE` (default: `int8`)
- `ASR_MODEL_DIR` (optional) — where models are downloaded/cached in the container

Notes:
- `int8` is usually a good CPU compromise (speed / memory).
- For Raspberry Pi, start with `tiny` or `base`.

---

## Run (Docker)

### Build & run
```bash
docker compose up --build
```

Then open:
- Swagger: `http://localhost:9000/docs`

### Caching downloaded models
The compose file mounts a local `./cache` folder to persist downloaded models across restarts.

---

## Compatibility with Whisper ASR Webservice

This project aims to keep **compatible endpoint names and common query parameters** (`/asr`, `/detect-language`, `output`, `task`, `language`, etc.) so it can be used as a **drop-in CPU alternative** for simple setups.

If you want a more feature-complete solution (and/or GPU support), you can use **Whisper ASR Webservice** instead.

---

## Releases & Docker image publishing (GHCR)

This repo includes a GitHub Actions workflow that builds and publishes a **multi-arch** image to **GitHub Container Registry (GHCR)** when you push a git tag like `v1.0.0`.

Example:
```bash
git tag v1.0.0
git push origin v1.0.0
```

The image will be published as:
- `ghcr.io/olivierpetitjean/sentinel-whisper-server:1.0.0`

By design, there is **no** `latest` tag.

---

## License

MIT License. See `LICENSE`.

This project bundles third-party components. See `THIRD_PARTY_NOTICES.md`.
