# Alien Draw Tool

Deterministic and publicly verifiable draw mechanism used by **The Aliens**.

The tool selects exactly one winner based on:
- a public Bitcoin block hash
- a finalized participants snapshot (`participants.csv` by default)

Given the same inputs, the output is always identical and can be independently reproduced.

---

## Algorithm

```text
canonical_snapshot = normalize + sort participants lexicographically by username
canonical_snapshot_sha256 = SHA256(canonical_snapshot bytes)
seed = SHA256(block_hash + canonical_snapshot_sha256)
winner_ticket = (int(seed, 16) % total_tickets) + 1
```

The canonical snapshot is built from trimmed `username,ticket_count` rows (whitespace trimmed only, case-sensitive) sorted lexicographically by `username` (standard string order - effectively alphabetical for typical identifiers).  
Sorting happens *before* hashing, which means the input file may be in any order without affecting the result.

The canonical snapshot always includes the header row username,ticket_count; implementations that accept header-less input must prepend this header before canonicalization to remain compatible.

---

## Input format

This section describes the weighted mode input format (CSV with `ticket_count`).
In uniform mode, all participants implicitly receive exactly one ticket.

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

Example files are provided as `participants-weighted.example.csv` and `participants-uniform.example.txt`.

---

## Modes

The CLI supports two explicit draw modes:

Modes:
- weighted: CSV with username,ticket_count header (default: No)
- uniform: One username per line (no commas); optional first line username is ignored (default: Yes)

### weighted

Weighted draws require a CSV file with the `username,ticket_count` header.

```csv
username,ticket_count
john,10
bob,15
charlie,13
```

### uniform (default)

Uniform draws require one username per line (no commas). Each participant gets exactly 1 ticket. A single
header line `username` is allowed and ignored if present.
The file extension is not validated; only the content format matters.

```text
@alice
@bob
@charlie
```

Regardless of mode, the canonical snapshot is always built with the standard header and sorted.
At least two unique usernames are required.

---

## Usage

```bash
# Weighted mode (CSV with ticket_count)
python3 draw.py --block-hash <BTC_BLOCK_HASH> --mode weighted participants-weighted.example.csv
```

```bash
# Uniform mode (one username per line)
python3 draw.py --block-height <BLOCK_HEIGHT> --mode uniform participants-uniform.example.txt
```

Notes:
- Provide exactly one of `--block-hash` or `--block-height`.
- The default mode is uniform. CSV files with `ticket_count` require `--mode weighted`.
- When using `--block-height`, the tool resolves the canonical block hash via mempool.space and prints it in the proof.
- Future block height returns `status=pending` with exit code 2. `status=final` uses exit code 0; hard errors use exit code 1.
- If the participants file argument is omitted, the tool defaults to `participants.csv` next to the script.

---

## Example (uniform, primary)

Example run using uniform mode:

```bash
python3 draw.py --block-hash 00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d --mode uniform tests/fixtures/vector-uniform.txt
```

Example output:

```text
project=The Aliens
tool=alien-draw-tool
version=1.1.1
status=final
block_source=hash
mode=uniform
block_hash=00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d
participants_file=vector-uniform.txt
canonical_snapshot=username,ticket_count (normalized + sorted)
participants_raw_file_bytes=1409
participants_raw_file_sha256=4f21575ee279c0025d3e9112fbf0e334f4ced8d3ea8ec031c29cf2ff326f2343
canonical_snapshot_bytes=1622
canonical_snapshot_sha256=0aa72e324420b5b7674528e0c61abd1fc0b4132dcf47d8d26bf044b33888351f
seed_sha256=672f59548cd61b97fec5fbfc4083b2849c945ca3375b035ac9d82ff1d66fa791
total_tickets=100
winner_ticket=90
winner_username=@carbon-echo
winner_ticket_range=90-90
```

---

## Example (weighted, secondary)

Example run using weighted mode:

```bash
python3 draw.py --block-hash 00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d --mode weighted tests/fixtures/vector-weighted.csv
```

Example output:

```text
project=The Aliens
tool=alien-draw-tool
version=1.1.1
status=final
block_source=hash
mode=weighted
block_hash=00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d
participants_file=vector-weighted.csv
canonical_snapshot=username,ticket_count (normalized + sorted)
participants_raw_file_bytes=1632
participants_raw_file_sha256=6459f3441742dddb0be650d1c13b6ef56e04a6c90f1712d62e649b2039d7a60b
canonical_snapshot_bytes=1632
canonical_snapshot_sha256=741ee72cdbf6516bc552135ad5b4bb4ae5240ef722240b8c78a289b91e8574dd
seed_sha256=d53a7c824741320cc0584a12d6ba97238f4286593bf75f0945e37fd2cacc5e28
total_tickets=550
winner_ticket=67
winner_username=@ancient-beacon
winner_ticket_range=66-67
```

---


## Determinism

- no local randomness is used
- the Bitcoin block hash is an external, unpredictable source
- the canonical snapshot (normalized + sorted) is hashed before selection

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

Run locally:

```bash
python3 tests/test_vectors.py
```

If output changes are intentional, update `tests/test_vectors.json` and record the change in `CHANGELOG.md`.

---

Part of **Alien Tools**.

## License

Apache License 2.0
