"""Manage physical RAG source files on disk and trigger re-ingestion."""
import os
import shutil
from pathlib import Path
from typing import List

import httpx
from fastapi import HTTPException, UploadFile, status

from src.core.config import get_settings


class RagFileService:
    def __init__(self) -> None:
        self._docs_path = Path(get_settings().DECISIONING_DOCS_PATH)
        self._decisioning_url = get_settings().DECISIONING_AGENT_URL

    def _resolve(self, filename: str) -> Path:
        path = (self._docs_path / filename).resolve()
        if not str(path).startswith(str(self._docs_path.resolve())):
            raise HTTPException(status_code=400, detail="Invalid filename")
        return path

    def list_files(self) -> List[dict]:
        if not self._docs_path.exists():
            return []
        files = []
        for entry in sorted(self._docs_path.iterdir()):
            if entry.is_file():
                stat = entry.stat()
                files.append(
                    {"filename": entry.name, "size_bytes": stat.st_size, "modified_at": stat.st_mtime}
                )
        return files

    async def save_file(self, file: UploadFile) -> dict:
        self._docs_path.mkdir(parents=True, exist_ok=True)
        dest = self._resolve(file.filename)
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        stat = dest.stat()
        return {"filename": dest.name, "size_bytes": stat.st_size, "modified_at": stat.st_mtime}

    def delete_file(self, filename: str) -> None:
        path = self._resolve(filename)
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {filename}")
        path.unlink()

    async def trigger_reingestion(self) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self._decisioning_url}/internal/refresh-rag")
            resp.raise_for_status()
        return resp.json()
