# Data Provenance Convention

LPMF shows grid-operations data to engineers who make real decisions from
it. Every chart and every number rendered in this app **must** make it
obvious whether it is measured reality, a stand-in, borrowed from elsewhere,
or just an illustration. Silently blurring that line is the one mistake
this project is not allowed to make.

## The four kinds

Defined once, shared by both halves of the stack:

- Python: [`lpmf.provenance.ProvenanceKind`](../ml/src/lpmf/provenance.py)
- TypeScript: [`@/lib/provenance`](../web/src/lib/provenance.ts)

| Kind | Meaning |
|---|---|
| `REAL` | Measured data from a real meter, SCADA feed, or official source (e.g. Delhi SLDC, Open-Meteo). |
| `SYNTHETIC` | Generated/simulated data standing in for real data that doesn't (yet) exist — e.g. synthetic smart-meter profiles before rollout. |
| `FOREIGN` | Real data, but not about Delhi — another DISCOM, another city, a benchmark/reference series. |
| `ILLUSTRATIVE` | Not real and not meant to be read as a forecast — worked examples, mock UI states, placeholders. |
| `MODELLED` | A published physical/engineering model applied to real, measured inputs, estimating something not itself directly metered — e.g. rooftop solar output from real Open-Meteo irradiance and a public capacity figure. Inputs are real; only the output is an estimate. |

## The rule

**Every chart and every standalone number in the dashboard renders a
`<SourceBadge kind=... source="..." />`.** No exceptions, including while a
page is still a Phase 0 placeholder — an empty chart slot still carries (or
will carry, the moment data lands in it) a badge, not a silent assumption.

`kind` is one of the four `ProvenanceKind` values above. `source` is a
short human string naming where the number actually came from, e.g.:

```tsx
<SourceBadge kind="REAL" source="Delhi SLDC (Kaggle)" />
<SourceBadge kind="REAL" source="Open-Meteo Archive API" />
<SourceBadge kind="SYNTHETIC" source="Synthetic smart-meter profile v1" />
<SourceBadge kind="ILLUSTRATIVE" source="Worked example" />
<SourceBadge kind="MODELLED" source="Open-Meteo GHI + MNRE capacity estimate" />
```

## Why this exists

A dashboard that mixes real SCADA numbers with synthetic placeholders and
gives them the same visual weight will eventually cause someone to act on
a number that was never real. The badge is cheap; the alternative is not.

## Enforcement

This is a convention today (Phase 0: no charts render real data yet). As
real charts and numbers are built in later phases, the badge becomes a
mandatory prop/requirement on every chart and stat component — a component
that renders a number without a `SourceBadge` is a bug, not a style choice.
The global topbar "Data: REAL / SYNTHETIC" legend chip is the page-level
summary of the same rule, not a replacement for it.
