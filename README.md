# Solar Home Agent (Pakistan) - prototype

**A simulation of a rooftop-solar home in Islamabad, run twice: once the way families behave
today, and once with an agent that plans each day from the weather forecast and refuses to act
when it is not confident.**

**Live demo:** _<!-- PLACEHOLDER: paste the Streamlit Community Cloud URL here once deployed -->_
`https://<your-app>.streamlit.app`

> **This is a simulation, not a measurement.** Every number below comes from running the code in
> this repository against one real month of weather (June 2025, Islamabad). Nothing here is
> evidence of savings in a real home. The assumptions are listed in
> [ASSUMPTIONS.md](ASSUMPTIONS.md), and several are rough estimates or placeholders.
> Prototype v0, currently being built.

---

## The problem

Pakistan has a very large amount of rooftop solar, and the grid can barely see it.

- **Most of it is unregistered.** Estimates of small-scale solar range from about **27 to 33 GW**,
  while only about **7 GW** is net-metered (official figures, June 2026). The exact total is
  genuinely uncertain.
- **An unregistered home cannot sell its surplus.** When the panels make more than the house is
  using at that moment, the inverter simply backs off. The power is not sold, not stored - it is
  never generated at all.
- **Solar peaks at the wrong time.** Panels work hardest around noon. Pakistani homes need power
  most in the evening, when the sun has gone and the AC is still running.
- **The 200-unit cliff.** A home at or under 200 units a month gets a cheap "protected" rate. Go
  over 200 once and the home is "unprotected" for six months - and unprotected pricing is
  *non-telescopic*, so the band the month reaches sets the price for **every** unit. In this
  project's own tariff model, 199 units costs Rs 2,342 and 201 units costs Rs 5,932.
- **Invisible solar distorts planning.** Because the grid cannot see most rooftop solar, demand
  forecasts are off. Pakistan's long-term demand-forecast plan has been criticised for omitting
  rooftop solar, and the regulator has warned that over-optimistic forecasts lead to over-building
  plants that are paid whether they run or not - which raises tariffs for everyone, including
  families with no solar at all.

Reported figures vary and some are contested. The evidence behind each claim, with its strength,
is set out in [ASSUMPTIONS.md](ASSUMPTIONS.md). The **reported Rs 11/unit net-billing rate is
contested** and is deliberately not used as a headline figure anywhere in this project.

---

## What v0 does

A Python simulation of one home, hour by hour, for one real month, in two modes:

- **Usual** - appliances run at habitual times; the battery, if any, behaves like a plain
  inverter. No forecast, no planning.
- **Agent** - each evening at 20:00 it plans tomorrow from the day-ahead forecast.

The agent:

1. Predicts tomorrow's hourly solar and unavoidable load.
2. **Keeps a safety margin learned from its own past errors** - the 80th percentile of its
   absolute error at each hour of the day. Before it has 5 days of history it uses cloud cover
   instead and **labels every message accordingly**.
3. Moves the water motor, washing machine and iron into hours with confident surplus.
4. **Refuses to move anything when no hour qualifies**, and says why.
5. Pre-cools the house on hot days when the surplus can pay for it.
6. Holds a battery reserve for the evening and the daily power cut, then spends it.
7. Watches the 200-unit threshold and warns the family before they cross it.
8. Checks its prediction against what actually happened, and updates its margin.

Every decision produces a plain-language message with a time, an action, a reason and a
confidence figure.

---

## Results

Full generated figures: **[results/HEADLINE.md](results/HEADLINE.md)**, written by code from
`results/summary.json`. Per-scenario numbers: `results/summary.csv`.

**The clearest case** is a home that currently sits *just over* the 200-unit limit (`at_risk`,
no battery, unregistered). This is where the tariff cliff bites:

| | Usual | Agent | Change |
|---|---|---|---|
| Units bought from the grid | 215.0 | **181.4** | −16% |
| Evening units (18:00–22:00) | 121.4 | **86.9** | −28% |
| Pricing band | **unprotected** | **protected** | limit not crossed |
| Cost of units bought | Rs 7,117 | **Rs 2,114** | −Rs 5,003 |
| Extra cost of 6 months unprotected | Rs 27,400 | **Rs 0** | avoided |

Crossing 200 units re-prices *every* unit for six months. On this month's usage that is about
**Rs 27,400** — a figure that assumes the month's usage repeats, which is an assumption, not a
forecast. The agent's guard fired on 2 days.

**The main scenario** in `config/scenario.yaml` is a low-use home with a 5 kWh battery, already
comfortably under the limit, so there is no cliff to avoid and the gains are smaller:

