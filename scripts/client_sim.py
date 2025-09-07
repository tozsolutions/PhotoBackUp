import argparse
import os
import time
from pathlib import Path

import requests


def find_recent_files(root: Path, hours: int) -> list[Path]:
    now = time.time()
    cutoff = now - hours * 3600
    results: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_mtime >= cutoff:
                results.append(p)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="Directory to scan")
    parser.add_argument("--hours", type=int, default=24, help="Look back this many hours")
    parser.add_argument("--url", required=True, help="Server upload URL, e.g., http://PC-IP:8080/upload")
    parser.add_argument("--api-key", default="", help="x-api-key header if required")
    args = parser.parse_args()

    root = Path(args.dir)
    files = find_recent_files(root, args.hours)
    print(f"Found {len(files)} files")

    headers = {}
    if args.api_key:
        headers["x-api-key"] = args.api_key

    for p in files:
        with p.open("rb") as f:
            files_param = {"file": (p.name, f)}
            r = requests.post(args.url, files=files_param, headers=headers, timeout=60)
            if r.status_code != 200:
                print(f"Failed: {p} -> {r.status_code} {r.text}")
            else:
                print(f"Uploaded: {p} -> {r.json().get('saved_path')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())