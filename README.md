Alien Draw Tool

Deterministic and publicly verifiable draw mechanism.

Algorithm:
- seed = sha256(block_hash + sha256(participants.csv))
- winner_ticket = (seed % total_tickets) + 1

Run:
cd btc_draw
python3 draw.py <BTC_BLOCK_HASH>

participants.csv must be placed next to draw.py.