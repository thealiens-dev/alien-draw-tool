#!/usr/bin/env python3
import argparse
import csv
import hashlib
import http.client
import os
import socket
import sys
import urllib.error
import urllib.request

VERSION = "1.1.1"
PROJECT = "The Aliens"


def _out(key: str, value: str) -> None:
    """Print a stable, machine-parseable key=value line to stdout."""
    print(f"{key}={value}")

def _is_valid_block_hash(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _resolve_block_hash_from_height(height: int) -> tuple[str | None, int | None]:
    url = f"https://mempool.space/api/block-height/{height}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status = response.getcode()
            if status != 200:
                return None, status
            body = response.read().decode("utf-8", errors="replace").strip().lower()
    except urllib.error.HTTPError as exc:
        return None, exc.code
    except (urllib.error.URLError, http.client.RemoteDisconnected, socket.timeout):
        print("Error: failed to resolve block height via mempool.space (network error)", file=sys.stderr)
        return None, None

    if not _is_valid_block_hash(body):
        print("Error: provider returned invalid block hash", file=sys.stderr)
        return None, None

    return body, 200


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="alien-draw-tool",
        description="Deterministic draw with no rerolls, no discretion and a verifiable input list.",
    )
    parser.add_argument("participants_file", nargs="?", default="participants.csv")
    block_group = parser.add_mutually_exclusive_group(required=True)
    block_group.add_argument("--block-hash", help="64-hex Bitcoin block hash")
    block_group.add_argument("--block-height", type=int, help="Bitcoin block height (int)")
    parser.add_argument(
        "--mode",
        choices=("uniform", "weighted"),
        default="uniform",
        help="Draw mode: uniform (default, 1 ticket each) or weighted (CSV with ticket_count).",
    )
    args = parser.parse_args()

    block_source = "hash"
    block_hash = ""
    block_height = None

    if args.block_hash is not None:
        block_hash = args.block_hash.strip().lower()
        if not _is_valid_block_hash(block_hash):
            print("Error: block_hash must be 64 hex chars.", file=sys.stderr)
            return 1
    else:
        block_source = "height"
        block_height = args.block_height
        if block_height is None:
            print("Error: Provide --block-hash or --block-height", file=sys.stderr)
            return 1

    participants_filename = args.participants_file.strip()
    if not participants_filename:
        print("Error: participants CSV filename cannot be empty.", file=sys.stderr)
        return 1

    # Read snapshot CSV bytes from the same folder.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, participants_filename)

    if not os.path.isfile(csv_path):
        print(f"Error: missing {participants_filename} next to the tool: {csv_path}", file=sys.stderr)
        print(
            "Tip: copy participants-weighted.example.csv or participants-uniform.example.txt next to the tool "
            "(or pass a filename as the participants argument).",
            file=sys.stderr,
        )
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
    # Notes:
    # - input may be unsorted
    # - usernames are normalized (trim only; case-sensitive)
    # - duplicate usernames are not allowed (tool fails)
    # - canonical ordering is username ascending (case-sensitive)

    # Read and parse input as text.
    # Use utf-8-sig to tolerate UTF-8 BOM (common when CSVs come from Excel).
    # Initialize totals before try block
    totals: dict[str, int] = {}
    try:
        with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
            if args.mode == "weighted":
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
            else:
                first_line = True
                for line in f:
                    username = line.strip()
                    if not username:
                        continue
                    if first_line and username == "username":
                        first_line = False
                        continue
                    first_line = False
                    if "," in username:
                        print("Error: uniform mode expects one username per line (no commas).", file=sys.stderr)
                        return 1
                    if username in totals:
                        print(f"Error: duplicate username not allowed: {username}.", file=sys.stderr)
                        return 1
                    totals[username] = 1
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

    # Build deterministic ticket ranges from canonical ordering.
    rows_sorted: list[tuple[str, int, int]] = []
    current = 1
    for uname, tc in participants_sorted:
        from_ticket = current
        to_ticket = current + tc - 1
        rows_sorted.append((uname, from_ticket, to_ticket))
        current = to_ticket + 1

    total_tickets = current - 1

    status = "final"
    reason = ""

    if block_source == "height":
        resolved_hash, resolved_status = _resolve_block_hash_from_height(block_height)
        if resolved_status == 404:
            status = "pending"
            reason = "block_not_found_yet"
        elif resolved_status != 200:
            if resolved_status is not None:
                print(
                    f"Error: failed to resolve block height via mempool.space (status {resolved_status})",
                    file=sys.stderr,
                )
            return 1
        else:
            block_hash = resolved_hash or ""

    if status == "final":
        seed_input = (block_hash + canonical_snapshot_sha256).encode("utf-8")
        seed = hashlib.sha256(seed_input).hexdigest()

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
    _out("project", PROJECT)
    _out("tool", "alien-draw-tool")
    _out("version", VERSION)
    _out("status", status)
    _out("block_source", block_source)
    if block_source == "height":
        _out("block_height", str(block_height))
        _out("block_height_provider", "mempool.space")
    _out("mode", args.mode)
    if status == "pending":
        _out("reason", reason)
        _out("block_hash", "")
    else:
        _out("block_hash", block_hash)
    _out("participants_file", os.path.basename(csv_path))
    _out("canonical_snapshot", "username,ticket_count (normalized + sorted)")

    # Raw input file (auditing only - can differ by ordering/formatting)
    _out("participants_raw_file_bytes", str(len(csv_bytes)))
    _out("participants_raw_file_sha256", participants_file_hash)

    # Canonical snapshot (used for selection)
    _out("canonical_snapshot_bytes", str(len(canonical_csv_bytes)))
    _out("canonical_snapshot_sha256", canonical_snapshot_sha256)

    _out("total_tickets", str(total_tickets))
    if status == "final":
        _out("seed_sha256", seed)
        _out("winner_ticket", str(winner_ticket))
        _out("winner_username", winner_username)
        _out("winner_ticket_range", winner_range)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