| | Usual | Agent | Change |
|---|---|---|---|
| Units bought from the grid | 69.7 | **53.4** | −23% |
| Evening units (18:00–22:00) | 10.1 | **3.9** | −61% |
| Units per 100 kWh actually served | 22.4 | **16.9** | −25% |
| Cost of units bought | Rs 735 | Rs 563 | protected rate kept in both |

Across all **18 scenarios** (household × battery × export mode), the agent reduces **both total
and evening grid units in every single one**.

### How much the agent is trusted, and how much it earns that trust

- **Promises kept: 98.1%.** It told the family the panels would cover an appliance 52 times; the
  sun actually delivered on 51 of them. This is the agent marking its own homework against what
  really happened, not against its own forecast.
- **Refused to move an appliance twice**, because no hour was sunny enough to be confident.
- **The family acts on only 70% of suggestions** in these runs, a deliberate assumption. Battery
  planning is automatic and always applies; appliance timing needs someone to act. At 100%
  compliance the main scenario reaches 53.7 units, at 30% it reaches 78.6 — so the headline
  numbers are *not* a best case.
- Average day-ahead forecast error **52.7 W/m²**, average margin held back **0.257 kW per hour**.

### What the agent does not fix

The main-scenario home still **wastes 466.9 kWh of solar** in the month (down from 485.5). It
generates 738.3 kWh and uses only 36.8% of it on site. A 5 kWh battery cannot absorb a sunny June
day, and an unregistered home cannot sell the rest. **Most surplus noon solar is still thrown
away** — no amount of household scheduling fixes that. It needs registration, bigger storage, or a
grid that can see and use it.

### Why "units per 100 kWh served" is reported

During a power cut, only essential loads run and a home with an empty battery goes dark. Power
that was never delivered never appears on the bill, so a home that fails its family can look
*thriftier*. Comparing modes on units bought alone is misleading whenever unserved load differs.

## Running it

Requires Python 3.10+. Tested on Python 3.14.4, Windows 11.

```bash
pip install -r requirements.txt

# Reproduce every result from the cached weather - no network needed
python -m src.simulate --all

# After editing config/scenario.yaml: re-solve the load calibration and rerun everything
python -m src.simulate --all --calibrate

# One scenario in detail
python -m src.simulate --scenario low_use_battery_none

# Re-download the weather (the cached CSVs in data/ are committed, so this is optional)
python -m src.fetch_weather --refresh

# Checks
python -m pytest -q

# Interactive demo
streamlit run app.py
```

Everything is written to `results/`.

### Scenario switches

All in [`config/scenario.yaml`](config/scenario.yaml):

| Switch | Options |
|---|---|
| `has_battery` | `true` / `false` |
| `export_mode` | `none` (unregistered, surplus wasted) / `net_billing` / `net_metering` |
| `household` | `low_use` (under 200 units) / `at_risk` (just over 200) / `high_use` (2 ACs) |
| `solar_kw` | default 5 |
| `power_cuts` | list of `[start, end]` hours; `[]` for none |
| `usual_times` | habitual start hour per appliance |
| `calibration.*_target_units` | monthly units each profile is calibrated to (175 and 215, both **assumed**) |
| `agent.suggestions_followed_pct` | share of advice the family acts on (default 70, **to be set from the survey**) |
| `power_cut_essential_load_kw` | what runs on backup during an outage (default 0.30 kW) |

### Deploying the demo publicly

