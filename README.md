# Alien Draw Tool

Deterministic and publicly verifiable random picker based on Bitcoin block entropy, used by **The Aliens**.
This tool selects one or more winners in a reproducible way that anyone can independently verify.

Winner selection is based on:
- a public Bitcoin block hash
- a finalized participants snapshot (`participants.csv` by default)

Given the same inputs, the output is always identical and can be independently reproduced.

## Requirements

- Python 3.9+
- Network access to mempool.space (only when using `--block-height`)

---

## Algorithm

### Single-winner example (winners_count = 1)

```text
snapshot_1 = canonicalize(all participants)
hash_1 = SHA256(snapshot_1 bytes)                      # canonical_snapshot_sha256_rounds[1]
seed_1 = SHA256(block_hash + hash_1)                   # seeds_sha256[1]
ticket_1 = (int(seed_1, 16) % total_tickets_1) + 1     # total_tickets_rounds[1]
winner_1 = the username whose ticket range contains ticket_1
```

### General case (winners_count = N)

For round i = 1..N:

```text
participants_remaining_1 = all participants
participants_remaining_i = participants_remaining_(i-1) minus winner_(i-1)     (for i > 1)

snapshot_i = canonicalize(participants_remaining_i)
hash_i = SHA256(snapshot_i bytes)                      # canonical_snapshot_sha256_rounds[i]
seed_i = SHA256(block_hash + hash_i)                   # seeds_sha256[i]
ticket_i = (int(seed_i, 16) % total_tickets_i) + 1     # total_tickets_rounds[i]
winner_i = the username whose ticket range contains ticket_i
```

In equal mode, each participant has ticket_count=1.
In weighted mode, ticket_count comes from the CSV input.

The canonical snapshot is built from trimmed `username,ticket_count` rows (whitespace trimmed only, case-sensitive) sorted lexicographically by `username` (standard string order - effectively alphabetical for typical identifiers).
Sorting happens *before* hashing, which means the input file may be in any order without affecting the result.

The canonical snapshot always includes the header row `username,ticket_count`; implementations that accept header-less input must prepend this header before canonicalization to remain compatible.

---

## Input format

This section describes the weighted mode input format (CSV with `ticket_count`).
In equal mode, all participants implicitly receive exactly one ticket.

```csv
username,ticket_count
john,10
bob,15
charlie,13
```

- `ticket_count` must be an integer >= 1
- input order does not matter – entries may be unsorted
- `username` is treated as a generic identifier (trimmed only, case-sensitive)
- duplicate usernames are not allowed (the tool will fail)
- ticket ranges are derived deterministically from the canonical (sorted) snapshot

Example files are provided as `participants-weighted.example.csv` and `participants-equal.example.txt`.

---

## Modes

Two modes are available: **equal** and **weighted**. The `--mode` flag is required.

- **equal**: each participant has exactly the same weight (1 ticket each)
- **weighted**: participant weights come from `ticket_count` column in CSV

### equal

One username per line (no commas). Each participant gets exactly 1 ticket.
The file extension is not validated; only the content format matters.

```text
john
bob
charlie
```

### weighted

Requires `--mode weighted` and a CSV file with the `username,ticket_count` header.

```csv
username,ticket_count
john,10
bob,15
charlie,13
```

Regardless of mode, the canonical snapshot is always built with the standard header and sorted.
At least two unique usernames are required.

---

## Usage

```bash
# Equal mode (one username per line)
python3 draw.py --block-hash <BTC_BLOCK_HASH> --mode equal --winners 1 participants-equal.example.txt
```

```bash
# Weighted mode (CSV with ticket_count)
python3 draw.py --block-height <BLOCK_HEIGHT> --mode weighted --winners 1 participants-weighted.example.csv
```

- Provide exactly one of `--block-hash` or `--block-height`.
- `--mode` is required: use `equal` for one username per line, or `weighted` for CSV with `ticket_count`.
- When using `--block-height`, the tool resolves the canonical block hash via mempool.space and prints it in the proof.
- Future block height returns `status=pending` with exit code 2. `status=final` uses exit code 0; hard errors use exit code 1.
- If the participants file argument is omitted, the tool defaults to `participants.csv` next to the script.
- `--winners N` is required (introduced in 2.0.0; must be >= 1 and <= participants_count - 1).
- Output fields are always list-based (pipe-delimited), even when `--winners 1`.
- `participants_count` is the number of unique usernames after normalization (trim only, case-sensitive) and duplicate checks; it is used to validate `--winners <= participants_count - 1`.

