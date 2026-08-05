# src/dr_no

CRAB KEY domain core.

Keep `mission.py` and `cli.py` as the only `bond_api`-importing adapters; every
other module imports the domain core plus stdlib / numpy / matplotlib / PyYAML.
Proven at runtime: importing the nine non-adapter modules (`scenario`,
`isotope_profiles`, `spectrum_processing`, `decay_chain`, `shielding`,
`dose_assessment`, `plume_model`, `island_assessment`, `canonical`) leaves
`bond_api` absent from `sys.modules`.

Layer order (dependencies point downward only):

```
scenario  ->  domain models  ->  canonical  ->  mission / manuscript_variables / figures
```

`mission.py`'s public shape is **frozen** — other BOND packages consume it.
See [`../docs/architecture.md`](../docs/architecture.md) §3 before touching it,
and [`../docs/agent_instructions.md`](../docs/agent_instructions.md) for the
working rules.
