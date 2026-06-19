"""Small filesystem helpers shared by background-safe writers."""

import os
from pathlib import Path
from uuid import uuid4


def write_text_atomic(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write text via same-directory replace so readers never see partial JSON/cache."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        tmp.write_text(text, encoding=encoding)
        tmp.replace(path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
