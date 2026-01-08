# Changelog

## Rules

- Any change to output/proof, CLI flags, default modes, input parsing, or README examples must be recorded here.
- Purely internal changes can be omitted unless they affect proof/format.

## [1.1.2] – 2026-01-08

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

## [1.1.0] – 2026-01-05

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

- Default mode is now uniform.
- Canonical snapshot is always normalized to username,ticket_count, including uniform mode (ticket_count = 1).
- README updated with clear description of both modes and new usage examples.
- block-height resolve 404 is now pending instead of a hard error.

### Breaking

- Default mode changed from weighted to uniform.
- Block hash is now passed via --block-hash (no longer positional).

### Unchanged

- Draw algorithm and cryptographic process remain unchanged.
- Weighted mode behavior is fully backward compatible.
