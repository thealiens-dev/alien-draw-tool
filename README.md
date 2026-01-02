Alien Draw Tool

Deterministic and publicly verifiable draw mechanism.

Algorithm:
- seed = sha256(block_hash + sha256(participants.csv))
- winner_ticket = (seed % total_tickets) + 1

Run:
python3 . <BTC_BLOCK_HASH>

participants.csv must be placed next to draw.py.