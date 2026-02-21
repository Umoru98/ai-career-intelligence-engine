from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import IO

import aiofiles

from app.core.config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def save_upload_file(
    file_obj: IO[bytes],
    original_filename: str,
    content_type: str,
) -> tuple[str, str, int]:
    """
    Save uploaded file to disk with a random safe filename.
    Returns (stored_path, sha256_hex, size_bytes).
    """
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(original_filename).suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = upload_dir / safe_name

    hasher = hashlib.sha256()
    size = 0

    async with aiofiles.open(dest_path, "wb") as out_file:
        while True:
            chunk = file_obj.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
            size += len(chunk)
            await out_file.write(chunk)

    return str(dest_path), hasher.hexdigest(), size


def validate_content_type(content_type: str) -> bool:
    return content_type in ALLOWED_CONTENT_TYPES
