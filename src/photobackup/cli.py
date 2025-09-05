import argparse
import glob
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Iterable, List, Optional


def _print(msg: str) -> None:
    sys.stdout.write(msg + "\n")


def _pigz_available() -> bool:
    return shutil.which("pigz") is not None


def _expand_archives(patterns: List[str]) -> List[Path]:
    expanded: List[Path] = []
    for pattern in patterns:
        for match in glob.glob(pattern):
            expanded.append(Path(match))
    return expanded


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def import_takeout(archives: List[str], destination: str, skip_existing: bool, strip_components: int, use_pigz: Optional[bool], dry_run: bool) -> None:
    dest = Path(destination).resolve()
    _ensure_dir(dest)

    resolved_archives = _expand_archives(archives)
    if not resolved_archives:
        raise SystemExit("No archives found for provided --archive patterns")

    use_pigz_final = _pigz_available() if use_pigz is None else use_pigz

    for archive in resolved_archives:
        if not archive.exists():
            _print(f"Skipping missing archive: {archive}")
            continue
        _print(f"Processing archive: {archive}")
        if dry_run:
            _print(f"DRY-RUN: would extract to {dest}")
            continue

        if use_pigz_final:
            # pigz --decompress <file | tar --extract
            tar_cmd = [
                "tar",
                "--extract",
                f"--strip-components={strip_components}",
                "--directory",
                str(dest),
            ]
            if skip_existing:
                tar_cmd.append("--skip-old-files")

            cmd = [
                "bash",
                "-lc",
                f"pigz --decompress < {shlex_quote(str(archive))} | {' '.join(map(shlex_quote, tar_cmd))}",
            ]
            _run_checked(cmd)
        else:
            # Use Python's tarfile
            mode = "r:gz"
            with tarfile.open(archive, mode) as tf:
                for member in tf.getmembers():
                    # Strip path components manually and validate
                    parts = Path(member.name).parts[strip_components:]
                    if not parts:
                        continue
                    if any(part in ("..", "") for part in parts):
                        continue
                    rel_path = Path(*parts)
                    # Skip dangerous types
                    if member.issym() or member.islnk():
                        continue
                    dest_path = (dest / rel_path).resolve()
                    # Ensure path remains within destination
                    if not str(dest_path).startswith(str(dest) + os.sep):
                        continue
                    if member.isdir():
                        dest_path.mkdir(parents=True, exist_ok=True)
                        continue
                    if skip_existing and dest_path.exists():
                        continue
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    if member.isreg():
                        src_f = tf.extractfile(member)
                        if src_f is None:
                            continue
                        with open(dest_path, "wb") as out_f:
                            shutil.copyfileobj(src_f, out_f)
                    # Other member types are ignored


def _run_checked(cmd: List[str]) -> None:
    proc = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def shlex_quote(s: str) -> str:
    # Minimal shlex.quote to avoid importing shlex
    if not s:
        return "''"
    if all(c.isalnum() or c in ("_", "-", ".", "/", ":") for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def file_hash(path: Path, algo: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    import hashlib

    hasher = getattr(hashlib, algo)()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def dedupe(root: str, link_hard: bool, algo: str, dry_run: bool) -> None:
    root_path = Path(root).resolve()
    if not root_path.exists():
        raise SystemExit(f"Root path not found: {root}")

    size_to_paths: dict[int, List[Path]] = {}
    for dirpath, _dirnames, filenames in os.walk(root_path):
        for name in filenames:
            p = Path(dirpath) / name
            try:
                st = p.stat()
            except OSError:
                continue
            size_to_paths.setdefault(st.st_size, []).append(p)

    duplicates: List[List[Path]] = []
    for size, paths in size_to_paths.items():
        if len(paths) < 2:
            continue
        hash_to_paths: dict[str, List[Path]] = {}
        for p in paths:
            try:
                h = file_hash(p, algo)
            except Exception:
                continue
            hash_to_paths.setdefault(h, []).append(p)
        for _h, group in hash_to_paths.items():
            if len(group) > 1:
                duplicates.append(group)

    actions = 0
    for group in duplicates:
        canonical = group[0]
        for p in group[1:]:
            if dry_run:
                _print(f"DRY-RUN: would hardlink {p} -> {canonical}")
                actions += 1
                continue
            if link_hard:
                # Replace file with hardlink to canonical
                tmp = p.with_suffix(p.suffix + ".tmp_link")
                try:
                    if tmp.exists():
                        tmp.unlink()
                    os.link(canonical, tmp)
                    p.unlink()
                    tmp.rename(p)
                    actions += 1
                except OSError:
                    # skip on failure
                    continue
    _print(f"Dedup complete. Actions: {actions}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="photobackup", description="PhotoBackUp CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="Import Google Takeout archives")
    p_import.add_argument("--archive", "-a", action="append", required=True, help="Archive path or glob; can be repeated")
    p_import.add_argument("--to", required=True, help="Destination directory")
    p_import.add_argument("--skip-existing", action="store_true", help="Skip existing files")
    p_import.add_argument("--strip-components", type=int, default=2, help="Strip N path components (default: 2)")
    p_import.add_argument("--use-pigz", dest="use_pigz", action="store_true", help="Force use of pigz if available")
    p_import.add_argument("--no-pigz", dest="use_pigz", action="store_false", help="Disable pigz usage")
    p_import.set_defaults(use_pigz=None)
    p_import.add_argument("--dry-run", action="store_true", help="Do not write changes")

    p_dedupe = sub.add_parser("dedupe", help="Deduplicate identical files by hard-linking")
    p_dedupe.add_argument("--root", required=True, help="Root directory to scan")
    p_dedupe.add_argument("--link-hard", action="store_true", help="Replace duplicates with hard links")
    p_dedupe.add_argument("--algo", default="sha256", choices=["sha256"], help="Hash algorithm")
    p_dedupe.add_argument("--dry-run", action="store_true", help="Do not write changes")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        import_takeout(
            archives=args.archive,
            destination=args.to,
            skip_existing=args.skip_existing,
            strip_components=args.strip_components,
            use_pigz=args.use_pigz,
            dry_run=args.dry_run,
        )
        return 0
    if args.command == "dedupe":
        dedupe(
            root=args.root,
            link_hard=args.link_hard,
            algo=args.algo,
            dry_run=args.dry_run,
        )
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

