# Architecture — CRAB KEY (dr_no)

Module-by-module architecture of `src/dr_no/`, how the pieces compose, and how
`mission.py` implements the frozen `bond_api` `MissionProvider`.

## 1. The shape of the package

CRAB KEY is a **pure domain core** with a **thin protocol adapter** bolted on
one edge and a **thin CLI** on another. Fourteen modules, three layers:

```
        manuscript/config.yaml          <-- the declared scenario (source of truth)
                  |
                  v
            scenario.py                 LAYER 0  configuration
                  |
    +-------------+---------------------------------+
    |             |                                 |
    v             v                                 v
isotope_profiles  plume_model      decay_chain  shielding  dose_assessment
       |          spectrum_processing       |        |          |
       |             |                      |        |          |
       +------+------+----------+-----------+--------+----------+
              |                 |
              v                 v
        island_assessment    (all of the above)     LAYER 1  domain models
              |                 |
              +--------+--------+
                       v
                  canonical.py                      LAYER 2  the single metric pass
                       |
         +-------------+--------------+-------------+
         v                            v             v
    mission.py                manuscript_variables  figures/plots.py
    (bond_api adapter)        (report tokens)       (figures)
         |                            |                    LAYER 3  consumers
         v                            v
      cli.py                  scripts/z_generate_...
      scripts/run_mission.py
```

Dependency direction is strictly downward. Nothing in Layer 0–2 imports
`bond_api`; only `mission.py` and `cli.py` do.

## 2. Module inventory

### Layer 0 — configuration

**`scenario.py`** — loads and validates the `mission:` block of
`manuscript/config.yaml` into frozen dataclasses: `DetectorSpec`, `PlumeSpec`,
`FacilitySpec`, `DecayProjectionSpec`, `ShieldingProbeSpec`, `DosePropeSpec`,
and the aggregate `MissionScenario`. `load_scenario()` caches per resolved path.

The loader is **strict by design**: every required key raises `KeyError` when
absent, every value raises `TypeError` on the wrong YAML type and `ValueError`
when out of range. There are no fallback defaults, because a default is exactly
how a config silently stops describing the computation. It also rejects `bool`
where a number is expected (`bool` subclasses `int`) and rejects YAML strings
that merely *look* numeric — PyYAML's YAML 1.1 resolver parses `2.0e6` as a
string, and `float("2.0e6")` would have accepted it.

`MissionScenario.as_payload()` produces the JSON-safe mapping used as the
provenance hash input, so a scenario edit changes the recorded hash.

### Layer 1 — domain models (pure, no config, no protocol)

**`isotope_profiles.py`** — the forensics core. A 10-isotope library of real
gamma emission lines (`IsotopeProfile`: name, half-life, `(energy, intensity)`
lines); `synthesize_spectrum()` builds a binned spectrum by placing a Gaussian
photopeak of integrated area `A·t·ε·I` per line, with FWHM growing as √E
anchored at the Co-60 1332.5 keV line, on a flat continuum; `detect_peaks()`
finds local maxima above an SNR floor and collapses near-duplicates;
`identify_isotopes()` scores each library isotope by summed matched intensity
scaled by √(matched fraction); `estimate_activity()` inverts the synthesis model
exactly.

**`spectrum_processing.py`** — quantification. `calibrate_energy()` fits a
least-squares linear channel→energy calibration returning gain, offset,
per-point residuals and R². `net_peak_area()` computes gross counts minus a
linearly interpolated continuum over a symmetric region, with Poisson-propagated
uncertainty `√(gross + background)`. `minimum_detectable_activity()` applies the
Currie limit `L_D = 2.71 + 4.65√B` and converts it to Bq.

**`decay_chain.py`** — time dependence. Five real parent→daughter chains
(`Nuclide`, `DecayChain`); `populations_at_t()` evaluates the Bateman solution
with coefficients built so every daughter starts at zero; `activities_at_t()`
converts through `A = λN`; plus `transient_equilibrium_ratio()`,
`activity_fraction_remaining()`, and `time_to_fraction()`.

**`shielding.py`** — barriers. Mass-attenuation tables (`μ/ρ`, cm²/g) for lead,
iron, concrete, and water over 0.1–2.0 MeV, plus densities.
`mass_attenuation()` interpolates log-log between bracketing table points;
`linear_attenuation_coefficient()` gives `μ = (μ/ρ)ρ`; then
`transmission_factor()`, `half_value_layer()`, `tenth_value_layer()`, and
`required_shield_thickness()`.

**`dose_assessment.py`** — dose accounting. Per-isotope inhalation dose
coefficients (Sv/Bq) and specific gamma-ray constants (mSv·m²·h⁻¹·GBq⁻¹);
`external_dose_rate()` (inverse-square point source),
`shielded_external_dose_rate()`, `dose_rate_from_concentration()`
(breathing-rate-weighted inhalation), `combined_dose_rate()`, and
`integrated_dose()`.

**`plume_model.py`** — atmospheric transport. The steady-state Gaussian plume
with ground reflection, over Pasquill–Gifford classes A–F in the power-law
coefficient form (`StabilitySpec`, `STABILITY_TABLE`). `sigma_y`/`sigma_z` give
the dispersion coefficients; `gaussian_plume_concentration()` and
`centerline_concentration()` the field; `grid_concentration()` a 2-D field;
`find_ground_level_max()` the crosswind maximum; `isopleth_extent()` the
downwind extent above a threshold.

> **`isopleth_extent` is deliberately two-stage.** The ground-level centreline
> profile of an *elevated* release is unimodal, not monotone — near zero at the
> stack, peaking downwind, then decaying. It therefore scans for the maximum
> first and bisects only the decaying tail. A single bisection seeded at the
> release point assumes a monotonicity that does not exist and returns a
> confidently wrong distance. See `tests/test_defect_regressions.py`.

