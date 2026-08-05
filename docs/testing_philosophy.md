# Testing philosophy — CRAB KEY (dr_no)

Zero-mock, real-data, deterministic testing — and, past that, tests that can
actually fail.

## 1. No mock framework — and four declared substitutions

No `MagicMock`, no `mocker.patch`, no `unittest.mock`, anywhere. Every test
calls the real computation path with real arguments and checks a real result.

Where a branch needs a controlled input we supply a **real object** rather than
a fake one:

- To exercise the "isotope with no emission lines" guard, we construct an
  actual `IsotopeProfile(gamma_lines=())` and put it in a real library dict.
- To exercise the strict config loader's failure modes, we write **real YAML
  files** to `tmp_path` and load them.

Beyond that there are exactly **four** `pytest.MonkeyPatch` substitutions, and
an earlier revision of this page described only one of them. Stated in full:

| Site | Replaces | With |
| --- | --- | --- |
| `test_cli.py` | `cli.SLUG` | a string constant — a value, not behaviour |
| `test_manuscript_variables.py` | `mv.library_names` | `lambda: ()` — a real empty tuple |
| `test_manuscript_variables.py` | `mv.isotope_library` | builtin `dict` — a real empty mapping |
| `test_isotope_profiles.py` | `canonical.isotope_library` | `lambda: extended` — a real dict of real `IsotopeProfile`s |

Three of those four replace a production **callable**, not merely a value, so
"we only swap constants" would be false. What is true, and is the actual line:
none installs an object whose behaviour is scripted by the test, none records or
asserts on calls, and each exists only to reach an empty-input guard that no
real configuration can produce.

That is a claim about the suite, so it is checked by reading the suite's own
source rather than asserted here: `tests/test_suite_hygiene.py` scans every file
under `src/` and `tests/` for mock-framework names and parses every
`monkeypatch.setattr` call out of the AST, failing on any that is not in its
declared inventory — and failing equally if a declared one silently disappears.
A grep for framework names alone, which is what the docs used to point at,
cannot see any of the four.

Real files, real numbers, real matplotlib PNGs, real subprocess invocations for
the script smoke tests.

## 2. Determinism

Nothing in `src/` draws a random number. The scenario is fixed and declared;
the seed in `manuscript/config.yaml` is recorded in provenance for audit rather
than consumed, and the docs say so rather than implying a stochasticity that is
not there.

Tests assert byte-level repeatability directly — `canonical_metrics() ==
canonical_metrics()`, and `execute()` twice over the same plan — so a
nondeterminism regression fails loudly rather than flaking.

Wall-clock time is never persisted. No token, metric, provenance field, or
rendered manuscript section is derived from the clock; the provenance stamp is
`SCENARIO_FINGERPRINT`, a truncated SHA-256 of the committed scenario.

That claim used to be false and the test suite could not see it. A
`GENERATION_TIMESTAMP` token was hydrated from `datetime.now()` and written
into both `output/data/manuscript_variables.json` and the resolved
`output/manuscript/06_reproducibility.md`, so every regeneration produced
different bytes while the docs promised byte-identity. The only assertion
covering that token checked that it was present and non-empty — a shape check
an ISO-8601 clock string passes forever, so it could never go red. Freezing the
clock would not have helped either: pinning `now` proves the formatter is a
function of its input, not that the input is clock-free. The *only* test that
catches this class of breach is one that runs the real generator twice and
diffs the bytes it actually wrote.
`tests/test_regeneration_determinism.py` does that: two consecutive subprocess
runs of `scripts/z_generate_manuscript_variables.py`, SHA-256 per file over
everything persisted under `output/`, with a deliberate delay between the runs
so any clock-derived value would differ.

## 3. Tests that can fail

A test that cannot fail is worse than no test: it reports safety it never
checked. Four disciplines follow from that.

**Known vectors and exact inverses.** Where an exact relation exists we assert
it exactly, not approximately-in-spirit: `estimate_activity()` inverts the
synthesis model; `mass_attenuation()` reproduces every tabulated value and
interpolates log-log to a value computed independently in the test;
`isopleth_extent()` returns a distance at which the concentration equals the
threshold to 1e-6 relative.

