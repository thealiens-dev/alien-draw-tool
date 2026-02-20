#!/usr/bin/env python3
"""
Helper script to regenerate test_vectors.json expected values from current draw.py output.
Run this after making intentional changes to the proof format.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS_PATH = ROOT / "tests" / "test_vectors.json"

# Fields to capture in expected (for status=ok)
EXPECTED_FIELDS_OK = [
    "participants_count",
    "winners_count",
    "winners_usernames",
    "winners_tickets",
    "winners_ticket_ranges",
    "total_tickets_rounds",
    "canonical_snapshot_sha256_rounds",
    "canonical_snapshot_bytes_rounds",
    "seeds_sha256",
]

# Fields to capture in expected (for status=pending)
EXPECTED_FIELDS_PENDING = [
    "block_hash",
    "reason",
    "participants_count",
    "winners_count",
    "total_tickets_rounds",
    "canonical_snapshot_sha256_rounds",
    "canonical_snapshot_bytes_rounds",
]


def parse_output(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def regenerate_vector(vector: dict) -> dict:
    name = vector.get("name", "(unnamed)")
    input_data = vector["input"]

    cmd = ["python3", "draw.py"]
    block_source = input_data["block_source"]
    if block_source == "hash":
        cmd += ["--block-hash", input_data["block_hash"]]
    elif block_source == "height":
        cmd += ["--block-height", str(input_data["block_height"])]
    else:
        print(f"WARNING: {name}: unknown block_source {block_source}", file=sys.stderr)
        return vector

    cmd += [
        input_data["participants_file"],
        "--ticket-distribution",
        input_data["ticket_distribution"],
    ]

    # --winners is required in 2.0.0
    winners = input_data.get("winners", 1)
    cmd += ["--winners", str(winners)]

    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    output = parse_output(result.stdout)

    status = output.get("status")

    if status == "final":
        new_expected = {"status": "ok"}
        for key in EXPECTED_FIELDS_OK:
            if key in output:
                new_expected[key] = output[key]
    elif status == "pending":
        new_expected = {"status": "pending"}
        for key in EXPECTED_FIELDS_PENDING:
            if key in output:
                new_expected[key] = output[key]
    else:
        print(f"WARNING: {name}: unexpected status {status}", file=sys.stderr)
        if result.stderr.strip():
            print(f"  stderr: {result.stderr.strip()}", file=sys.stderr)
        return vector

    vector["expected"] = new_expected
    print(f"Regenerated: {name}")
    return vector


def main() -> int:
    with VECTORS_PATH.open("r", encoding="utf-8") as f:
        vectors = json.load(f)

    # Ensure all vectors have winners in input
    for vector in vectors:
        if "winners" not in vector["input"]:
            vector["input"]["winners"] = 1

    regenerated = [regenerate_vector(v) for v in vectors]

    with VECTORS_PATH.open("w", encoding="utf-8") as f:
        json.dump(regenerated, f, indent=2)
        f.write("\n")

    print(f"\nRegenerated {len(regenerated)} vectors to {VECTORS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
