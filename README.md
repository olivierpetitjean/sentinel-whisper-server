# sentinel-whisper-server

Minimal **Whisper ASR** HTTP server for **Sentinel** (CPU-only), dockerized, with **Swagger/OpenAPI**.

This project is intentionally small and easy to run: it exposes a simple transcription API that Sentinel (or any client) can call.

---

## Features

- **FastAPI** server with **Swagger UI** (`/docs`)
- **CPU-only** inference (no CUDA/GPU setup)
- Uses **faster-whisper** (Whisper via CTranslate2) for good CPU performance on CPU
- **Optional FFmpeg** audio normalization (**multipart** endpoints only, `encode=true`) to ensure consistent results (mono 16kHz PCM)
- **Native PCM (strict)** batch endpoints for Sentinel (no FFmpeg, no resampling, no downmix): `POST /asr/pcm`, `POST /detect-language/pcm`
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

## Native PCM endpoints (strict)

These endpoints accept **raw PCM** directly, with **no FFmpeg** and **no normalization**.

**Accepted audio format (only):**
- **PCM float32 little-endian**, **mono**, **16 kHz**
- Canonical format string: `audio/x-f32le;rate=16000;channels=1`

### Transcription (ASR) — PCM

- `POST /asr/pcm`

**Content-Type**
- `application/octet-stream`

**Body**
- Raw `f32le` PCM stream (mono 16 kHz). Values are expected in `[-1.0, +1.0]` (server may clamp).

**Query params** (same as `/asr`, except **no** `encode`)
- `output` = `text | json | vtt | srt | tsv` (default: `text`)
- `task` = `transcribe | translate` (default: `transcribe`)
- `language` = ISO code (optional, e.g. `fr`, `en`)
- `word_timestamps` = `true|false` (default: `false`)
- `vad_filter` = `true|false` (default: `false`)

**Optional headers (debug/correlation)**
- `X-Audio-Format: audio/x-f32le;rate=16000;channels=1`
- `X-Session-Id: <id>`
- `X-Turn-Id: <id>`

**Errors (strict validation)**
- `415` if `Content-Type` is not `application/octet-stream`
- `400` if body is empty or length is not a multiple of 4 bytes
- Optional: `413` if payload is too large (configurable via `MAX_PCM_BYTES` environment variable)

**Example**
```bash
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  -H "X-Audio-Format: audio/x-f32le;rate=16000;channels=1" \
  --data-binary @audio_16k_mono_f32le.pcm \
  "http://localhost:9000/asr/pcm?output=text&task=transcribe&language=fr"
```

### Language detection — PCM

- `POST /detect-language/pcm`

Same contract as `/asr/pcm` (octet-stream `f32le` mono 16 kHz). Response matches `/detect-language`.

**Example**
```bash
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @audio_16k_mono_f32le.pcm \
  "http://localhost:9000/detect-language/pcm"
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

This repo includes a GitHub Actions workflow that builds and publishes a **multi-arch** image to **GitHub Container Registry (GHCR)** and **Docker Hub[^1]** when you push a git tag like `v1.0.0`.

Example:
```bash
git tag v1.0.0
git push origin v1.0.0
```

The image will be published as:
- `https://ghcr.io/<your-github-username>/sentinel-whisper-server:1.0.0`
- `https://hub.docker.com/r/<your-docker-hub-username>/sentinel-whisper-server`

By design, there is **no** `latest` tag.

[^1]: see [GitHub Actions secrets](https://docs.github.com/fr/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) on your repository settings if you want to publish on Docker Hub.

---

## License

MIT License. See `LICENSE`.

## Third-party notices

This project bundles third-party components. See THIRD_PARTY_NOTICES.md.