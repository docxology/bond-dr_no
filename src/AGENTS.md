# src/dr_no

CRAB KEY domain core. Keep `mission.py` as the sole `bond_api`-importing seam;
everything else imports only the domain modules and stdlib/numpy/matplotlib.

Boundary gate: `grep -rnE "^(from|import) bond_api" src/dr_no/` must match only
`mission.py`. See `../docs/architecture.md`.
