# TODO — dr_no (CRAB KEY)

CRAB KEY is the PROJECT BOND film package for *Dr. No* (1962): a radiation/isotope
forensics chain that runs from a declared scenario in `manuscript/config.yaml`
through gamma-spectrum synthesis and isotope identification, Currie
quantification, Bateman decay projection, shielding attenuation, Gaussian plume
dispersion, and inhalation dose, to a five-band island threat posture and a
containment action. It exposes the frozen `bond_api` `MissionProvider` surface
(slug `dr_no`) and hydrates every manuscript number as a token from one metric
pass. **Verified state: re-measured 2026-11-04 after the `bond-api` vendoring
round** (§Round-2 below is the prior round's record) — 346 tests collected, 346
passed, 0 failed, 0 skipped; `src/` line+branch coverage 100.00% (`uv run pytest
tests/ --cov=src --cov-report=term-missing`). Ruff check, ruff format --check
(47 files), and mypy on `src/` + `scripts/` (20 files) are all clean in the same
session, the template-lineage scan returns nothing, `scripts/vendor.py --check`
reports `vendor/bond-api: ok`, and
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) is that run's output
from `scripts/z_generate_counts.py`.

This file tracks only what is **not** done. What exists is described in
[`README.md`](README.md) and [`docs/architecture.md`](docs/architecture.md).

---

## Open work

### Correctness — things that are wrong

**C1. The shielding table cannot cover the library's highest-energy line.**
`MASS_ATTENUATION_CM2_G` (`src/dr_no/shielding.py:40-45`) tabulates six energy
points per material and `mass_attenuation()` hard-rejects anything outside
`[_MIN_ENERGY_MEV, _MAX_ENERGY_MEV] = [0.1, 2.0]` MeV
(`src/dr_no/shielding.py:58-59`, guard at `:72-76`). The isotope library carries
Tl-208 at 2614.53 keV (`src/dr_no/isotope_profiles.py:52`), so shielding cannot
be computed at all for the library's strongest high-energy emitter — it raises
`ValueError: energy 2.61453 MeV is outside the table range [0.1, 2.0]`. This is
not a disclosed limitation anywhere; the manuscript §7.3 caveat is about
tabulation *coarseness*, not about a line falling off the end of the table.
*Done when:* the table extends to at least 3 MeV for all four materials from the
cited NIST source, `_MAX_ENERGY_MEV` moves with it, and a test iterates every
gamma line in `isotope_library()` and asserts `mass_attenuation()` returns a
finite positive value for each.
*Demonstrate:*
```bash
uv run python -c "from dr_no.shielding import mass_attenuation; print(mass_attenuation(2.61453, 'lead'))"
uv run pytest tests/test_shielding.py tests/test_defect_regressions.py -q
```
Note `tests/test_defect_regressions.py:228
::test_mass_attenuation_raises_outside_the_table_range` pins the *current*
bounds and will need its probe energy moved above the new ceiling, not deleted.

