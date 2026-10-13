#!/usr/bin/env python3
"""Fetch and verify the two source-code snapshots used by the benchmark."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = TASK_ROOT / ".cache" / "upstream"

SNAPSHOTS = {
    "reference_simulator": {
        "commit": "6916101b6df55ca97f5522a999c0dc499d6e4362",
        "url": "https://github.com/FFroehlich/reference_simulator/archive/6916101b6df55ca97f5522a999c0dc499d6e4362.tar.gz",
        "sha256": "5a856950780b87bff58c7ec160bb3ef447e29450e42fb46f45b17cfc0942ad82",
    },
    "treatment_opt": {
        "commit": "62b25f5d4956e91c509d561c999c4cceb98a1081",
        "url": "https://github.com/Sandholm-Lab/treatment-opt-pancancer/archive/62b25f5d4956e91c509d561c999c4cceb98a1081.tar.gz",
        "sha256": "e142185b7a146cf877046bc44b18ba41ab921d98b5320591716890c10305756a",
    },
}


def fetch(name: str, metadata: dict[str, str]) -> dict[str, str | int]:
    target = CACHE_ROOT / f"{name}-{metadata['commit']}"
    marker = target / ".verified.json"
    if marker.exists():
        return json.loads(marker.read_text())

    with urllib.request.urlopen(metadata["url"], timeout=120) as response:
        payload = response.read()
    observed = hashlib.sha256(payload).hexdigest()
    if observed != metadata["sha256"]:
        raise RuntimeError(
            f"Checksum mismatch for {name}: expected {metadata['sha256']}, got {observed}"
        )

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        members = archive.getmembers()
        prefix = members[0].name.split("/", 1)[0]
        for member in members:
            if member.name != prefix and not member.name.startswith(prefix + "/"):
                raise RuntimeError(f"Unexpected archive path: {member.name}")
        archive.extractall(CACHE_ROOT, filter="data")

    extracted = CACHE_ROOT / prefix
    extracted.rename(target)
    record = {
        "name": name,
        "commit": metadata["commit"],
        "url": metadata["url"],
        "sha256": observed,
        "bytes": len(payload),
    }
    marker.write_text(json.dumps(record, indent=2) + "\n")
    return record


def main() -> None:
    records = [fetch(name, metadata) for name, metadata in SNAPSHOTS.items()]
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