**`island_assessment.py`** — the decision layer. `DetectedFacility` and
`Meteorology` in, `IslandAssessment` out. Per facility it takes the plume
concentration at its position, converts it to an inhaled dose rate through its
isotope mix, maps that onto five threat bands (escalating one band if
containment is breached), and picks a containment action. Both decision
thresholds — evacuation dose rate and action concentration — are parameters
threaded from the scenario, not baked-in constants.

### Layer 2 — the single metric pass

**`canonical.py`** — computes *every* reported metric, once, from a
`MissionScenario`. This is the module that guarantees the mission outcome and
the manuscript cannot disagree: both call `canonical_metrics()`. It also owns
`canonical_spectrum()`, `detector_energy_grid()`, and `line_intensity()`.

`_calibration_from_peaks()` **raises** when fewer than two detected peaks match
a declared calibration line rather than returning a zero gain — a zero would
render in the manuscript as a plausible-looking calibration.

### Layer 3 — consumers

**`mission.py`** — the BOND-API adapter (see §3).
**`cli.py`** — a phase driver mapping `brief|recon|plan|execute|debrief|full|render`
onto the provider; exit codes 0 / 1 / 2.
**`util_render.py`** — deterministic key-sorted text rendering of protocol
dataclasses, kept out of `cli.py` so the driver stays structural.
**`manuscript_variables.py`** — hydrates every `{{TOKEN}}` from the scenario plus
`canonical_metrics()`, and resolves numbered manuscript sections into
`output/manuscript/`.
**`figures/plots.py`** — three deterministic figures. `plot_gamma_spectrum()`
renders the *canonical* spectrum (same grid, same mixture as the metrics),
`plot_plume_field()` the declared plume including its release height, and
`plot_decay_curves()` the declared chain.

## 3. How `mission.py` implements the frozen MissionProvider

`bond_api.protocol.MissionProvider` is a `Protocol`; `dr_no.mission.MissionProvider`
satisfies it structurally — there is no inheritance, and
`isinstance(provider, MissionProvider)` against the runtime-checkable protocol is
asserted in `tests/test_mission.py`.

**The frozen public surface — do not change its shape.** `bond-cli`, the
coordinator's reconcile pass, and the orchestrator consume it across packages:

| Symbol | Contract |
| --- | --- |
| `MissionProvider` (module top level) | the provider class itself |
| `MissionProvider.film` | the slug, `"dr_no"` |
| `.brief() -> MissionBrief` | codename, objectives, assets, constraints |
| `.recon(ReconRequest) -> ReconReport` | findings describing the threat surface |
| `.plan(MissionBrief) -> MissionPlan` | seven ordered `Step`s |
| `.execute(MissionPlan) -> MissionOutcome` | `results` + `Provenance` |
| `.debrief(MissionOutcome) -> Debrief` | outcome + standing lessons |
| `GADGETS` (module-level dict) | eight Q-branch entries |
| `GADGET_REGISTRY`, `MISSION_REGISTRY` | populated at import time |

The adapter is intentionally thin. `brief()` reads its codename and asset
payloads from the scenario; `plan()` names the seven pipeline steps;
`execute()` calls `canonical_metrics()` and adds only two plan-derived counts
(`steps_planned`, `facilities_assessed`) — it recomputes nothing.
`tests/test_mission.py::test_execute_results_match_canonical_metrics` asserts
exactly that.

`Provenance` records the package version, the scenario-declared seed, a
16-character SHA-256 prefix over the whole declared scenario, and a fixed
`wall_time_s` of 0.0 so artifacts stay byte-stable. The seed is recorded for
audit, not consumed — nothing in the computation is stochastic.

Discovery works because `src/dr_no/mission.py` exists and `src/` is on
`sys.path`; `bond_api.discovery.load_provider("dr_no", search_paths=[...])` is
exercised in the test suite.

## 4. Boundary rules

| Surface | Rule |
| --- | --- |
| `scenario.py` | stdlib + PyYAML only. No `bond_api`, no `infrastructure`. |
| `isotope_profiles`, `spectrum_processing`, `decay_chain`, `shielding`, `dose_assessment`, `plume_model` | stdlib + numpy. No config I/O, no `bond_api`. |
| `island_assessment.py` | may import `plume_model` + `dose_assessment`. No `bond_api`. |
| `canonical.py` | may import `scenario` + all domain modules. No `bond_api`. |
| `manuscript_variables.py`, `figures/plots.py` | may import `canonical` + `scenario`. No `bond_api`. |
| `mission.py`, `cli.py` | the **only** modules importing `bond_api`. |
| `scripts/` | thin argv-forwarding wrappers. No business logic. |

Everything below `mission.py` must stay importable **without** bond-api, so a
broken protocol dependency can never take the forensics down.

## 5. Data flow, end to end

```
manuscript/config.yaml
   │  (scenario.load_scenario — strict validation)
   ▼
MissionScenario ──────────────┬──────────────────┬─────────────────┐
   │                          │                  │                 │
   ▼                          ▼                  ▼                 ▼
canonical_metrics()   figures/plots.py   manuscript_variables   mission.brief()
   │  (one pass over all seven domain models)     │                 │
   ├──────────────┬───────────────────────────────┘                 │
   ▼              ▼                                                 ▼
mission.execute() {{TOKEN}} map ──► output/manuscript/     Provenance(seed,
   │                    └──► output/data/manuscript_variables.json   input_hash)
   ▼
MissionOutcome ──► debrief ──► cli / orchestrator
```

The load-bearing property: `canonical_metrics()` is called by both the mission
provider and the token hydrator, over the same `MissionScenario`. There is one
computation and two observers of it.