**C2. `detect_peaks()` silently reports a genuine doublet as one line.**
`src/dr_no/isotope_profiles.py:258-264`: candidates closer than
`min_separation_keV` (default 5.0 keV, `:218`) are collapsed and only the
stronger survives — the weaker peak is discarded, not flagged. For a real
doublet this returns a confidently wrong answer (one line, at the stronger
line's energy) rather than an uncertain one, and identification downstream never
learns a peak was dropped. *Done when:* either a fitted two-Gaussian
deconvolution resolves the merged region, or — the smaller honest fix —
`DetectedPeak` carries a `merged_count`/`merged_energies` field so a collapsed
multiplet is visible to the caller, with a test that synthesizes a known doublet
inside `min_separation_keV` and asserts both members are recovered or the merge
is reported.
*Demonstrate:* `uv run pytest tests/test_isotope_profiles.py -q -k doublet`

**C3. The threat-band edges are Python literals, which violates this package's
own scenario invariant.** `_DOSE_THRESHOLDS_SV_S = (1.0e-11, 1.0e-9, 1.0e-7,
1.0e-5)` at `src/dr_no/island_assessment.py:49`, plus `SHELTER_THRESHOLD_SV_S`
(`:52`) and `ACTION_CONCENTRATION_BQ_M3` (`:55`). `AGENTS.md:111-115` states
flatly that scenario numbers live in `manuscript/config.yaml`, never as Python
literals, and `manuscript/config.yaml` already carries a thresholds block that
the other decision constants read. These four are the exception, and they are
the numbers that decide the mission's headline posture. Separately they have no
published provenance (accepted as a *stated* limitation — see L4 — but the
config-invariant breach is not accepted). *Done when:* the band edges are keys
in the `mission:` block, loaded and validated by `src/dr_no/scenario.py`, and a
test edits the YAML on disk to move a band edge and asserts the island posture
changes — the same binding pattern `tests/test_canonical.py` already uses.
*Demonstrate:* `uv run pytest tests/test_scenario.py tests/test_island_assessment.py tests/test_canonical.py -q`

### Verification — claims not yet bound by a test that can fail

**V1. `data/claim_ledger.yaml` marks ten claims `verified: true` and nothing
reads the file.** `rg -n claim_ledger` finds only `data/README.md:3` and
`data/AGENTS.md:3` — no test, no script, no gate. Every entry could go false
(a renamed symbol, a deleted test, a softened claim) and the whole suite stays
green. This is the classic hand-maintained ledger whose truth is unbound.
*Done when:* a test loads `data/claim_ledger.yaml` and, per entry, resolves the
`source:` field — importing the named module attribute for
`module.py::symbol` entries and asserting the named test exists in the collected
suite for `tests/...::test_...` entries — and fails on any unresolvable source.
Bonus binding: assert every claim id is referenced somewhere in `manuscript/`.
*Demonstrate:* `uv run pytest tests/test_claim_ledger.py -q`, then rename a
symbol named in the ledger and watch it go red.

**V2. The published Pasquill–Gifford reference values live in the test module,
not in a citable data file.** *(Carried from the unresolved audit findings.)*
`tests/test_plume_model.py:48-98` hard-codes the reference σ values that
`test_sigma_y_matches_published_pasquill_gifford` (`:82`) and
`test_sigma_z_matches_published_pasquill_gifford` (`:91`) bind against; they are
graphical reads of the Turner-workbook curves transcribed into the test by the
same pass that wrote the implementation. The gate constrains the
implementation's arithmetic, units, and coefficient transcription — which is
exactly the defect class the phase-6 audit found — but the reference numbers
themselves carry no external, checkable provenance. *Done when:* the tabulated
curve values ship as a data file under `data/` with a page-and-edition-level
citation to the Turner workbook, the two tests load it instead of holding
literals, and the file is registered in `data/claim_ledger.yaml`.
*Demonstrate:* `uv run pytest tests/test_plume_model.py -q -k published`
(fails if the data file is missing or malformed).

**V3. Seven code paths are unreached — enumerate and pin them.** Measured this
session: 6 uncovered statements, 7 partial branches.

| Path | Location | What is unreached |
| --- | --- | --- |
| `_fwhm_at` guard | `src/dr_no/isotope_profiles.py:148` | non-positive detector resolution raise |
| zero-activity skip | `src/dr_no/isotope_profiles.py:200` | `continue` for an isotope declared at 0 Bq |
| empty-spectrum guard | `src/dr_no/isotope_profiles.py:242` | `return []` for a zero-length counts array |
| sub-threshold peak | `src/dr_no/isotope_profiles.py:249->245` | local maximum whose SNR is below `min_snr` |
| multiplet replace | `src/dr_no/isotope_profiles.py:261-262` | the merged-peak swap (see C2 — the untested branch *is* the wrong behaviour) |
| half-life guard | `src/dr_no/decay_chain.py:87` | `time_to_fraction` with a non-positive half-life |
| explicit chain arg | `src/dr_no/figures/plots.py:151->153` | `plot_decay_curves(chain_name=...)` given a non-`None` chain |

None can emit a wrong number today except the multiplet branch, which is C2.
*Done when:* each row has a test and the term-missing report is empty.
*Demonstrate:* `uv run pytest tests/ --cov=src --cov-report=term-missing` shows
`isotope_profiles.py 100.00%`, `decay_chain.py 100.00%`,
`figures/plots.py 100.00%`, TOTAL 100.00%.

**V4. Nothing binds `dr_no` into a multi-film chain.**
`tests/test_mission.py::test_discovery_loads_provider_by_slug` proves the
provider is discoverable in isolation, and `bond-cli`'s generic dispatcher
already loads it across packages (verified this session:
`bond_cli.dispatch.load_film("dr_no")` returns a provider whose `brief()`
codename is `CRAB KEY`, and `bond-coordinator/src/bond_coordinator/registry.py:83`
lists the slug). What is untested is the chain case: `_omnibus/run_omnibus.py`
feeds each film's recon findings into the next film's recon goal, and no test
asserts `dr_no.recon()` behaves sanely on a goal string produced by another
film. *Done when:* either a chain run including `dr_no` is recorded with its
provenance record, or a package-local test drives `recon()` with a foreign-format
goal and asserts non-empty, deterministic findings. The harness lives outside
this tree, so this may legitimately close at the suite level rather than here.
*Demonstrate:* `uv run pytest tests/test_mission.py -q -k recon`

### Documentation

**D1. `docs/_generated/COUNTS.md` says "generated" and is written by hand.**
Its header instructs a human to re-run the gate and transcribe the numbers. It
is currently accurate (its 318/99.02% matches this session's run), which is
exactly how a manual step stays invisible until the day it does not.
*Done when:* a script — `scripts/z_generate_counts.py`, alongside the two
existing thin CLIs — writes the file from `coverage json` output plus the pytest
summary, and a test fails when the committed file disagrees with a fresh
measurement. *Demonstrate:*
```bash
uv run python scripts/z_generate_counts.py && git diff --exit-code docs/_generated/COUNTS.md
```

**D2. Dose coefficients and gamma constants are cited collectively, not per
row.** The twenty constants in `INHALATION_DCF_SV_BQ`
(`src/dr_no/dose_assessment.py:34-48`) and `GAMMA_CONSTANT_MSV_M2_H_GBQ`
(`:50-62`) are attributed as a block to ICRP 119 and Smith & Stabin in
`manuscript/99_references.md:47,56` and `manuscript/references.bib:95,116`. A
reader cannot check any single number without re-deriving the whole table.
*Done when:* each entry carries an inline comment naming its table/row (or the
dicts are restructured to hold `(value, citation)`), so one constant can be
audited in isolation. *Demonstrate:* pick any three isotopes at random and trace
each to a named table row from the source comment alone; no command gates this
one, which is why it is documentation and not verification.

### Extension — genuine future work

**E1. Compton continuum in the detector model.** `synthesize_spectrum()`
(`src/dr_no/isotope_profiles.py:158-208`) places Gaussian photopeaks on a *flat*
background (`counts = np.full_like(energy_arr, background_level, dtype=float)`,
`:195`). Real
spectra carry a Compton continuum, backscatter peak, and Compton edge — which is
what makes real peak-finding hard. Acceptance: continuum shape derived from the
Klein–Nishina cross-section; existing round-trip identification tests still
pass, with SNR thresholds re-tuned rather than the tests relaxed.

**E2. Escape peaks and true-coincidence summing.** Single/double escape peaks
above 1.022 MeV and cascade summing (Co-60 in particular) are absent. Currently
disclosed in `manuscript/07_scope_and_related_work.md` §7.3.

**E3. Deposition/depletion in the plume.** The Gaussian plume has no dry or wet
deposition term (`src/dr_no/plume_model.py`, disclosed at
`manuscript/07_scope_and_related_work.md:55`), so it does not conserve mass
against the ground and overestimates far-field airborne concentration. The error
is in the conservative direction, which is why this is extension and not a
defect. A depletion factor is the smallest honest improvement; acceptance is a
test showing centreline concentration falls below the no-deposition case at a
stated distance while staying non-negative everywhere.

**E4. Delegate provenance persistence to `bond-utilities`.** *Now unblocked* —
`bond_utilities.mission_io.record_provenance_outcome` has shipped
(`bond-utilities/src/bond_utilities/mission_io.py:153`, exported at
`bond_utilities/__init__.py:82`). `src/dr_no/mission.py:57-61` still builds its
own `_input_hash()` and hands it to a locally constructed `Provenance`
(`:159-167`). Two things to get right when adopting it: (a) `bond-utilities` is
not yet a dependency in `pyproject.toml:18-23` and the `AGENTS.md:83-94` layer
contract confines protocol imports to `mission.py`/`cli.py` — keep it there; and
(b) `record_provenance_outcome` defaults `started_at` to
`datetime.now(timezone.utc)` (`mission_io.py:189`), so the `now=`/`started_at=`
overrides **must** be passed explicitly or it will break this package's
no-wall-clock-in-any-persisted-artifact guarantee (`README.md`, "Deterministic"
bullet). `_input_hash()` now delegates to
`dr_no.canonical.scenario_fingerprint()`, which is also the source of the
manuscript's `SCENARIO_FINGERPRINT` token — if the local helper is dropped, the
delegation must survive so the two cannot drift. Acceptance: outcome
persistence goes through `record_provenance_outcome`,
`tests/test_mission.py::test_input_hash_is_stable` is replaced by a test that
runs `execute()` twice and asserts byte-identical records, and
`tests/test_regeneration_determinism.py` still passes unchanged.

---

## Known limitations (not bugs)

These are accepted. Do not re-open them as defects.

**L1. `sigma_z` beyond 1 km is an extrapolation.** *(From the unresolved audit
findings.)* `src/dr_no/plume_model.py:124-140` implements only D. O. Martin's
(1976) near-field (`x ≤ 1 km`) vertical branch; Martin publishes a separate
coefficient set for `x > 1 km` that this package does not carry. Stated in the
`sigma_z` docstring, the `STABILITY_TABLE` comment (`:77-79`),
`manuscript/02_methodology.md` §2.2, §7.3, `docs/architecture.md`,
`manuscript/references.bib`, and `data/claim_ledger.yaml`. **Reason accepted:**
implementing the far-field branch introduces a discontinuity at 1 km that needs
its own treatment and its own test; that was out of scope for the phase-6
remediation. Implementing it is legitimate future work, but the current state is
honest, not broken.

**L2. Both dispersion coefficients are floored at 0.1 m near the source.**
*(From the unresolved audit findings.)* `_SIGMA_FLOOR_M` at
`src/dr_no/plume_model.py:99` (rationale comment `:92-98`). Martin's negative `f_z` offsets drive the raw
`sigma_z` non-positive inside roughly 7–17 m (class-dependent), and
`sigma_y = 0` exactly at `x = 0`. Flooring keeps the Gaussian well-posed instead
of returning a negative concentration. **Honest scope:** concentrations inside
that near-source region are *not quantitatively modelled*. Stated in the module,
in methodology §2.2, and in the claim ledger; pinned by
`tests/test_plume_model.py:113::test_sigma_is_strictly_positive_including_near_source`
and `tests/test_defect_regressions.py:68::test_sigma_z_never_returns_a_non_positive_value`.

**L3. The Pasquill–Gifford binding validates the implementation, not Martin's
fit.** Agreement at the anchor points is expected rather than surprising: the
tests pin arithmetic, units, and coefficient transcription against published
numbers, and deliberately claim no more. Stated in the test-module comment
(`tests/test_plume_model.py:55-60`). The separate, open question of where those
reference numbers themselves come from is V2 — do not conflate the two.

**L4. Threat banding is a declared decision rule, not a regulatory standard.**
`manuscript/07_scope_and_related_work.md` §7.3 says so plainly: the band edges
are chosen to be legible, not derived from a published intervention level.
Sourcing them from a protective-action guide would be an improvement but is not
required for the claims this package makes. What *is* open is that they are
Python literals rather than declared config — that is C3, and it is a different
complaint.

**L5. All physical constants are representative literature values at coarse
tabulation.** Dose coefficients, gamma constants, mass-attenuation entries, and
dispersion coefficients are order-of-magnitude faithful, named, and traceable,
interpolated log-log between table points. §7.3 states the results are a
screening pass, not a substitute for a licensed consequence assessment.

**L6. Repository.** Upstream `https://github.com/docxology/bond-dr_no`, default
branch `main`. Commits are path-scoped to this directory.

### Standing constraints

- Never change the public shape of `mission.py` or the `GADGETS` registry —
  `bond-cli`, the coordinator, and the orchestrator consume it across packages.
- Never reintroduce template-scaffold lineage strings.
- Never introduce a mock framework or non-determinism; substitutions are
  inventoried by `tests/test_suite_hygiene.py` and an undeclared one fails the
  build.
- Never derive a token, metric, or provenance field from the wall clock. A
  `GENERATION_TIMESTAMP` built from `datetime.now()` falsified the package's
  byte-identical-regeneration claim for several releases while a clock-freezing
  test reported it safe (fixed 2026-08-05). Use
  `dr_no.canonical.scenario_fingerprint()` for provenance;
  `tests/test_regeneration_determinism.py` regenerates twice and diffs bytes.
- Never hand-author a metric in manuscript prose — every number arrives as a
  token.
- Never let a failure path return a plausible-looking number.

---

## Verification

The gate, and what a green run looks like on this tree:

```bash
cd bond-dr_no

# The gate — 345 passed, src/ coverage 100.00% (floor 90%)
uv run pytest tests/ --cov=src --cov-fail-under=90

uv run ruff check src/ scripts/ tests/          # All checks passed!
uv run ruff format --check src/ scripts/ tests/ # 45 files already formatted
uv run mypy src/ scripts/                       # no issues in 19 source files

# Policy scans
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
rg -n "MagicMock|mocker\.patch|unittest\.mock" src/ tests/ || echo "No mock framework"
# ^ necessary but NOT sufficient: it cannot see monkeypatch.setattr.
#   The complete check runs in-suite:
uv run pytest tests/test_suite_hygiene.py -q    # 3 passed

# Artifacts, if anything you changed moves a number
uv run python scripts/run_mission.py render
uv run python scripts/z_generate_manuscript_variables.py
# then update docs/_generated/COUNTS.md from the run you actually performed (D1)

git status --short   # clean after commit
```

If a gate could not be run, say so rather than reporting the last number you
read.


---

## Round-2 (2026-08-06)

Verified state measured **this session** on this tree (commit ahead of the
round-1 `f5fa300`), Python 3.14.6: **345 tests collected, 345 passed, 0 failed,
0 skipped; `src/` line+branch coverage 100.00%** (`uv run pytest tests/
--cov=src --cov-report=term-missing`). Ruff check, ruff format --check, and
mypy on `src/` + `scripts/` all clean; the template-lineage scan returns
nothing. This resolves TODO items **C1, C2, C3, V1, V3, and D1** below (each
recorded in its own bullet). V2, V4, D2, and E1–E4 remain open as listed.

### Fixed this round (each with a regression/negative-control test)

- **C1 — shielding table could not cover the library's highest-energy line**
  (Tl-208 @ 2614.53 keV): extended `MASS_ATTENUATION_CM2_G` to 0.05–3.0 MeV
  for all four materials (representative NIST-XCOM values, still log-log
  interpolated) and moved `_MAX_ENERGY_MEV` (`src/dr_no/shielding.py`). Two new
  tests — `test_every_library_gamma_line_is_covered_by_the_attenuation_table`
  and `test_library_hottest_line_is_covered_and_finite` in
  `tests/test_shielding.py` — iterate every gamma line of every isotope and
  assert `mass_attenuation()` returns a finite positive value, so a future
  higher-energy line that falls off the table fails the build. The OLD defect
  regression `test_mass_attenuation_raises_outside_the_table_range` still passes
  (its 10 MeV probe is above the new ceiling).

- **C2 — `detect_peaks()` silently reported a doublet as one line**:
  `DetectedPeak` now carries `merged_energies` and the merge loop records every
  absorbed member instead of discarding it (`src/dr_no/isotope_profiles.py`).
  `test_detect_peaks_reports_merged_doublet` synthesizes two peaks 2 keV apart
  inside the 5 keV window and asserts the survivor carries the absorbed member;
  `test_detect_peaks_reports_merge_when_stronger_arrives_second` pins the other
  merge orientation; `test_detect_peaks_filters_subthreshold_local_maxima` pins
  the previously-unreached sub-SNR branch.

- **C3 — threat band edges and shelter threshold were Python literals** in
  `island_assessment.py`, breaching the package's scenario invariant. They are
  now declared under `mission.threat` in `manuscript/config.yaml` (`band_edges_sv_s`,
  `shelter_dose_rate_sv_s`), loaded and validated by `src/dr_no/scenario.py`
  (new `ThreatSpec`), and threaded through `canonical_metrics` →
  `assess_island` → `facility_threat_level`. Binding tests:
  `test_declared_threat_band_edges_drive_island_posture`,
  `test_threat_config_file_edit_reaches_the_posture`,
  `test_declared_shelter_threshold_drives_evacuation_recommendation` (all in
  `tests/test_canonical.py`), plus load-time validation tests in
  `tests/test_scenario.py` (wrong edge count, non-positive, non-ascending,
  non-list, non-positive shelter). `test_every_required_mission_key_is_enforced`
  now includes `threat`.

- **V1 — the claim ledger was unbound**: `data/claim_ledger.yaml` marked ten
  claims `verified: true` and nothing read it. New `tests/test_claim_ledger.py`
  loads the ledger and resolves every `source:` against the live tree by AST (a
  `module.py::symbol` must define that symbol; a `tests/…::test_…` must define
  that test; a bare path must exist). All ten resolve; a renamed symbol, deleted
  test, or removed file now fails the build.

- **V3 — seven code paths were unreached**; now every one is covered and the
  `--cov-report=term-missing` module table is **100.00% everywhere**. New tests:
  `_fwhm_at` non-positive resolution raise, zero-activity synthesize skip,
  empty-spectrum `detect_peaks` guard, sub-threshold peak filter, both merge
  orientations, `time_to_fraction` non-positive half-life raise
  (`tests/test_decay_chain.py`), and an explicit `chain_name` decay figure
  (`tests/test_figures.py`).

- **Addition (hostile review) — negative activities were type-checked but not
  range-checked**. `_as_activities` in `src/dr_no/scenario.py` now rejects a
  negative declared activity at load (a planted negative value previously could
  flow into facility dose/threat arithmetic); `test_negative_activity_is_rejected_at_load`
  pins it. Zero remains a legitimate absent-activity placeholder.

### Manuscript improvements

- Methodology §2.3 now documents the *scenario-declared* threat band edges
  (`THREAT_BAND_EDGES_SV_S_CSV`) and evacuation dose rate
  (`SHELTER_DOSE_RATE_SV_S`) as tokens, and that a config edit moves the posture.
- Setup §5.1 corrected the shielding table span from "0.1–2.0 MeV" to
  "0.05–3.0 MeV" and lists the declared threat thresholds.
- Scope & limitations §7.3 rewritten: notes the doublet merge is now visible
  (not silently dropped), adds the low-energy/pass-through-edge
  (lead ~88 keV K-edge) attenuation caveat, and states the band edges are
  config-declared decision rules (with provenance) rather than unsourced Python
  literals — while still not claiming they are a protective-action guideline.
- `docs/architecture.md` shielding-row span corrected to 0.05–3.0 MeV.
- Manifold variables gained `THREAT_BAND_EDGES_SV_S_CSV` and
  `SHELTER_DOSE_RATE_SV_S` tokens (both consumed by sections: no orphan tokens).

### Gate numbers this round

- pytest: **345 passed, 0 failed, 0 skipped; coverage 100.00%** (`--cov-fail-under=90`)
- ruff check: clean · ruff format --check: clean (45 files) · mypy: clean (19 files)
- Regeneration: two consecutive `z_generate_manuscript_variables.py` runs are
  byte-identical (same SHA-256 of all JSON+MD artifacts under `output/`).
- `docs/_generated/COUNTS.md` regenerated by the new `scripts/z_generate_counts.py`
  (D1) from a real run: 345 passed / 100.00%.

### What this round deliberately did NOT do (left for a future round)

- **V2** — Pasquill–Gifford reference values still live in
  `tests/test_plume_model.py` rather than a citable data file; the coefficients
  are transcription-pinned but the reference numbers carry no external
  page-level provenance.
- **V4** — `dr_no` still has no package-local cross-film chain binding test
  (the harness lives in `_omnibus/` outside this tree).
- **D1 residual** — `scripts/z_generate_counts.py` writes COUNTS.md from a real
  run, but an *in-suite* test asserting the committed file equals a fresh
  measurement was intentionally not added: it would re-run the whole suite
  inside the suite (changing the very count it validates) and recurse. Left as
  a fleet-level docs-gate responsibility.
- **D2** — dose coefficients and gamma constants are cited as blocks, not per
  row; a reader cannot audit one constant in isolation without re-deriving the
  whole table.
- **E1–E4** — Compton continuum (E1), escape-peak/summing (E2), plume
  deposition (E3), and `bond-utilities` provenance delegation (E4) remain real
  extension work, unchanged from their earlier sections above.

## Workflowz review — 2026-11-10

### Documentation

**W1. [P2] Retire completed open-work entries so TODO.md again tracks only unfinished work.** TODO.md says it tracks only what is not done (`TODO.md:20-21`), but C1 still specifies the obsolete 0.1–2.0 MeV range (`TODO.md:29-50`) while production now declares 0.05–3.0 MeV (`src/dr_no/shielding.py:99-106`) and regression coverage is documented (`tests/test_shielding.py:130-135`). C2 remains open (`TODO.md:52-64`) although the doublet regression says absorbed energies are now exposed through `merged_energies` (`tests/test_isotope_profiles.py:215-222`). C3 remains open (`TODO.md:66-79`) although the canonical path now reads `mission.threat.band_edges_sv_s`, retaining only a documented standalone-domain fallback (`src/dr_no/island_assessment.py:98-102`). V1 and D1 likewise remain listed (`TODO.md:83-94`, `TODO.md:148-158`) despite their binding test and generator (`tests/test_claim_ledger.py:1-15`; `scripts/z_generate_counts.py:1-7`). *Done when:* C1, C2, C3, V1, and D1 are removed from Open work or moved to a clearly dated completed-work record with current evidence; V3 is reconciled against the reported 100% coverage (`TODO.md:10-18`, `TODO.md:112-129`), while genuinely unresolved entries remain open. No scientific behavior or frozen provider surface changes. *Demonstrate:* from the repository root, run `uv run pytest tests/test_shielding.py tests/test_isotope_profiles.py tests/test_scenario.py tests/test_island_assessment.py tests/test_canonical.py tests/test_claim_ledger.py -q` and expect all selected tests to pass; then run `uv run python scripts/z_generate_counts.py && git diff --exit-code docs/_generated/COUNTS.md` and expect the generated counts file to remain unchanged.
