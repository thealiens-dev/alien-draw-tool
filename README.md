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

This section describes the `weighted` mode input format (CSV with `ticket_count`).
In `uniform` mode, all participants implicitly receive exactly one ticket.

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

An example file is provided as `participants.example.csv`.

---

## Modes

The CLI supports two explicit draw modes:

| Mode | Input format | Default |
| --- | --- | --- |
| uniform | One username per line (no commas); optional first line `username` is ignored | Yes |
| weighted | CSV with `username,ticket_count` header | No |

### weighted

Weighted draws require a CSV file with the `username,ticket_count` header.

### uniform (default)

Uniform draws require one username per line (no commas). Each participant gets exactly 1 ticket. A single
header line `username` is allowed and ignored if present.

```text
@alice
@bob
@charlie
```

Regardless of mode, the canonical snapshot is always built with the standard header and sorted.

---

## Usage

```bash
# Run with an explicit participants file
python3 draw.py <BTC_BLOCK_HASH> participants.example.csv --mode weighted
```

```bash
# Uniform mode (one username per line)
python3 draw.py <BTC_BLOCK_HASH> participants.txt --mode uniform
```

If the participants file argument is omitted, the tool defaults to `participants.csv`
located next to the script. Note: if that file is a CSV with `ticket_count`, you must
run with `--mode weighted` because the default mode is `uniform`.

Note: The default mode is uniform. CSV files with ticket_count require --mode weighted.

```bash
# Optional convenience
cp participants.example.csv participants.csv
python3 draw.py <BTC_BLOCK_HASH> participants.csv --mode weighted
```

---

## Example (uniform, primary)

Example run using uniform mode:

```bash
python3 draw.py 00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d participants-uniform.csv --mode uniform
```

Example output:

```text
tool=alien-draw-tool
version=1.1.0
mode=uniform
block_hash=00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d
participants_file=participants-uniform.csv
canonical_snapshot=username,ticket_count (normalized + sorted)
participants_raw_file_bytes=42
participants_raw_file_sha256=4d6e1b3e6c5b0f3f4b0d0f6f1b9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a
canonical_snapshot_bytes=56
canonical_snapshot_sha256=1f2e3d4c5b6a79808f9e0d1c2b3a4958675647382910a1b2c3d4e5f60718293a
seed_sha256=9a8b7c6d5e4f32100123456789abcdef0123456789abcdef0123456789abcdef
total_tickets=3
winner_ticket=2
winner_username=@bob
winner_ticket_range=2-2
```

---

## Example (weighted, secondary)

Example run using weighted mode:

```bash
python3 draw.py 00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d participants.example.csv --mode weighted
```

Output differences vs uniform (same block hash, full proof omitted):

```text
mode=weighted
participants_file=participants.example.csv
participants_raw_file_bytes=50
participants_raw_file_sha256=73945614bc951e555d60e480af946c105a032965e8711a2355e402f551722b16
canonical_snapshot_sha256=9d41533ede4ce04097234f69959d87d130122eaa622ef386b79dccb6d8144762
seed_sha256=018dbfab7a0acc0051282294e89f20489bc4d5e1bd6670b5fd929276779ae857
total_tickets=38
winner_ticket=18
winner_username=charlie
winner_ticket_range=16-28
```

---


## Determinism

- no local randomness is used
- the Bitcoin block hash is an external, unpredictable source
- the canonical snapshot (normalized + sorted) is hashed before selection

Selection depends on the canonical snapshot hash; the raw participants file hash is printed for auditing purposes only.

Anyone can reproduce the result byte-for-byte using the same inputs.

---

Part of **Alien Tools**.
