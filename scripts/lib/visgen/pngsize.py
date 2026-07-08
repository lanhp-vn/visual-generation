"""Read PNG pixel dimensions from the IHDR chunk (bytes 16-24). No Pillow."""
import struct
from pathlib import Path


def png_size(path) -> tuple[int, int]:
    data = Path(path).read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    w, h = struct.unpack(">II", data[16:24])
    return int(w), int(h)
