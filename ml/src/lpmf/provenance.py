"""Data-provenance convention shared across the LPMF codebase.

Every chart and every number shown in the dashboard must be tagged with one of
these four kinds so a viewer always knows whether they are looking at
measured reality or something else. This module is the Python half of the
convention; the TypeScript twin lives at web/src/lib/provenance.ts and MUST be
kept in sync field-for-field.

See docs/PROVENANCE.md for the rule this enforces.
"""

from __future__ import annotations

from enum import Enum


class ProvenanceKind(str, Enum):
    """The four provenance kinds. Values are the exact strings persisted to
    disk (parquet columns, JSON, etc.) and sent over the wire to the web app
    — do not rename without updating both sides of the stack.
    """

    REAL = "REAL"
    """Measured data from a real meter, SCADA feed, or official source."""

    SYNTHETIC = "SYNTHETIC"
    """Generated/simulated data standing in for real data that does not
    (yet) exist — e.g. synthetic smart-meter profiles before rollout."""

    FOREIGN = "FOREIGN"
    """Real data, but not from the primary subject of this dashboard (e.g.
    another DISCOM, another city, or a benchmark/reference series)."""

    ILLUSTRATIVE = "ILLUSTRATIVE"
    """Not real and not meant to be mistaken for a forecast — illustrative
    placeholders, worked examples, mock UI states."""


# Human-readable label + short description, used by the QA report and any
# place that renders a legend.
PROVENANCE_LABELS: dict[ProvenanceKind, str] = {
    ProvenanceKind.REAL: "Real",
    ProvenanceKind.SYNTHETIC: "Synthetic",
    ProvenanceKind.FOREIGN: "Foreign",
    ProvenanceKind.ILLUSTRATIVE: "Illustrative",
}


def is_real(kind: ProvenanceKind | str) -> bool:
    """True only for genuine, primary-subject measured data."""
    return ProvenanceKind(kind) == ProvenanceKind.REAL
