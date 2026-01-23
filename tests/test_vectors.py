#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS_PATH = ROOT / "tests" / "test_vectors.json"


def parse_output(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def run_vector(vector: dict) -> list[str]:
    name = vector.get("name", "(unnamed)")
    input_data = vector["input"]
    expected = vector["expected"]

    cmd = ["python3", "draw.py"]
    block_source = input_data["block_source"]
    if block_source == "hash":
        cmd += ["--block-hash", input_data["block_hash"]]
    elif block_source == "height":
        cmd += ["--block-height", str(input_data["block_height"])]
    else:
        return [f"{name}: unknown block_source {block_source}"]

    cmd += [input_data["participants_file"], "--mode", input_data["mode"]]

    # --winners is required in 2.0.0
    winners = input_data.get("winners", 1)
    cmd += ["--winners", str(winners)]

    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    output = parse_output(result.stdout)

    errors: list[str] = []
    expected_status = expected.get("status")
    if expected_status == "ok":
        if result.returncode != 0:
            errors.append(f"{name}: expected exit code 0, got {result.returncode}")
        if output.get("status") != "final":
            errors.append(f"{name}: expected status=final, got {output.get('status')}")
    elif expected_status == "pending":
        if result.returncode != 2:
            errors.append(f"{name}: expected exit code 2, got {result.returncode}")
        if output.get("status") != "pending":
            errors.append(f"{name}: expected status=pending, got {output.get('status')}")
    else:
        errors.append(f"{name}: expected status must be ok or pending")

    if output.get("block_source") != block_source:
        errors.append(f"{name}: block_source mismatch")

    if output.get("mode") != input_data["mode"]:
        errors.append(f"{name}: mode mismatch")

    if block_source == "height":
        if output.get("block_height") != str(input_data["block_height"]):
            errors.append(f"{name}: block_height mismatch")
        if output.get("block_height_provider") != "mempool.space":
            errors.append(f"{name}: block_height_provider mismatch")

    if "block_hash" in input_data:
        if output.get("block_hash") != input_data["block_hash"]:
            errors.append(f"{name}: block_hash mismatch")

    for key, value in expected.items():
        if key in ("status", "reason"):
            continue
        if output.get(key) != value:
            errors.append(f"{name}: {key} mismatch (expected={value}, got={output.get(key)})")

    if expected_status == "pending":
        if output.get("reason") != expected.get("reason"):
            errors.append(f"{name}: reason mismatch")
        # For pending, verify round 1 preview fields exist
        pending_required = [
            "winners_count",
            "total_tickets_rounds",
            "canonical_snapshot_sha256_rounds",
            "canonical_snapshot_bytes_rounds",
        ]
        for key in pending_required:
            if key not in output:
                errors.append(f"{name}: missing pending preview field {key}")
    else:
        # For status=ok, verify required 2.0.0 list-based fields exist
        required_fields = [
            "winners_count",
            "winners_usernames",
            "winners_tickets",
            "winners_ticket_ranges",
            "total_tickets_rounds",
            "canonical_snapshot_sha256_rounds",
            "canonical_snapshot_bytes_rounds",
            "seeds_sha256",
        ]
        for key in required_fields:
            if key not in output:
                errors.append(f"{name}: missing required field {key}")

    if errors and result.stderr.strip():
        errors.append(f"{name}: stderr: {result.stderr.strip()}")

    return errors


def main() -> int:
    with VECTORS_PATH.open("r", encoding="utf-8") as f:
        vectors = json.load(f)

    all_errors: list[str] = []
    for vector in vectors:
        all_errors.extend(run_vector(vector))

    if all_errors:
        for err in all_errors:
            print(err)
        return 1

    print("All test vectors passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
