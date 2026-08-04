# scripts/

Thin orchestrators only — no business logic. `run_mission.py` forwards argv to
`dr_no.cli.main`; `z_generate_manuscript_variables.py` hydrates manuscript
tokens. Both self-bootstrap `src/` onto `sys.path` before importing.
