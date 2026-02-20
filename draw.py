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
from typing import Optional

VERSION = "2.0.1"
PROJECT = "The Aliens"


def _out(key: str, value: str) -> None:
    """Print a stable, machine-parseable key=value line to stdout."""
    print(f"{key}={value}")

def _is_valid_block_hash(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _resolve_block_hash_from_height(height: int) -> tuple[Optional[str], Optional[int]]:
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


def build_ranges(participants_sorted: list[tuple[str, int]]) -> tuple[list[tuple[str, int, int]], int]:
    rows_sorted: list[tuple[str, int, int]] = []
    current = 1
    for uname, tc in participants_sorted:
        from_ticket = current
        to_ticket = current + tc - 1
        rows_sorted.append((uname, from_ticket, to_ticket))
        current = to_ticket + 1
    total_tickets = current - 1
    return rows_sorted, total_tickets


def build_canonical_csv_bytes(participants_sorted: list[tuple[str, int]]) -> bytes:
    canonical_lines = ["username,ticket_count\n"]
    for uname, tc in participants_sorted:
        canonical_lines.append(f"{uname},{tc}\n")
    return "".join(canonical_lines).encode("utf-8")


def pick_winner(
    seed_hex: str, rows_sorted: list[tuple[str, int, int]], total_tickets: int
) -> tuple[str, int, str]:
    winner_ticket = (int(seed_hex, 16) % total_tickets) + 1
    winner_username = ""
    winner_range = ""
    for username, from_ticket, to_ticket in rows_sorted:
        if from_ticket <= winner_ticket <= to_ticket:
            winner_username = username
            winner_range = f"{from_ticket}-{to_ticket}"
            break
    return winner_username, winner_ticket, winner_range


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
        "--ticket-distribution",
        metavar="<equal|weighted>",
        choices=("equal", "weighted"),
        required=True,
        help="Defines how raffle tickets are distributed among participants.",
    )
    parser.add_argument(
        "--winners",
        type=int,
        required=True,
        help="Number of winners. Must be >= 1 and <= participants_count - 1.",
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
            "Tip: copy participants-weighted.example.csv or participants-equal.example.txt next to the tool"
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
            if args.ticket_distribution == "weighted":
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
                        print(
                            "Error: ticket distribution 'equal' expects one username per line (no commas). "
                            "This looks like a weighted CSV — did you mean to use --ticket-distribution weighted?",
                            file=sys.stderr,
                        )
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
    if len(totals) < 2:
        print(
            f"Error: participants file must include at least two usernames: {os.path.basename(csv_path)}",
            file=sys.stderr,
        )
        return 1
    if args.winners < 1:
        print("Error: winners must be >= 1.", file=sys.stderr)
        return 1
    if args.winners > len(totals) - 1:
        print("Error: winners must be <= participants_count - 1.", file=sys.stderr)
        return 1

    participants_count = len(totals)

    # Canonical ordering: lexicographic by username (case-sensitive).
    participants_sorted = sorted(totals.items(), key=lambda kv: kv[0])

    # Build canonical CSV bytes (used for snapshot hash) so ordering in the input file
    # does not change the result.
    canonical_csv_bytes = build_canonical_csv_bytes(participants_sorted)

    # Canonical snapshot hash is computed from canonical bytes (trimmed + sorted).
    canonical_snapshot_sha256 = hashlib.sha256(canonical_csv_bytes).hexdigest()

    # Build deterministic ticket ranges from canonical ordering.
    rows_sorted, total_tickets = build_ranges(participants_sorted)
    total_tickets_full = total_tickets

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

        winners_usernames: list[str] = []
        winners_tickets: list[int] = []
        winners_ranges: list[str] = []
        seeds: list[str] = [seed]
        total_tickets_rounds: list[int] = [total_tickets_full]
        canonical_snapshot_sha256_rounds: list[str] = [canonical_snapshot_sha256]
        canonical_snapshot_bytes_rounds: list[int] = [len(canonical_csv_bytes)]

        remaining_participants = participants_sorted[:]

        winner_username, winner_ticket, winner_range = pick_winner(seed, rows_sorted, total_tickets)
        if not winner_username:
            # This should not happen if CSV ranges are correct, but guard anyway.
            print("Error: winner ticket not found in any range (CSV ranges inconsistent).", file=sys.stderr)
            return 1
        winners_usernames.append(winner_username)
        winners_tickets.append(winner_ticket)
        winners_ranges.append(winner_range)

        remaining_participants = [
            (uname, tc) for uname, tc in remaining_participants if uname != winner_username
        ]

        if args.winners > 1:
            for i in range(2, args.winners + 1):
                remaining_sorted = sorted(remaining_participants, key=lambda kv: kv[0])
                rows_sorted, total_tickets = build_ranges(remaining_sorted)
                total_tickets_rounds.append(total_tickets)
                canonical_csv_bytes_round = build_canonical_csv_bytes(remaining_sorted)
                canonical_snapshot_bytes_rounds.append(len(canonical_csv_bytes_round))
                canonical_snapshot_sha256_round = hashlib.sha256(canonical_csv_bytes_round).hexdigest()
                canonical_snapshot_sha256_rounds.append(canonical_snapshot_sha256_round)
                seed_i_input = (block_hash + canonical_snapshot_sha256_round).encode("utf-8")
                seed_i = hashlib.sha256(seed_i_input).hexdigest()
                seeds.append(seed_i)
                next_username, next_ticket, next_range = pick_winner(
                    seed_i, rows_sorted, total_tickets
                )
                if not next_username:
                    print(
                        "Error: winner ticket not found in any range (CSV ranges inconsistent).",
                        file=sys.stderr,
                    )
                    return 1
                winners_usernames.append(next_username)
                winners_tickets.append(next_ticket)
                winners_ranges.append(next_range)
                remaining_participants = [
                    (uname, tc) for uname, tc in remaining_participants if uname != next_username
                ]

    # Print stable, machine-parseable outputs (key=value).
    _out("project", PROJECT)
    _out("tool", "alien-draw-tool")
    _out("version", VERSION)
    _out("status", status)
    _out("block_source", block_source)
    if block_source == "height":
        _out("block_height", str(block_height))
        _out("block_height_provider", "mempool.space")
    _out("ticketDistribution", args.ticket_distribution)
    if status == "pending":
        _out("reason", reason)
        _out("block_hash", "")
    else:
        _out("block_hash", block_hash)
    _out("participants_file", os.path.basename(csv_path))
    _out("participants_count", str(participants_count))
    _out("canonical_snapshot", "username,ticket_count (normalized + sorted)")

    # Raw input file (auditing only - can differ by ordering/formatting)
    _out("participants_raw_file_bytes", str(len(csv_bytes)))
    _out("participants_raw_file_sha256", participants_file_hash)

    if status == "final":
        _out("winners_count", str(args.winners))
        _out("winners_usernames", "|".join(winners_usernames))
        _out("winners_tickets", "|".join(str(t) for t in winners_tickets))
        _out("winners_ticket_ranges", "|".join(winners_ranges))
        _out("total_tickets_rounds", "|".join(str(t) for t in total_tickets_rounds))
        _out("canonical_snapshot_sha256_rounds", "|".join(canonical_snapshot_sha256_rounds))
        _out("canonical_snapshot_bytes_rounds", "|".join(str(n) for n in canonical_snapshot_bytes_rounds))
        _out("seeds_sha256", "|".join(seeds))
        return 0
    else:
        # pending - preview for round 1 only (no seeds, no winners)
        _out("winners_count", str(args.winners))
        _out("total_tickets_rounds", str(total_tickets_full))
        _out("canonical_snapshot_sha256_rounds", canonical_snapshot_sha256)
        _out("canonical_snapshot_bytes_rounds", str(len(canonical_csv_bytes)))
        return 2


if __name__ == "__main__":
    sys.exit(main())
