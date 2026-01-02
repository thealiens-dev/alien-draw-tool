#!/usr/bin/env python3
import csv
import hashlib
import os
import sys

VERSION = "1.0.0"


def _out(key: str, value: str) -> None:
    """Print a stable, machine-parseable key=value line to stdout."""
    print(f"{key}={value}")


def main() -> int:
    # Require exactly one argument: 64 hex characters.
    if len(sys.argv) != 2:
        print("Usage: python3 . <64-hex-block-hash>  (or: python3 draw.py <64-hex-block-hash>)", file=sys.stderr)
        return 1

    block_hash = sys.argv[1].strip().lower()
    if len(block_hash) != 64 or any(c not in "0123456789abcdef" for c in block_hash):
        print("Error: block_hash must be 64 hex chars.", file=sys.stderr)
        return 1

    # Read snapshot CSV bytes from the same folder.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "participants.csv")

    if not os.path.isfile(csv_path):
        print(f"Error: missing participants.csv next to the tool: {csv_path}", file=sys.stderr)
        return 1

    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    # Compute snapshot hash and combined seed.
    snapshot_hash = hashlib.sha256(csv_bytes).hexdigest()
    seed_input = (block_hash + snapshot_hash).encode("utf-8")
    seed = hashlib.sha256(seed_input).hexdigest()

    # Parse participants and validate ticket coverage.
    rows: list[tuple[str, int, int]] = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {"username", "from_ticket", "to_ticket"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            print("Error: CSV must have headers: username,from_ticket,to_ticket", file=sys.stderr)
            return 1

        for row in reader:
            username = (row.get("username") or "").strip()
            if not username:
                print("Error: username cannot be empty.", file=sys.stderr)
                return 1

            try:
                from_ticket = int(row["from_ticket"])
                to_ticket = int(row["to_ticket"])
            except (ValueError, TypeError, KeyError):
                print("Error: from_ticket/to_ticket must be integers.", file=sys.stderr)
                return 1

            if from_ticket < 1 or to_ticket < from_ticket:
                print("Error: invalid ticket range (from_ticket must be >= 1 and <= to_ticket).", file=sys.stderr)
                return 1

            rows.append((username, from_ticket, to_ticket))

    if not rows:
        print("Error: participants.csv has no rows.", file=sys.stderr)
        return 1

    # Ensure ranges are contiguous and non-overlapping: 1..total_tickets.
    rows_sorted = sorted(rows, key=lambda r: r[1])
    if rows_sorted[0][1] != 1:
        print("Error: ticket ranges must start at 1.", file=sys.stderr)
        return 1

    prev_to = 0
    for username, from_ticket, to_ticket in rows_sorted:
        if from_ticket != prev_to + 1:
            print("Error: ticket ranges must be contiguous with no gaps/overlaps.", file=sys.stderr)
            return 1
        prev_to = to_ticket

    total_tickets = prev_to

    # Determine the winner ticket.
    winner_ticket = (int(seed, 16) % total_tickets) + 1

    # Find the winner range.
    winner_username = ""
    winner_range = ""
    for username, from_ticket, to_ticket in rows_sorted:
        if from_ticket <= winner_ticket <= to_ticket:
            winner_username = username
            winner_range = f"{from_ticket}-{to_ticket}"
            break

    if not winner_username:
        # This should not happen if CSV ranges are correct, but guard anyway.
        print("Error: winner ticket not found in any range (CSV ranges inconsistent).", file=sys.stderr)
        return 1

    # Print stable, machine-parseable outputs (key=value).
    _out("tool", "alien-draw-tool")
    _out("version", VERSION)
    _out("block_hash", block_hash)
    _out("participants_csv", os.path.basename(csv_path))
    _out("participants_csv_bytes", str(len(csv_bytes)))
    _out("participants_csv_sha256", snapshot_hash)
    _out("seed_sha256", seed)
    _out("total_tickets", str(total_tickets))
    _out("winner_ticket", str(winner_ticket))
    _out("winner_username", winner_username)
    _out("winner_ticket_range", winner_range)
    return 0


if __name__ == "__main__":
    sys.exit(main())