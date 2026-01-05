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

## Usage

```bash
# Run with an explicit participants file
python3 draw.py <BTC_BLOCK_HASH> participants.example.csv
```

If the participants file argument is omitted, the tool defaults to `participants.csv`
located next to the script.

```bash
# Optional convenience
cp participants.example.csv participants.csv
python3 draw.py <BTC_BLOCK_HASH>
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
participants_file=participants.example.csv
canonical_snapshot=username,ticket_count (normalized + sorted)
participants_file_bytes=50
participants_file_sha256=73945614bc951e555d60e480af946c105a032965e8711a2355e402f551722b16
canonical_snapshot_bytes=51
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