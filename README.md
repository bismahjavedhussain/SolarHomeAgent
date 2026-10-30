# Solar Home Agent (Pakistan) - prototype v0

**A simulation of a rooftop-solar home in Islamabad, run twice: once the way families behave
today, and once with an agent that plans each day from the weather forecast and refuses to act
when it is not confident.**

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

**Main scenario** - a low-use home, 5 kW of panels, with a 5 kWh battery, not registered to sell
power, with a one-hour power cut each evening:

| | Usual | Agent | Change |
|---|---|---|---|
| Units bought from the grid | 85.4 | **63.6** | −26% |
| Evening units (18:00–22:00) | 15.7 | **0.0** | eliminated |
| Highest single-hour grid draw | 1.02 kW | **0.84 kW** | −18% |
| Load unserved during power cuts | 11.2 kWh (16 h) | **0.0 kWh (0 h)** | eliminated |
| Units per 100 kWh **actually served** | 25.2 | **17.8** | −29% |
| Estimated bill | Rs 900 | Rs 670 | protected rate kept in both |

Across all **12 scenarios** (household × battery × export mode):

- **Evening grid units fall in all 12.** This is the agent's core job and the number the grid
  cares about.
- **Total grid units fall in 9 of 12.** The exceptions are the three `high_use` + battery
  scenarios, where the agent buys **4.2 units more** (352.8 → 357.0) - and serves **46.2 kWh more
  of the family's actual demand**, cutting time without power from 28 hours to 21. It is a
  trade-off, and it is reported as one.
- The agent **refused to move an appliance twice**, sent **122 messages**, and held back an
  average of **0.257 kW** of solar per hour as its safety margin.

### Why "units per 100 kWh served" is reported

During a power cut, a home with an empty battery goes dark, and power that was never delivered
never appears on the bill. So a home that fails its family can look *thriftier*. Comparing modes
on units bought alone is misleading whenever unserved load differs, so unserved load and units
per 100 kWh served are reported alongside.

### What the agent does not fix

The home still **wastes 433.5 kWh of solar in the month** (down from 472.9). It generates 738.3
kWh and uses only 41.3% of it on site. A 5 kWh battery cannot absorb a sunny June day, and an
unregistered home cannot sell the rest. **Most surplus noon solar is still thrown away** - no
amount of household scheduling fixes that. It needs registration, bigger storage, or a grid that
can see and use it.

### Where the 200-unit guard stands

In the main scenario the guard **never activates**, because the agent keeps the home at 63.6
units - far below the threshold. It is a safety net this scenario did not need, not an
achievement. Tests confirm it activates on 22 of 30 days for a protected-eligible home that is
genuinely on course to cross.

---

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
| `household` | `low_use` (1 AC, protected-eligible) / `high_use` (2 ACs) |
| `solar_kw` | default 5 |
| `power_cuts` | list of `[start, end]` hours; `[]` for none |
| `usual_times` | habitual start hour per appliance |
| `calibration.low_use_target_units` | the monthly units `low_use` is calibrated to (default 175, **assumed**) |

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

`python -m pytest -q` - **41 tests**:

- The hourly energy balance holds in both modes, in every scenario (currently to ~4×10⁻¹⁶ kWh).
- Battery charge stays within its minimum and capacity; power limits are never exceeded.
- No grid import, and no export, during a power cut.
- Appliances the agent moves land inside their allowed window and run their full duration;
  refused appliances keep their usual time.
- Protected and unprotected pricing, the switch at 200 units, non-telescopic bands, and export
  values per mode.
- The agent never exports while the battery still has room.
- Guard mode activates when a protected home is on course to cross 200 units, and stays off when
  it is not.
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
- Six of the eight unprotected tariff rates are **placeholders** - straight-line interpolation
  between the reported lowest and highest bands.
- Taxes, duties and fuel-price adjustments are **excluded**, so every bill shown is lower than a
  real one.
- Assumes a **hybrid inverter** that keeps working during a power cut; many real systems shut down
  completely, and would deliver nothing.
- No tilt or shading model, no battery ageing, no thermal physics.
- Assumes the family always acts on the notification. Real families will not.
- The six-month penalty for losing protected status is flagged but not simulated, so the real cost
  of crossing 200 units is understated.

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
