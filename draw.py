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
    # Args:
    #   1) block hash (64 hex)
    #   2) optional participants csv filename (default: participants.csv)
    if len(sys.argv) not in (2, 3):
        print(
            "Usage: python3 draw.py <64-hex-btc-block-hash> [participants.csv]",
            file=sys.stderr,
        )
        return 1

    block_hash = sys.argv[1].strip().lower()
    if len(block_hash) != 64 or any(c not in "0123456789abcdef" for c in block_hash):
        print("Error: block_hash must be 64 hex chars.", file=sys.stderr)
        return 1

    participants_filename = sys.argv[2].strip() if len(sys.argv) == 3 else "participants.csv"
    if not participants_filename:
        print("Error: participants CSV filename cannot be empty.", file=sys.stderr)
        return 1

    # Read snapshot CSV bytes from the same folder.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, participants_filename)

    if not os.path.isfile(csv_path):
        print(f"Error: missing {participants_filename} next to the tool: {csv_path}", file=sys.stderr)
        print("Tip: copy participants.example.csv to participants.csv (or pass a filename as 2nd arg).", file=sys.stderr)
        return 1

    with open(csv_path, "rb") as f:
        csv_bytes = f.read()
    # Hash of the raw input file bytes (exact file as provided).
    # Note: this can change if the input file differs in ordering or formatting.
    # Raw hash is printed for auditing only; it does not affect selection.
    # Selection uses the canonical snapshot hash computed later.
    participants_file_hash = hashlib.sha256(csv_bytes).hexdigest()

    # Compute snapshot hash and seed later from canonical participant data.

    # Parse participants and build deterministic ticket ranges.
    # Expected CSV headers: username,ticket_count
    # Notes:
    # - input may be unsorted
    # - usernames are normalized (trim only; case-sensitive)
    # - duplicate usernames are not allowed (tool fails)
    # - canonical ordering is username ascending (case-sensitive)

    # Read and parse CSV as text.
    # Use utf-8-sig to tolerate UTF-8 BOM (common when CSVs come from Excel).
    # Initialize totals before try block
    totals: dict[str, int] = {}
    try:
        with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            required = {"username", "ticket_count"}
            if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
                print(
                    "Error: CSV must have headers: username,ticket_count",
                    file=sys.stderr,
                )
                return 1

            # Aggregate ticket counts per normalized username.
            for row in reader:
                raw_username = (row.get("username") or "").strip()
                if not raw_username:
                    print("Error: username cannot be empty.", file=sys.stderr)
                    return 1

                # Normalize: trim whitespace only (case-sensitive username preserved).
                username = raw_username.strip()

                raw_tc = (row.get("ticket_count") or "").strip()
                if not raw_tc:
                    print(f"Error: ticket_count is empty for {username}.", file=sys.stderr)
                    return 1
                try:
                    ticket_count = int(raw_tc)
                except (ValueError, TypeError):
                    print(f"Error: ticket_count must be an integer for {username}.", file=sys.stderr)
                    return 1

                if ticket_count < 1:
                    print(f"Error: ticket_count must be >= 1 for {username}.", file=sys.stderr)
                    return 1

                if username in totals:
                    print(f"Error: duplicate username not allowed: {username}.", file=sys.stderr)
                    return 1

                totals[username] = ticket_count
    except UnicodeDecodeError:
        print(
            f"Error: cannot read participants file as UTF-8: {os.path.basename(csv_path)} "
            "(try saving it as UTF-8 or UTF-8 with BOM).",
            file=sys.stderr,
        )
        return 1

    if not totals:
        print(f"Error: participants file has no rows: {os.path.basename(csv_path)}", file=sys.stderr)
        return 1

    # Canonical ordering: lexicographic by username (case-sensitive).
    participants_sorted = sorted(totals.items(), key=lambda kv: kv[0])

    # Build canonical CSV bytes (used for snapshot hash) so ordering in the input file
    # does not change the result.
    canonical_lines = ["username,ticket_count\n"]
    for uname, tc in participants_sorted:
        canonical_lines.append(f"{uname},{tc}\n")
    canonical_csv_bytes = "".join(canonical_lines).encode("utf-8")

    # Canonical snapshot hash is computed from canonical bytes (trimmed + sorted).
    canonical_snapshot_sha256 = hashlib.sha256(canonical_csv_bytes).hexdigest()
    seed_input = (block_hash + canonical_snapshot_sha256).encode("utf-8")
    seed = hashlib.sha256(seed_input).hexdigest()

    # Build deterministic ticket ranges from canonical ordering.
    rows_sorted: list[tuple[str, int, int]] = []
    current = 1
    for uname, tc in participants_sorted:
        from_ticket = current
        to_ticket = current + tc - 1
        rows_sorted.append((uname, from_ticket, to_ticket))
        current = to_ticket + 1

    total_tickets = current - 1

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
    _out("participants_file", os.path.basename(csv_path))
    _out("canonical_snapshot", "username,ticket_count (normalized + sorted)")

    # Raw input file (auditing only - can differ by ordering/formatting)
    _out("participants_raw_file_bytes", str(len(csv_bytes)))
    _out("participants_raw_file_sha256", participants_file_hash)

    # Canonical snapshot (used for selection)
    _out("canonical_snapshot_bytes", str(len(canonical_csv_bytes)))
    _out("canonical_snapshot_sha256", canonical_snapshot_sha256)

    _out("seed_sha256", seed)
    _out("total_tickets", str(total_tickets))
    _out("winner_ticket", str(winner_ticket))
    _out("winner_username", winner_username)
    _out("winner_ticket_range", winner_range)
    return 0


if __name__ == "__main__":
    sys.exit(main())