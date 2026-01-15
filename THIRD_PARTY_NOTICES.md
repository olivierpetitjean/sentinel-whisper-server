# Third-Party Notices

This project depends on third-party software packages. Their respective licenses apply.

Tip: You can (re)generate the Python dependency license table automatically (see “How to regenerate” below).

---

## Python dependencies (runtime)

The Docker image installs the Python dependencies from requirements.txt.

| Package | Version | License | URL |
|--------:|:--------|:--------|:----|
| fastapi | (see lock/runtime) | (auto) | (auto) |
| uvicorn | (see lock/runtime) | (auto) | (auto) |
| python-multipart | (see lock/runtime) | (auto) | (auto) |
| faster-whisper | (see lock/runtime) | (auto) | (auto) |
| requests | (see lock/runtime) | (auto) | (auto) |

### How to regenerate (recommended)

From a virtualenv (or inside the container) you can generate an authoritative list:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pip-licenses

pip-licenses --format=markdown --with-urls --with-license-file --output-file THIRD_PARTY_NOTICES_PYTHON.md
```

Then either:
- commit THIRD_PARTY_NOTICES_PYTHON.md as the full detailed list, or
- copy/paste the table contents into this file.

Notes:
- Licenses for transitive dependencies (installed automatically) will also be listed by pip-licenses.
- If you use a lockfile in the future, the output becomes perfectly reproducible.

---

## System packages (Docker image)

The Docker image installs system packages via apt, notably:

- ffmpeg

The exact license terms for system packages are provided by the Debian package metadata shipped in the image.
You can find them inside the container under:

- /usr/share/doc/<package>/copyright

Example:

```bash
docker exec -it sentinel-whisper-server sh -lc \
  "sed -n '1,120p' /usr/share/doc/ffmpeg/copyright"
```

---

## Trademarks

“Whisper” and any referenced upstream project names are trademarks of their respective owners.
This project is not affiliated with upstream authors unless explicitly stated.

---

## Contact

If you believe a notice is missing or incorrect, please open an issue or a pull request.
