# Changelog

## Rules

- Any change to output/proof, CLI flags, default modes, input parsing, or README examples must be recorded here.
- Purely internal changes can be omitted unless they affect proof/format.

## [2.0.0] - 2026-01-23

### Breaking

- Proof format is now list-based only (pipe-delimited), even for --winners 1.
- Removed single-winner fields: seed_sha256, winner_ticket, winner_username, winner_ticket_range.
- Removed global canonical_snapshot_bytes and canonical_snapshot_sha256 fields (to avoid duplicating per-round proof fields; canonical snapshot proof is now only emitted via the *_rounds outputs).
- Renamed mode "uniform" to "equal" (terminology change only; algorithm and behavior unchanged).
- `--mode` is now required (must be explicitly set to `equal` or `weighted`).

### Added

- Added new --winners flag and made it required (must be provided explicitly).
- winners_* list outputs (pipe-delimited): winners_count, winners_usernames, winners_tickets, winners_ticket_ranges.
- total_tickets_rounds (pipe-delimited) to document per-round ticket pools.
- canonical_snapshot_sha256_rounds (pipe-delimited) to document per-round canonical hashes.
- canonical_snapshot_bytes_rounds (pipe-delimited) to document per-round canonical byte sizes.
- seeds_sha256 (pipe-delimited) to document per-round seeds.
- tests/regenerate_vectors.py helper to regenerate test vectors from current output.
- `participants_count` field documenting the number of unique participants after normalization and validation.

### Notes

- Multi-winner seeding is per-round: SHA256(block_hash + canonical_snapshot_sha256_round_i).
- Pending (`status=pending`) output includes round-1 preview fields (including `participants_count`) but does not include seeds or winner lists.

## [1.1.3] - 2026-01-18

### Fixed

- Python 3.9 compatibility: replaced PEP 604 union type syntax (`str | None`) with `typing.Optional` in type hints.

## [1.1.2] - 2026-01-08

### Added

- GitHub Actions workflow to run test vectors on every push.
- 100-user test vector fixtures for uniform and weighted modes.
- New test vector cases (uniform + block_hash, weighted + block_hash, uniform + block_height, pending block_height).

### Changed

- README positioning clarified (tool naming aligned with common random picker terminology).
- Require at least two unique usernames to run a draw.
- README examples updated to full, standalone proof outputs using the new fixtures.
- README clarified that uniform file extensions are not validated (content-only).
- CHANGELOG formatting standardized for GitHub Preview (headings + Markdown lists).
- .gitignore now ignores `local/` instead of `participants*.csv`.

## [1.1.0] - 2026-01-05

### Added

- New uniform mode for CLI draws (one username per line, equal weight).
- mode field added to proof output (uniform / weighted).
- Support for participant lists without ticket counts in uniform mode.
- project field added to proof output (project=The Aliens).
- Added Apache License 2.0 for the CLI tool.
- --block-height resolver via mempool.space.
- status field and pending mode for future block heights (exit code 2).
- Test vectors to lock deterministic CLI outputs.

### Changed

- Canonical snapshot is always normalized to username,ticket_count, including uniform mode (ticket_count = 1).
- README updated with clear description of both modes and new usage examples.
- block-height resolve 404 is now pending instead of a hard error.

### Breaking

- Default mode changed from weighted to uniform.
- Block hash is now passed via --block-hash (no longer positional).

### Unchanged

- Draw algorithm and cryptographic process remain unchanged.
- Weighted mode behavior is fully backward compatible.