The app runs entirely from the cached weather in `data/`, so it needs no API keys and no network
access at runtime. To put it on [Streamlit Community Cloud](https://share.streamlit.io):

1. Sign in with the GitHub account that owns this repository.
2. **New app** → pick this repo, branch `main`, main file `app.py`.
3. Under **Advanced settings**, set the Python version to **3.12** (`runtime.txt` also pins it).
4. Deploy, then paste the resulting URL into the **Live demo** line at the top of this README.

`requirements.txt` is pinned to the exact versions this project was tested with. If the cloud
build fails on a wheel, relax that one pin to `>=` and redeploy.

---

## Data

| | Source |
|---|---|
| Actual weather | Open-Meteo **archive-api**, hourly radiation, temperature and cloud cover |
| Day-ahead forecast | Open-Meteo **historical-forecast-api**, the `*_previous_day1` variables |

Both are cached as CSV in `data/` and committed, so the repository runs offline.

**One finding worth stating plainly.** The plain `historical-forecast-api` query returns values
**identical to the archive** - 0 of 720 hours differ for June 2025. Used as the agent's forecast
it would hand the agent a perfect forecast: no error, no margin, no refusals, and a confidence
figure that means nothing. The `*_previous_day1` variables return the forecast as it was actually
issued the day before, which gives a real error to learn from:

- Mean absolute error **52.7 W/m²**
- 80th-percentile error at midday **212 W/m²** (about 0.85 kW for a 5 kW system)
- **Positive at every daylight hour** - the day-ahead forecast is consistently too optimistic
  about sun, which is exactly why a conservative margin matters

Open-Meteo reports hourly radiation as the mean over the *preceding* hour, so both series are
shifted by one hour to line up with simulation hours. One extra day is fetched so no values are
invented at the boundary. Details in [ASSUMPTIONS.md](ASSUMPTIONS.md).

---

## Correctness checks

`python -m pytest -q` - **56 tests**:

- The hourly energy balance holds in both modes, in every scenario (currently to ~4×10⁻¹⁶ kWh).
- Battery charge stays within its minimum and capacity; power limits are never exceeded.
- No grid import, and no export, during a power cut.
- Appliances the agent moves land inside their allowed window and run their full duration;
  refused appliances keep their usual time.
- Protected and unprotected pricing, the switch at 200 units, non-telescopic bands, and export
  values per mode.
- The agent never exports while the battery still has room.
- Guard mode defends every non-telescopic band edge, activates only after enough days to make a
  projection meaningful, and stays off for a home that is comfortably under.
- Only essential load is served during an outage, and nothing is ever scheduled into one.
- Following every suggestion does at least as well as following some of them.
- Promises are judged against real solar, and message wording softens as confidence falls.
- The agent's forecast error is non-zero - a direct guard against the forecast silently becoming
  the actuals.
- Identical inputs produce identical outputs.

---

## Repository layout

```
config/scenario.yaml     every switch and assumption
data/                    cached weather CSVs (committed, so it runs offline)
src/fetch_weather.py     download and cache
src/solar.py             sunlight to panel output
src/home.py              base load, AC, flexible appliances
src/battery.py           capacity, power limits, efficiency
src/tariff.py            protected and unprotected bands
src/baseline.py          usual behaviour
src/agent.py             the agent: margin, refusals, guard, messages
src/simulate.py          hourly dispatch, scenario matrix, CLI
src/metrics.py           monthly metrics
src/plots.py             the three charts
app.py                   Streamlit demo
survey/survey_summary.py survey helper
results/                 generated output
tests/                   41 pytest checks
```

---

## Honest limits

- A **simulation** with stated assumptions. **No claims of real-world savings.**
- One month, one city, one weather year, one home.
- Pre-cooling (1.0 kWh spent to save 0.6 kWh) is **a rough guess**, not measured.
- Tariff band rates are the **reported S.R.O. 279(I)/2026 figures and still need verifying against
  NEPRA**. The per-band fixed charges span the reported Rs 200–675/kW range, but the step pattern
  between those endpoints is **not individually confirmed**.
- The calibration targets (175 and 215 units) are **assumptions**, to be replaced from a real bill.
- The 70% compliance rate is an **assumption**, to be set from the survey.
- Taxes, duties and fuel-price adjustments are **excluded**, so every bill shown is lower than a
  real one.
- Assumes a **hybrid inverter** that keeps working during a power cut; many real systems shut down
  completely, and would deliver nothing.
- No tilt or shading model, no battery ageing, no thermal physics.
- Assumes the family always acts on the notification. Real families will not.
- The six-month penalty for losing protected status is **estimated by assuming the month's usage
  repeats**, not simulated month by month.
- During an outage only essential loads are modelled as running; the AC and flexible appliances do
  not. A home that would really run its AC on a large battery is not represented.

---

## Next steps

1. Replace assumptions with real figures: an electricity bill, survey results, and an inverter
   export. `config/scenario.yaml` is designed so each is a one-line change.
2. Measure pre-cooling in a real home instead of guessing it.
3. Model several months, so the six-month protected-status penalty can be simulated properly.
4. Add a tilt model and real load-shedding schedules.
5. **Neighbourhood forecasting** - combine many homes' forecasts *and their margins* into one
   neighbourhood solar forecast with a confidence band. Not built in v0. This is the part aimed at
   the grid problem: helping the system operator see rooftop solar, and know how much to trust
   what it sees.

---

## Licence and credits

Weather data from [Open-Meteo](https://open-meteo.com/) (free, no key required).
Built as prototype v0 for the IRENA Youth Forum 2027 application.
