
# Alien Draw Tool

Deterministic and publicly verifiable draw mechanism used by **The Aliens**.

The tool selects exactly one winner based on:
- a public Bitcoin block hash
- a finalized participants snapshot (`participants.csv`)

Given the same inputs, the output is always identical and can be independently reproduced.

---

## Algorithm

```
snapshot_hash = SHA256(participants.csv bytes)
seed          = SHA256(block_hash + snapshot_hash)
winner_ticket = (int(seed, 16) % total_tickets) + 1
```

The winning participant is the one whose ticket range contains `winner_ticket`.

---

## Input format

```csv
username,ticket_count,from_ticket,to_ticket
@alice,10,1,10
@bob,15,11,25
@charlie,13,26,38
```

Rules:
- ticket ranges must be continuous and start at `1`
- `ticket_count` must equal `(to_ticket - from_ticket + 1)`
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
block_hash=00000000000000000000a2fe23965ff0ca8a8178e8912840c0652201e9d6bb0d
participants_csv=participants.example.csv
participants_csv_sha256=<sha256>
seed_sha256=<sha256>
total_tickets=38
winner_ticket=<n>
winner_username=<username>
winner_ticket_range=<from>-<to>
```

---

## Determinism

- no local randomness is used
- the Bitcoin block hash is external and unpredictable
- the participants snapshot is hashed before selection

Anyone can reproduce the result byte-for-byte using the same inputs.

---

Part of **Alien Tools**.