**Binding tests, not shape tests.** Asserting that `canonical_metrics()`
returns the right *keys* would pass just as well if the metrics ignored the
configuration entirely — which is precisely the defect this package had. So the
config→metric binding is pinned by *moving the input and asserting the output
moves*, with the exact expected relation wherever the physics gives one:

- doubling the declared release rate doubles the plume concentration (exactly —
  the plume is linear in Q);
- doubling the wind speed halves it (exactly);
- a thicker declared barrier transmits strictly less;
- a longer declared projection leaves strictly less parent activity;
- a stricter action threshold pushes the isopleth strictly further out.

One of these (`test_config_file_edit_reaches_the_metrics`) deliberately goes
through a **real file on disk**, because the in-memory `dataclasses.replace`
variants would all still pass if the YAML loader were bypassed.

**Negative controls on every guard.** Each validation raise has a matching
`pytest.raises`. The strict scenario loader is parametrised over every required
key, every wrong type, and every out-of-range value, so a guard that gets
deleted or inverted fails immediately.

**Regression tests that name the defect.** `tests/test_defect_regressions.py`
holds one test per bug actually found in review, each docstring stating what was
wrong and what the wrong answer used to be. When one fails, the message names
the original defect instead of asserting something generic.

## 4. The manuscript is under test

Three gates in `tests/test_manuscript_variables.py`, in both directions:

1. every `{{TOKEN}}` used in a numbered section must be produced by
   `generate_variables()`;
2. every token produced must be **consumed** by some section — otherwise a
   rename leaves its predecessor in the map forever while the forward gate
   stays green;
3. the results narrative may contain **no bare numeral** in prose (figure
   paths, cross-references, code spans, inline maths, and headings are stripped
   first). Hand-authored numbers do the most damage in Section 3, because they
   read as measurements.

A fourth pins that the token values themselves track the config, so tokens
cannot be computed once and frozen.

`tests/test_version_identity.py` gates the third-copy problem: `pyproject.toml`,
`dr_no.__version__`, and `manuscript/config.yaml` must declare one version.
They had already drifted before this gate existed.

## 5. Coverage gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Line **and** branch coverage (`branch = true` in `pyproject.toml`) on `src/`,
floor 90%. The live measured figure is in `docs/_generated/COUNTS.md` — never
hardcode it in prose that nobody regenerates.

Coverage is a floor, not a goal. High coverage over assertion-free tests proves
nothing; the point of the disciplines above is that the covered lines are
covered by checks that would notice if they broke.

## 6. Test layout

| File | Covers |
| --- | --- |
| `test_scenario.py` | strict config loader: required keys, type guards, range guards, caching, JSON payload |
| `test_isotope_profiles.py` | isotope library, synthesis, peak detection, identification, activity inversion |
| `test_spectrum_processing.py` | energy calibration, net area, Currie MDA |
| `test_decay_chain.py` | Bateman chains, equilibrium, time projection |
| `test_shielding.py` | attenuation, transmission, HVL/TVL, required thickness |
| `test_dose_assessment.py` | external / inhalation / combined / integrated dose |
| `test_plume_model.py` | dispersion coefficients, concentration field, isopleth |
| `test_island_assessment.py` | dose rate, threat bands, containment, aggregation |
| `test_canonical.py` | single-source metrics **and** the config→metric binding |
| `test_mission.py` | BOND-API provider: protocol, flow, registries, discovery, provenance |
| `test_manuscript_variables.py` | token hydration + the three manuscript gates |
| `test_version_identity.py` | one version across pyproject / `__init__` / config |
| `test_defect_regressions.py` | one test per defect found in review |
| `test_suite_hygiene.py` | the no-mock claim, enforced by reading the suite's own source |
| `test_cli.py` | in-process CLI phase driver, exit codes |
| `test_figures.py` | figure generators write real PNGs |
| `test_scripts_smoke.py` | thin scripts exit cleanly and write artifacts |
