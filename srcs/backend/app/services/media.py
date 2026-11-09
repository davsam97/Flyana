"""Avatars

1. The size cap applies while reading, not after a full `await file.read()`.
2. `content_type` and the extension are never trusted: Pillow decides.
3. Every image is re-encoded, which drops metadata and any payload hidden in
   a polyglot file.
"""

from __future__ import annotations

import asyncio
import colorsys
import hashlib
import io
import secrets
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

MEDIA_ROOT = Path("/srv/media")
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # matches nginx client_max_body_size
CHUNK = 64 * 1024
ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "WEBP", "GIF"})
AVATAR_SIZE = 512

# Decompression bomb: a 4 kB PNG can declare 50 000² pixels (~7.5 GB decoded)
Image.MAX_IMAGE_PIXELS = 40_000_000


async def read_limited(file: UploadFile, limit: int = MAX_AVATAR_BYTES) -> bytes:
    """Reads an upload but stops the moment it goes over the size cap"""
    buf = bytearray()
    while chunk := await file.read(CHUNK):
        buf.extend(chunk)
        if len(buf) > limit:
            raise HTTPException(
                status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"file too heavy (max {limit // 1024 // 1024} Mo)",
            )
    return bytes(buf)


def _process_sync(raw: bytes) -> bytes:
    """Validates then re encodes an image the blocking way"""
    # Everything Pillow touches is attacker controlled, so it all lives inside the try
    # The 415 raised below crosses it untouched: HTTPException inherits
    # from neither OSError nor ValueError
    try:
        with Image.open(io.BytesIO(raw)) as img:
            fmt = img.format
            if fmt not in ALLOWED_FORMATS:
                raise HTTPException(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"unauthorised format : {fmt}",
                )
            img.verify()

        with Image.open(io.BytesIO(raw)) as img:
            rgb = img.convert("RGB")
            rgb.thumbnail((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            rgb.save(out, format="WEBP", quality=82, method=4)
            return out.getvalue()

    # Before the other except : DecompressionBombError derives from Exception,
    # not from OSError, so it would never be reached after it
    except Image.DecompressionBombError as exc:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            detail="image too large once decoded",
        ) from exc
    # UnidentifiedImageError derives from OSError, named for what it says
    # a polyglot `GIF89a<script>` lands here : Pillow never identifies it,
    # so the whitelist above never even runs. Without this the request is a 500
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="unreadable image",
        ) from exc


async def process_avatar(raw: bytes) -> bytes:
    """Validates and re encodes an uploaded image"""
    return await asyncio.to_thread(_process_sync, raw)


async def save_avatar(data: bytes) -> str:
    """Writes the processed image under a random name, never the client's filename"""
    name = f"{secrets.token_hex(16)}.webp"
    path = MEDIA_ROOT / "avatars" / name
    await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(path.write_bytes, data)
    return f"/media/avatars/{name}"  # public path, nginx location /media/


async def delete_avatar(public_path: str | None) -> None:
    """Removes an uploaded avatar from disk, given the path `save_avatar` returned"""
    prefix = "/media/avatars/"
    if not public_path or not public_path.startswith(prefix):
        return
    # the name is ours (`token_hex`), but never let a stored value walk out of the folder
    name = Path(public_path[len(prefix):]).name
    await asyncio.to_thread((MEDIA_ROOT / "avatars" / name).unlink, missing_ok=True)


def identicon(user_id: int, size: int = AVATAR_SIZE) -> bytes:
    """Draws a symmetric 5×5 fallback avatar from a hash of the user id"""
    digest = hashlib.sha256(str(user_id).encode()).digest()
    r, g, b = (int(c * 255) for c in colorsys.hsv_to_rgb(digest[0] / 255.0, 0.55, 0.72))

    grid = 5
    img = Image.new("RGB", (grid, grid), (238, 238, 243))
    for x in range(3):
        for y in range(grid):
            if digest[1 + x * grid + y] & 1:
                img.putpixel((x, y), (r, g, b))
                img.putpixel((grid - 1 - x, y), (r, g, b))
    out = io.BytesIO()
    img.resize((size, size), Image.Resampling.NEAREST).save(out, format="WEBP")
    return out.getvalue()
