from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

DEFAULT_BASE_URL = "https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1/"


def main() -> int:
    args = parse_args()
    rows = read_manifest(args.manifest)
    for row in rows:
        sequence = row["sequence"]
        for path_key, hash_key in (
            ("video_path", "video_sha256"),
            ("annotation_path", "annotation_sha256"),
        ):
            target = Path(row[path_key])
            expected_hash = row[hash_key].upper()
            if target.exists() and not args.force and sha256(target) == expected_hash:
                print(f"verified {target}")
                continue

            relative_url = f"{sequence}/{target.name}"
            url = urljoin(args.base_url.rstrip("/") + "/", relative_url)
            download_and_verify(url, target, expected_hash)
            print(f"downloaded and verified {target}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the audited RouteLens CAVIAR pilot subset."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/research/caviar-pilot-manifest.csv"),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def download_and_verify(url: str, target: Path, expected_hash: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "RouteLens/1.1"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out)
        actual_hash = sha256(partial)
        if actual_hash != expected_hash.upper():
            raise ValueError(
                f"SHA-256 mismatch for {url}: expected {expected_hash}, got {actual_hash}"
            )
        partial.replace(target)
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if __name__ == "__main__":
    raise SystemExit(main())
