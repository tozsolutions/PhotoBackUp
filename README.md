# PhotoBackUp

Minimal, local-first tooling to import Google Takeout Archives (Google Photos) into a target directory and deduplicate identical media using hard links.

## Features

- Import `.tgz` Takeout archives directly to a target directory
- Skip existing files safely to avoid overwrite
- Optional parallel extraction when `pigz` is available
- Deduplicate identical files by hard-linking, saving disk space
- Dry-run support to preview actions

## Requirements

- Python 3.9+
- Optional: `pigz` for faster decompression

## Install (local)

```bash
python3 -m venv .venv  # if ensurepip is available
source .venv/bin/activate
pip install -e .
```

If venv creation isn’t available on your system, you can run via module mode:

```bash
PYTHONPATH=src python3 -m photobackup.cli --help
```

## Usage

```bash
photobackup import --archive path/to/takeout-*.tgz --to /path/to/Originals --skip-existing
photobackup dedupe --root /path/to/Originals --link-hard
```

### Import options
- `--archive`: Glob/path to a Takeout archive (supports multiple). Required.
- `--to`: Destination directory. Required.
- `--skip-existing`: Do not overwrite existing files.
- `--strip-components`: How many path components to strip from tar entries (default 2).
- `--use-pigz` / `--no-pigz`: Force/disable `pigz` usage (default: auto-detect).
- `--dry-run`: Show planned actions without writing.

### Dedupe options
- `--root`: Root directory to scan recursively. Required.
- `--link-hard`: Replace duplicates with hard links to a canonical file.
- `--algo`: Hash algorithm, `sha256` (default). More can be added later.
- `--dry-run`: Show planned actions without writing.

## Security & Safety

- Tar extraction via Python enforces path sanitization and ignores symlinks.
- When using `pigz|tar`, use trusted archives. The Python path is safer by default.

## Deploying Docs

This repo includes a minimal `public/index.html` and `netlify.toml`.

- Netlify: Connect repo, keep default build (command in `netlify.toml`), publish `public/`.
- Vercel: Use the included `vercel.json` to serve `public/`.

## License

MIT