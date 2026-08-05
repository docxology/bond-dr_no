# Architecture — CRAB KEY (dr_no)

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/dr_no/isotope_profiles.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/spectrum_processing.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/decay_chain.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/shielding.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/dose_assessment.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/plume_model.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/island_assessment.py` | Pure (imports plume_model + dose_assessment). No `bond_api`. |
| `src/dr_no/canonical.py` | Pure: single-source-of-truth scenario + metrics. No `bond_api`. |
| `src/dr_no/mission.py` | Mission **adapter**: imports `bond_api`; thin protocol adapter over `canonical`. |
| `src/dr_no/figures/plots.py` | Pure visualization (matplotlib). No `bond_api`. |
| `src/dr_no/cli.py` | Thin phase driver over `mission.py` + figures (imports `bond_api` to run the flow). |
| `scripts/` | Thin CLI wrappers (argv forwarding). |

## Data flow

```
manuscript/config.yaml ──► z_generate_manuscript_variables.py ──► manuscript_variables.py ─► tokens
        │                                        ▲
        ▼                                        │ canonical_metrics()
bond_api discovery ──► dr_no.mission.MissionProvider ──► canonical_metrics() ──┐
                              │  brief/recon/plan/execute/debrief              ▼
                              ▼                                   isotope_profiles · spectrum_processing
                   outcomes + Provenance (seed, input_hash)         decay_chain · shielding · dose_assessment
                                                                    plume_model · island_assessment
```

## Why the boundary exists

All seven domain modules plus `canonical.py` carry the real science and must
stay importable and testable *without* bond-api — so a broken protocol
dependency can never take the forensics down. mission.py is the seam where the
frozen protocol meets the domain; only it depends on bond-api. The
single-source-of-truth `canonical_metrics()` is consumed by **both** the
mission's `execute()` results and `manuscript_variables` tokens, so the two can
never disagree. This mirrors the bond-suite convention and keeps the pure core
reusable.
