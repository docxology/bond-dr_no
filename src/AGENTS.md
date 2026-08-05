# src/dr_no

CRAB KEY domain core. Keep `mission.py` / `cli.py` as the `bond_api`-importing
adapters; every domain module imports only the domain core and
stdlib/numpy/matplotlib. Proven at runtime: importing the eight pure modules
(`isotope_profiles`, `spectrum_processing`, `decay_chain`, `shielding`,
`dose_assessment`, `plume_model`, `island_assessment`, `canonical`) leaves
`bond_api` absent from `sys.modules`. See `../docs/architecture.md`.
