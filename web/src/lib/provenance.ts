/**
 * Data-provenance convention shared across the LPMF codebase.
 *
 * Every chart and every number shown in the dashboard must be tagged with
 * one of these four kinds so a viewer always knows whether they are looking
 * at measured reality or something else. This is the TypeScript half of the
 * convention; the Python twin lives at ml/src/lpmf/provenance.py and MUST be
 * kept in sync value-for-value.
 *
 * See docs/PROVENANCE.md for the rule this enforces.
 */

export enum ProvenanceKind {
  /** Measured data from a real meter, SCADA feed, or official source. */
  REAL = "REAL",
  /**
   * Generated/simulated data standing in for real data that does not (yet)
   * exist — e.g. synthetic smart-meter profiles before rollout.
   */
  SYNTHETIC = "SYNTHETIC",
  /**
   * Real data, but not from the primary subject of this dashboard (e.g.
   * another DISCOM, another city, or a benchmark/reference series).
   */
  FOREIGN = "FOREIGN",
  /**
   * Not real and not meant to be mistaken for a forecast — illustrative
   * placeholders, worked examples, mock UI states.
   */
  ILLUSTRATIVE = "ILLUSTRATIVE",
}

export const PROVENANCE_LABELS: Record<ProvenanceKind, string> = {
  [ProvenanceKind.REAL]: "Real",
  [ProvenanceKind.SYNTHETIC]: "Synthetic",
  [ProvenanceKind.FOREIGN]: "Foreign",
  [ProvenanceKind.ILLUSTRATIVE]: "Illustrative",
};

export function isReal(kind: ProvenanceKind): boolean {
  return kind === ProvenanceKind.REAL;
}
