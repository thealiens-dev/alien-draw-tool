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

### Single-winner case (N = 1)

```
This section explains the algorithm conceptually using round numbering starting from 1.
In the actual CLI output, all list-based fields (e.g. *_rounds) are zero-indexed.
This is a representation detail only – the algorithm itself operates in rounds 1..N.
```

```text
snapshot_1 = canonicalize(all participants)
hash_1 = SHA256(snapshot_1 bytes)                      # canonical_snapshot_sha256_rounds[1]
seed_1 = SHA256(block_hash + hash_1)                   # seeds_sha256[1]
ticket_1 = (int(seed_1, 16) % total_tickets_1) + 1     # total_tickets_rounds[1]
winner_1 = the username whose ticket range contains ticket_1
```

### General case (N > 1)

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
This snippet shows the format only. For canonical, reproducible demos, use the full fixtures in `tests/fixtures/`.

- `ticket_count` must be an integer >= 1
- input order does not matter – entries may be unsorted
- `username` is treated as a generic identifier (trimmed only, case-sensitive)
- duplicate usernames are not allowed (the tool will fail)
- ticket ranges are derived deterministically from the canonical (sorted) snapshot

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
This example shows the minimal file format only. For real verification and reproducible proofs, always use the full canonical fixtures shipped with the repository (see `tests/fixtures/vector-equal.txt`).

### weighted

Requires `--mode weighted` and a CSV file with the `username,ticket_count` header.

```csv
username,ticket_count
john,10
bob,15
charlie,13
```
This example shows the format only. Canonical demo data is provided in `tests/fixtures/vector-weighted.csv`.

Regardless of mode, the canonical snapshot is always built with the standard header and sorted.
At least two unique usernames are required.

---

## Usage

```bash
# Equal mode (one username per line, canonical demo using full fixture list)
python3 draw.py --block-hash <BTC_BLOCK_HASH> --mode equal --winners 1 tests/fixtures/vector-equal.txt
```

```bash
# Weighted mode (CSV with ticket_count, canonical demo using full fixture list)
python3 draw.py --block-height <BLOCK_HEIGHT> --mode weighted --winners 1 tests/fixtures/vector-weighted.csv
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

Canonical demo using the shipped equal-mode fixture (100 participants).

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
participants_raw_file_bytes=1309
participants_raw_file_sha256=f9586b69592a447101d20b6fba39a0790b404af19c23a0ab6149084780120356
winners_count=1
winners_usernames=binary-beacon
winners_tickets=44
winners_ticket_ranges=44-44
total_tickets_rounds=100
canonical_snapshot_sha256_rounds=7d407a2e2ac897526d972856e1b2efa3318e86e8a4fe52eb3be4faf3e72abc0d
canonical_snapshot_bytes_rounds=1522
seeds_sha256=3899e115af6f863ffada03fcb8aba47ef852e91b1eeaab1593bd9b983d6f31a7
```

---

## Example (weighted, secondary)

Canonical demo using the shipped weighted-mode fixture (100 participants).

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
participants_raw_file_bytes=1532
participants_raw_file_sha256=031fc431184e7bae0ead5220c1cd0ea3ae34c2be6e953ab74c6b74cf7612005c
winners_count=1
winners_usernames=ancient-circuit
winners_tickets=85
winners_ticket_ranges=77-85
total_tickets_rounds=550
canonical_snapshot_sha256_rounds=e2aab16d8dc600a074fb28cd095bfb138cce0b80064300f7efb2be29092502a6
canonical_snapshot_bytes_rounds=1532
seeds_sha256=dffa7821ec8aefa63afc0ae1d28ab2c8d684a3f3e114bea10ee23006ff597b36
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
