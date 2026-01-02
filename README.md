Alien Draw Tool

Deterministic and publicly verifiable draw mechanism.

Algorithm:
- seed = SHA256(block_hash + SHA256(participants.csv))
- winner_ticket = (seed % total_tickets) + 1

Run:
python3 . <BTC_BLOCK_HASH>

participants.csv must be placed in the same directory as the tool.

## Determinism

The draw is fully deterministic and reproducible.

Inputs:
- `block_hash` – Bitcoin block hash provided at runtime (external, unpredictable source)
- `participants.csv` – snapshot of participants and ticket ranges

Steps:
1. `snapshot_hash = SHA256(participants.csv bytes)`
2. `seed = SHA256(block_hash + snapshot_hash)`
3. `winner_ticket = (int(seed, 16) % total_tickets) + 1`

The value printed as `seed_sha256` is the final deterministic seed used to derive the selection.
The selection index is derived via modulo; any theoretical modulo bias is negligible for this use-case.
Given the same inputs, the result is always identical and can be independently verified.