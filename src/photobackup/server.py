import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .storage import StorageManager


def get_env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def get_app() -> FastAPI:
    app = FastAPI(title="PhotoBackUp Server", version="0.1.0")

    storage_root = Path(os.getenv("PHOTO_BACKUP_ROOT", "./backups")).resolve()
    storage = StorageManager(storage_root)

    api_key = os.getenv("PHOTO_BACKUP_API_KEY", "")

    def require_key(key: Optional[str] = None):
        if not api_key:
            return
        if key != api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")

    @app.post("/upload")
    async def upload(file: UploadFile = File(...), x_api_key: Optional[str] = None):
        require_key(x_api_key)
        contents = await file.read()
        # Persist temp file
        tmp_dir = storage.root / ".incoming"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / file.filename
        tmp_path.write_bytes(contents)
        try:
            saved = storage.save_with_dedup(tmp_path, datetime.now())
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass
        rel = saved.relative_to(storage.root)
        return {"saved_path": str(rel)}

    @app.get("/list")
    def list_backups():
        items = []
        for d in sorted(storage.root.iterdir()):
            if not d.is_dir():
                continue
            day_items = []
            for f in sorted(d.iterdir()):
                if f.is_file():
                    day_items.append(f.name)
            items.append({"date": d.name, "files": day_items})
        return {"days": items}

    # Serve the static public UI if present
    public_dir = Path("public").resolve()
    if public_dir.exists():
        app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="static")

    return app


def main() -> None:
    app = get_app()
    host = os.getenv("PHOTO_BACKUP_HOST", "0.0.0.0")
    port = int(os.getenv("PHOTO_BACKUP_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()

