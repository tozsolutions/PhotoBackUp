import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class StorageManager:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def date_dir(self, dt: Optional[datetime] = None) -> Path:
        dt = dt or datetime.now()
        folder = dt.strftime("%Y-%m-%d")
        path = self.root / folder
        path.mkdir(parents=True, exist_ok=True)
        return path

    def compute_hash(self, file_path: Path, algo: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
        hasher = getattr(hashlib, algo)()
        with file_path.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    def save_with_dedup(self, src_path: Path, dt: Optional[datetime] = None) -> Path:
        assert src_path.exists(), f"Source path does not exist: {src_path}"
        target_dir = self.date_dir(dt)
        # Use content hash to identify duplicates
        content_hash = self.compute_hash(src_path)
        target_name = f"{content_hash}{src_path.suffix}"
        target_path = target_dir / target_name
        if target_path.exists():
            # Already saved; hardlink if not same inode
            return target_path
        tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        if tmp_path.exists():
            tmp_path.unlink()
        # Link or copy to tmp then rename
        try:
            os.link(src_path, tmp_path)
        except OSError:
            # Fallback to copy
            data = src_path.read_bytes()
            tmp_path.write_bytes(data)
        tmp_path.rename(target_path)
        return target_path

