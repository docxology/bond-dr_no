# scripts/ — thin CRAB KEY CLI orchestrators

| Script | Purpose |
| --- | --- |
| `run_mission.py` | CLI wrapper over `dr_no.cli.main`; phases brief/recon/plan/execute/debrief/full/render |
| `z_generate_manuscript_variables.py` | hydrates `{{TOKEN}}` map + resolved manuscript sections |

All business logic lives in `src/`. Scripts only bootstrap `src/` onto
`sys.path` and forward. Keep them thin.
