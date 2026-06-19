"""Small filesystem helpers shared by background-safe writers."""

from pathlib import Path


def write_text_atomic(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write text via same-directory replace so readers never see partial JSON/cache."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding=encoding)
    tmp.replace(path)
