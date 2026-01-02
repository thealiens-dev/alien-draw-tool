#!/usr/bin/env python3
import csv
import hashlib
import os
import sys

def main() -> int:
    # Require exactly one argument: 64 hex characters.
    if len(sys.argv) != 2:
        print("Usage: python3 draw.py <64-hex-block-hash>", file=sys.stderr)
        return 1

    block_hash = sys.argv[1].strip().lower()
    if len(block_hash) != 64 or any(c not in "0123456789abcdef" for c in block_hash):
        print("Error: block_hash must be 64 hex chars.", file=sys.stderr)
        return 1

    # Read snapshot CSV bytes from the same folder.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "participants.csv")

    if not os.path.isfile(csv_path):
        print(f"Error: missing participants.csv next to draw.py: {csv_path}", file=sys.stderr)
        return 1

    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    # Compute snapshot hash and combined seed.
    snapshot_hash = hashlib.sha256(csv_bytes).hexdigest()
    seed_input = (block_hash + snapshot_hash).encode("utf-8")
    seed = hashlib.sha256(seed_input).hexdigest()

    # Parse participants and compute total tickets.
    rows = []
    total_tickets = 0
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {"username", "from_ticket", "to_ticket"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            print("Error: CSV must have headers: username,from_ticket,to_ticket", file=sys.stderr)
            return 1

        for row in reader:
            try:
                from_ticket = int(row["from_ticket"])
                to_ticket = int(row["to_ticket"])
            except (ValueError, TypeError):
                print("Error: from_ticket/to_ticket must be integers.", file=sys.stderr)
                return 1

            if from_ticket < 1 or to_ticket < from_ticket:
                print("Error: invalid ticket range (from_ticket must be >= 1 and <= to_ticket).", file=sys.stderr)
                return 1

            rows.append((row["username"], from_ticket, to_ticket))
            if to_ticket > total_tickets:
                total_tickets = to_ticket

    if total_tickets <= 0 or not rows:
        print("Error: no valid tickets found in participants.csv", file=sys.stderr)
        return 1

    # Determine the winner ticket.
    winner_ticket = (int(seed, 16) % total_tickets) + 1

    # Find the winner range.
    winner_username = ""
    winner_range = ""
    for username, from_ticket, to_ticket in rows:
        if from_ticket <= winner_ticket <= to_ticket:
            winner_username = username
            winner_range = f"{from_ticket}-{to_ticket}"
            break

    if not winner_username:
        # This should not happen if CSV ranges are correct, but guard anyway.
        print("Error: winner ticket not found in any range (CSV ranges inconsistent).", file=sys.stderr)
        return 1

    # Print labeled outputs in order for clarity.
    print(f"block_hash (BTC block): {block_hash}")
    print(f"snapshot_hash_csv (sha256 of participants.csv): {snapshot_hash}")
    print(f"seed (sha256(block_hash+snapshot_hash_csv)): {seed}")
    print(f"total_tickets: {total_tickets}")
    print(f"winner_ticket: {winner_ticket}")
    print(f"winner_username: {winner_username}")
    print(f"winner_range: {winner_range}")
    return 0

if __name__ == "__main__":
    sys.exit(main())