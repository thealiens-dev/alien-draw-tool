Changelog

[1.1.0] – 2026-01-05

Added
	•	New uniform mode for CLI draws (one username per line, equal weight).
	•	mode field added to proof output (uniform / weighted).
	•	Support for participant lists without ticket counts in uniform mode.

Changed
	•	Default mode is now uniform.
	•	Canonical snapshot is always normalized to username,ticket_count, including uniform mode (ticket_count = 1).
	•	README updated with clear description of both modes and new usage examples.

Breaking
	•	Default mode changed from weighted to uniform.

Unchanged
	•	Draw algorithm and cryptographic process remain unchanged.
	•	Weighted mode behavior is fully backward compatible.