## Multiple winners

For winners > 1, each round recomputes the canonical snapshot from the remaining participants; seed for each round is SHA256(block_hash + canonical_snapshot_sha256_round_i).
Mode is preserved across rounds: equal mode keeps 1 ticket per participant, weighted mode uses ticket_count when rebuilding ranges.
Older proofs (<=1.1.3) used single-winner fields; current versions use only list-based fields.

---

## Example (equal, primary)

Example run using equal mode:

```bash
python3 draw.py --block-hash 00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d --mode equal --winners 1 tests/fixtures/vector-equal.txt
```

Example output:

```text
project=The Aliens
tool=alien-draw-tool
version=2.0.0
status=final
block_source=hash
mode=equal
block_hash=00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d
participants_file=vector-equal.txt
participants_count=100
canonical_snapshot=username,ticket_count (normalized + sorted)
participants_raw_file_bytes=1409
participants_raw_file_sha256=4f21575ee279c0025d3e9112fbf0e334f4ced8d3ea8ec031c29cf2ff326f2343
winners_count=1
winners_usernames=@carbon-echo
winners_tickets=90
winners_ticket_ranges=90-90
total_tickets_rounds=100
canonical_snapshot_sha256_rounds=0aa72e324420b5b7674528e0c61abd1fc0b4132dcf47d8d26bf044b33888351f
canonical_snapshot_bytes_rounds=1622
seeds_sha256=672f59548cd61b97fec5fbfc4083b2849c945ca3375b035ac9d82ff1d66fa791
```

---

## Example (weighted, secondary)

Example run using weighted mode:

```bash
python3 draw.py --block-hash 00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d --mode weighted --winners 1 tests/fixtures/vector-weighted.csv
```

Example output:

```text
project=The Aliens
tool=alien-draw-tool
version=2.0.0
status=final
block_source=hash
mode=weighted
block_hash=00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d
participants_file=vector-weighted.csv
participants_count=100
canonical_snapshot=username,ticket_count (normalized + sorted)
participants_raw_file_bytes=1632
participants_raw_file_sha256=6459f3441742dddb0be650d1c13b6ef56e04a6c90f1712d62e649b2039d7a60b
winners_count=1
winners_usernames=@ancient-beacon
winners_tickets=67
winners_ticket_ranges=66-67
total_tickets_rounds=550
canonical_snapshot_sha256_rounds=741ee72cdbf6516bc552135ad5b4bb4ae5240ef722240b8c78a289b91e8574dd
canonical_snapshot_bytes_rounds=1632
seeds_sha256=d53a7c824741320cc0584a12d6ba97238f4286593bf75f0945e37fd2cacc5e28
```

---


## Determinism

- no local randomness is used
- the Bitcoin block hash is an external, unpredictable source
- the canonical snapshot (normalized + sorted) is hashed before selection
- All list-based output fields are pipe-delimited (`|`). Usernames must not contain the `|` character.

Selection depends on the canonical snapshot hash; the raw participants file hash is printed for auditing purposes only.

Anyone can reproduce the result byte-for-byte using the same inputs.

When resolving a block height, the provider only maps height to hash; selection always uses the hash.
If the provider is unavailable, provide the block hash directly via --block-hash.

The CLI is the reference implementation; the proof output (key=value) is stable.
Any change to the proof format requires a conscious decision and a changelog entry.

---

## Test Vectors

Golden test vectors lock the current deterministic outputs and prevent accidental changes.
They are the source of truth for expected results.
Test vectors include a multi-winner case (winners=3) to lock multi-round behavior.

Run locally:

```bash
python3 tests/test_vectors.py
```

If output changes are intentional, update `tests/test_vectors.json` and record the change in `CHANGELOG.md`.

---

Part of **Alien Tools**.

## License

Apache License 2.0
