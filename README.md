# Alien Draw Tool

Deterministic and publicly verifiable draw mechanism used by **The Aliens**.

The tool selects exactly one winner based on:
- a public Bitcoin block hash
- a finalized participants snapshot (`participants.csv`)

Given the same inputs, the output is always identical and can be independently reproduced.

---

## Algorithm

```text
canonical_snapshot = normalize + sort participants by username
canonical_snapshot_hash = SHA256(canonical_snapshot bytes)
seed = SHA256(block_hash + canonical_snapshot_hash)
winner_ticket = (int(seed, 16) % total_tickets) + 1
```

The canonical snapshot is built from trimmed `username,ticket_count` rows sorted alphabetically (case-sensitive).
Ticket ranges are derived deterministically from this ordering; the winner is the participant whose range contains `winner_ticket`.

---

## Input format

```csv
username,ticket_count
john,10
bob,15
charlie,13
```

Rules:
- `ticket_count` must be a positive integer
- input order does not matter – entries may be unsorted
- `username` is treated as a generic identifier (trimmed only, case-sensitive)
- duplicate usernames are not allowed (the tool will fail)
- ticket ranges are derived deterministically from the canonical (sorted) snapshot
- `participants.csv` is not tracked in git (local, per-giveaway input)

An example file is provided as `participants.example.csv`.

---

## Usage

```bash
cp participants.example.csv participants.csv
python3 draw.py <BTC_BLOCK_HASH> [participants.csv]
```

---

## Example

Example run using a real Bitcoin block hash:

```bash
python3 draw.py 00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d participants.example.csv
```

Example output (values will be identical for the same inputs):

```text
tool=alien-draw-tool
version=1.0.0
block_hash=00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d
participants_csv=participants.example.csv
participants_file_bytes=<n>
participants_file_sha256=<sha256>
canonical_snapshot=username,ticket_count (normalized + sorted)
canonical_snapshot_bytes=<n>
canonical_snapshot_sha256=<sha256>
seed_sha256=<sha256>
total_tickets=38
winner_ticket=<n>
winner_username=<username>
winner_ticket_range=<from>-<to>
```

---

## Determinism

- no local randomness is used
- the Bitcoin block hash is an external, unpredictable source
- the canonical snapshot (normalized + sorted) is hashed before selection

Anyone can reproduce the result byte-for-byte using the same inputs.

---

Part of **Alien Tools**.