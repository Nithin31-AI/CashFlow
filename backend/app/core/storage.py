import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

# Magic number signatures
MAGIC_NUMBERS = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "xlsx": b"PK\x03\x04",
    "xls": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
}

def sanitize_filename(filename: str) -> str:
    # Remove path traversal and invalid characters
    base = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    if not clean or clean.startswith("."):
        clean = f"upload_{clean}"
    return clean

def detect_mime_and_validate(header_bytes: bytes, ext: str) -> str:
    ext_lower = ext.lstrip(".").lower()
    
    if ext_lower == "pdf":
        if header_bytes.startswith(MAGIC_NUMBERS["pdf"]):
            return "application/pdf"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file content signature."
        )
    elif ext_lower == "png":
        if header_bytes.startswith(MAGIC_NUMBERS["png"]):
            return "image/png"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PNG file content signature."
        )
    elif ext_lower in ("jpg", "jpeg"):
        if header_bytes.startswith(MAGIC_NUMBERS["jpeg"]):
            return "image/jpeg"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JPEG file content signature."
        )
    elif ext_lower == "xlsx":
        if header_bytes.startswith(MAGIC_NUMBERS["xlsx"]):
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid XLSX file content signature."
        )
    elif ext_lower == "xls":
        if header_bytes.startswith(MAGIC_NUMBERS["xls"]):
            return "application/vnd.ms-excel"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid XLS file content signature."
        )
    elif ext_lower == "csv":
        # Check that it's plain text without null bytes
        if b"\x00" in header_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Binary content detected in CSV file."
            )
        return "text/csv"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {ext}"
        )

class StorageManager:
    @staticmethod
    async def save_uploaded_file(upload_file: UploadFile) -> Tuple[str, str, int, str, str]:
        """
        Reads, validates, computes hash, and saves file to non-public secure storage.
        Returns: (safe_stored_filename, absolute_file_path, file_size, mime_type, sha256_hash)
        """
        original_name = upload_file.filename or "uploaded_file"
        clean_name = sanitize_filename(original_name)
        _, ext = os.path.splitext(clean_name)
        ext = ext.lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not permitted. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Read content
        content = await upload_file.read()
        file_size = len(content)

        # Size check
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        # Validate magic number / content
        header_sample = content[:64]
        mime_type = detect_mime_and_validate(header_sample, ext)

        # Calculate SHA-256 hash
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Generate unique storage filename
        stored_filename = f"{uuid.uuid4().hex}_{clean_name}"
        storage_dir = settings.upload_path
        storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = str(storage_dir / stored_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        return stored_filename, file_path, file_size, mime_type, sha256_hash
