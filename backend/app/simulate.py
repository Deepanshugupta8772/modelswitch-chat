"""Parser for the gated Phase 3 provider-failure test header."""

import re

ALLOWED_FAILURE_STATUSES = frozenset({429, 500, 502, 503})
_KEY_ID_PATTERN = re.compile(r"key_[1-9]\d*|\*")


def parse_simulated_failures(
    header_value: str | None, *, enabled: bool
) -> dict[str, int]:
    """Parse valid key/status pairs only when simulation is enabled."""
    if not enabled or not header_value:
        return {}

    failures: dict[str, int] = {}
    for entry in header_value.split(","):
        key_id, separator, raw_status = entry.strip().partition("=")
        if not separator or not _KEY_ID_PATTERN.fullmatch(key_id):
            continue
        try:
            status = int(raw_status.strip())
        except ValueError:
            continue
        if status in ALLOWED_FAILURE_STATUSES:
            failures[key_id] = status
    return failures
