from __future__ import annotations


def serialize_words(words):
    if not words:
        return None

    out = []
    for w in words:
        out.append(
            {
                "start": float(getattr(w, "start", 0.0)),
                "end": float(getattr(w, "end", 0.0)),
                "word": getattr(w, "word", getattr(w, "text", "")),
                "probability": (
                    float(getattr(w, "probability", 0.0))
                    if getattr(w, "probability", None) is not None
                    else None
                ),
            }
        )
    return out
