# Architecture — CRAB KEY (dr_no)

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/dr_no/isotope_profiles.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/plume_model.py` | Pure. No `bond_api`, no `infrastructure`. |
| `src/dr_no/island_assessment.py` | Pure (imports only the other pure core). No `bond_api`. |
| `src/dr_no/mission.py` | **Only** module importing `bond_api`; thin protocol adapter. |
| `src/dr_no/figures/plots.py` | Pure visualization (matplotlib). No `bond_api`. |
| `src/dr_no/cli.py` | Thin phase driver over `mission.py` + figures. |
| `scripts/` | Thin CLI wrappers (argv forwarding). |

## Data flow

```
manuscript/config.yaml ──► z_generate_manuscript_variables.py ──► manuscript_variables.py ─► tokens
        │
        ▼
bond_api discovery ──► dr_no.mission.MissionProvider ──► domain core
                              │  brief/recon/plan/execute/debrief
                              ▼
                   isotope_profiles · plume_model · island_assessment
                              │
                              ▼
                   outcomes + Provenance (seed, input_hash)
```

## Why the boundary exists

The three domain modules carry the real science and must stay importable and
testable *without* bond-api — so a broken protocol dependency can never take the
forensics down. mission.py is the seam where the frozen protocol meets the
domain; only it depends on bond-api. This mirrors the bond-suite convention and
keeps the pure core reusable.
