# Assumptions

Every number the simulation uses, and where it came from. Three labels are used:

- **Reported** - taken from a published tariff, regulator document or news report. Still worth re-checking.
- **Assumed** - a modelling choice. Not measured, not sourced.
- **Placeholder** - a stand-in that is known to be wrong in detail and should be replaced.

Everything lives in `config/scenario.yaml`, so each value can be changed without touching code.
No claim here is a measurement from a real home.

---

## 1. Weather data

| Item | Value | Label | Notes |
|---|---|---|---|
| Location | Islamabad, 33.6844 N, 73.0479 E | Reported | Open-Meteo grid cell, not a specific rooftop |
| Month simulated | June 2025 | - | One real summer month, 720 hours |
| Actual weather | Open-Meteo **archive-api** | Reported | `shortwave_radiation`, `temperature_2m`, `cloud_cover` |
| Day-ahead forecast | Open-Meteo **historical-forecast-api**, `*_previous_day1` | Reported | The forecast as issued the day before |
| Mean daily radiation | 6.15 kWh/m2 | Generated | From the cached data |
| Mean temperature | 31.7 C (max 44.3 C) | Generated | From the cached data |

### A finding about the forecast source

The build brief gave this URL for archived forecasts:

```
https://historical-forecast-api.open-meteo.com/v1/forecast?...&hourly=shortwave_radiation,...
```

Checked against the archive for all 720 hours of June 2025, **it returns identical values** -
0 of 720 hours differ in radiation or temperature. Used as the agent's forecast it would
hand the agent a perfect forecast: margin near zero, confidence always 100%, and no refusals
ever. The brief's documented fallback (use the actual weather as the forecast, with confidence
from cloud cover) has the same defect, since forecast error would again be exactly zero.

So this project uses the **`*_previous_day1`** variables on the same endpoint, which return the
forecast as it was actually issued one day earlier. Measured over June 2025:

| | Value |
|---|---|
| Month mean absolute radiation error | 52.7 W/m2 |
| 80th-percentile absolute error at 12:00 | 212 W/m2 (about 0.85 kW for a 5 kW system) |
| Direction of error | Positive at every daylight hour - the forecast is consistently **too optimistic about sun** |

That last row is why a safety margin matters: an agent that believed the forecast would
routinely over-commit.

### Radiation time alignment

Open-Meteo hourly radiation is the **mean over the preceding hour**, so the value stamped
`12:00` covers 11:00-12:00. The simulation treats hour `h` as covering `[h, h+1)`, so both the
actual and the forecast series are shifted back by one hour. One extra day is fetched so the
last hour of the month has a real partner; no values are invented. Temperature and cloud cover
are instantaneous readings and are not shifted.

---

## 2. Solar

| Item | Value | Label | Notes |
|---|---|---|---|
| System size | 5 kW | Assumed | `solar_kw` in config |
| Output model | `solar_kw x GHI/1000 x 0.80` | Assumed | Derate covers heat, dust and wiring |
| Derate | 0.80 | Assumed | A common rule of thumb, not measured for this roof |
| Tilt and azimuth | **Not modelled** | - | v0 treats the array as flat-plate on global horizontal irradiance. A real roof at a tilt would generate a different daily shape, usually more in the morning and evening and less at noon. |
| Shading, soiling over time, panel ageing | **Not modelled** | - | |
| Inverter clipping | **Not modelled** | - | |

---

## 3. Household demand

| Item | Value | Label |
|---|---|---|
| Base load, 00:00-06:00 | 0.30 kW | Assumed |
| Base load, 06:00-18:00 | 0.40 kW | Assumed |
| Base load, 18:00-24:00 | 0.60 kW | Assumed |
| AC rated power | 1.5 kW per unit | Assumed |
| AC switches on above | 30 C | Assumed |
| AC at full duty from | 40 C | Assumed |
| AC duty curve | linear, 0.5 at 30 C to 1.0 at 40 C | Assumed |
| AC hours | 13:00-18:00 at half duty, 18:00-06:00 at full duty | Assumed |
| `low_use` | 1 AC, protected-eligible | Assumed |
| `high_use` | 2 ACs, not protected-eligible | Assumed |

### The `low_use` calibration

With the brief's literal defaults and real June 2025 weather, the `low_use` baseline came to
about **341 grid units/month**, not the 150-200 the brief targets. `high_use` came to about
502, already inside the brief's 400+ band.

Rather than quietly editing several numbers, there is **one knob**: `load_scale`, which
multiplies base load and AC power together for a household. A bisection solver sets it so the
reference baseline (usual mode, no battery, no exporting) lands on a configurable target.

| Item | Value | Label |
|---|---|---|
| `calibration.low_use_target_units` | 175 units | **Assumed** - midpoint of the brief's 150-200 band |
| Solved `low_use` load_scale | 0.5578 | Generated |
| Achieved baseline | 175.0 units | Generated |
| `high_use` load_scale | 1.0 (untouched) | - |

**The 175-unit target is an assumption, not a measurement.** It is the single value to replace
once a real electricity bill is available. Changing it and running
`python -m src.simulate --all --calibrate` re-solves the scale and regenerates every result.

The calibration deliberately uses one fixed reference scenario so the scale does not drift
between scenarios.

---

## 4. Flexible appliances

| Appliance | Power | Duration | Days | Usual start | Allowed window | Label |
|---|---|---|---|---|---|---|
| Water motor | 0.75 kW | 1 h | every day | 19:00 | 08:00-18:00 | Assumed |
| Washing machine | 0.5 kW | 1 h | 4 per week | 18:00 | 09:00-17:00 | Assumed |
| Iron | 1.0 kW | 0.5 h | every day | 20:00 | 09:00-18:00 | Assumed |

Usual start times are placeholders for survey results. Which days the washing machine runs is a
fixed rule based on the day of the month, not a random draw, so results are reproducible.

**Scheduling note:** when the agent *moves* an appliance it must land inside the allowed window.
When it *refuses*, it keeps the usual start time, which may sit outside that window by design -
19:00 and 20:00 are outside the shifting windows. A refusal is "leave things as they are".

---

## 5. Pre-cooling

| Item | Value | Label |
|---|---|---|
| Extra AC energy used, 14:00-17:00 | 1.0 kWh | **Assumed - rough estimate** |
| Evening AC energy saved | 0.6 kWh | **Assumed - rough estimate** |
| Triggers when forecast evening temperature reaches | 35 C | Assumed |

**This is the weakest assumption in the project.** The 1.0 kWh to 0.6 kWh ratio is a guess about
how well a Pakistani home holds cool air. It is a net energy loss by construction (0.4 kWh),
justified only by moving demand off the evening peak. It depends on insulation, ceiling height,
window area and how long doors stay open - none of which v0 models. A real figure needs
measurement in an actual home. Disabling pre-cooling changes the main scenario's monthly grid
units by less than 1 unit, so no headline result rests on it.

---

## 6. Battery

| Item | Value | Label |
|---|---|---|
| Capacity | 5 kWh | Assumed |
| Maximum charge and discharge | 2.5 kW | Assumed |
| Round-trip efficiency | 90% | Assumed |
| Minimum charge level | 20% of capacity | Assumed |
| Charge at the start of the month | 50% | Assumed |
| Degradation over time | **Not modelled** | - |
| Charging from the grid | **Never** - surplus solar only | Assumed |

Efficiency is applied as the square root of the round-trip figure on each of charge and
discharge, so a full cycle loses 10% in total.

---

## 7. Power cuts

| Item | Value | Label |
|---|---|---|
| Default outage | one hour daily, 20:00-21:00 | Assumed |
| Grid import during an outage | forced to zero | By definition |
| Exporting during an outage | not possible | By definition |
| **Essential load on backup** | **0.30 kW** (fans, lights, router) | **Assumed** |
| AC and flexible appliances during an outage | **do not run** | Assumed |
| Load that cannot be served | counted as **unmet**, in kWh and hours | - |

**Only essential loads run during a power cut.** The AC and the flexible appliances are treated as
off, so the battery reserve is sized to the essential energy of the cut rather than to full
household load. A home with a large battery that really would run its AC through an outage is not
represented.

An appliance whose habitual time falls inside an outage is **deferred to when power returns**, in
both usual and agent modes. Without this the iron (usual 20:00, inside the default cut) silently
never ran, removing about 15 kWh a month from the baseline and making the agent look worse than it
is.

**Simplification:** during an outage the home is assumed to keep running on solar plus battery,
which requires a **hybrid inverter**. Many Pakistani rooftop systems use plain grid-tie
inverters that shut down completely when the grid fails, for the installer's safety, and would
deliver nothing at all during a cut. v0 models the more capable hardware.

Outage timing is the same every day, which is unrealistic - real load-shedding varies by day,
area and season.

---

## 8. Tariff

Based on the 2026 tariff as reported (S.R.O. 279(I)/2026). **Every rate below should be verified
against NEPRA before being quoted anywhere.** Rates are revised periodically.

### Protected (telescopic, each slice at its own rate)

| Units | Rate | Label |
|---|---|---|
| 1-100 | Rs 10.54 | Reported |
| 101-200 | Rs 13.01 | Reported |

### Unprotected (non-telescopic - the band reached sets the rate for *every* unit)

| Band | Rate | Fixed charge | Label |
|---|---|---|---|
| 1-100 | Rs 22.44 | Rs 275/kW | Reported |
| 101-200 | Rs 28.91 | Rs 300/kW | Reported |
| 201-300 | Rs 33.10 | Rs 350/kW | Reported |
| 301-400 | Rs 36.46 | Rs 400/kW | Reported |
| 401-500 | Rs 38.95 | Rs 500/kW | Reported |
| 501-600 | Rs 40.22 | Rs 675/kW | Reported |
| 601-700 | Rs 41.85 | Rs 675/kW | Reported |
| Over 700 | Rs 47.20 | Rs 675/kW | Reported |

The earlier version of this project interpolated six of these eight rates and flagged them as
placeholders. They are now the reported figures, used verbatim from `config/scenario.yaml` with no
interpolation anywhere in the code.

**Fixed charges** are Rs per kW of sanctioned load, applied to the band the month reaches. All
values are the reported S.R.O. 279(I)/2026 figures and **should still be verified against NEPRA**.
Protected and unprotected consumers have separate tables:

| Protected band | Fixed charge |
|---|---|
| 1-100 | Rs 200/kW |
| 101-200 | Rs 300/kW |

Sanctioned load defaults to **5 kW** (assumed), so a protected home on 150 units pays Rs 1,500 of
fixed charges. Protected consumers are **not** exempt
(`fixed_charge_applies_to_protected: true`).

Note that the fixed charge often cancels out of the six-month penalty, because a home just under
200 units sits in the same band position on both tables (Rs 300/kW either way).

### The cost of crossing 200 units

| Units | Pricing | Bill |
|---|---|---|
| 199 | protected | Rs 2,342 |
| 201 | unprotected | Rs 6,653 |

Two extra units, and the bill nearly triples, because all 201 are re-priced.

`six_month_penalty_rs` estimates what the **following** months cost. A month above the limit can
never itself be billed at protected rates, so the penalty is not that month's own gap. It is the
cost of staying unprotected for six months even once usage is back under 200, priced at the
agent's own monthly usage and **assuming that usage holds steady** - an assumption, not a forecast.
For the `at_risk` home, which the agent brings down to 181.4 units, that is about **Rs 18,788**.
It is reported separately from the crossing month's own difference of Rs 5,003.

### Other tariff settings

| Item | Value | Label |
|---|---|---|
| Protected threshold | 200 units | Reported |
| Months of unprotected pricing after crossing | 6 | Reported |
| `taxes_multiplier` | 1.0 | **Assumed** - GST, duty, TV fee and fuel-price adjustments are **not** included, so every bill here is lower than a real one |
| Net billing export rate | Rs 11/unit | **Reported but contested** - applies to new users from Feb 2026; existing users keep earlier terms until their 7-year contracts end. Never used as a headline number, and shown separately from the cost of units bought rather than netted into one figure. |
| Net metering | 1:1 unit offset | Comparison only - being withdrawn for new users |
| Export under `none` | Rs 0, surplus wasted | By definition - an unregistered home cannot sell |

## 9. The agent

| Item | Value | Label |
|---|---|---|
| Planning time | 20:00 the evening before | Assumed |
| Margin | 80th percentile of past absolute errors for that hour of day | Assumed |
| Days of history before the learned margin is used | 5 | Assumed |
| Margin before then | `predicted solar x cloud-cover fraction` | Assumed |
| Confidence shown to the family | `1 - total margin / total predicted solar`, as a percentage | Assumed |
| Guard threshold | 200 units, plus every non-telescopic band edge | Assumed |
| Minimum days before the guard projects | 10 | **Assumed** - a projection from fewer days is off by hundreds of units in June |
| Overshoot at which an edge is abandoned | 20% | Assumed |
| Share of suggestions the family acts on | **70%**, in steps of 10, on a fixed pattern of days | **Assumed - to be set from the survey** |

Every notification records which margin rule produced it, as `margin_source`:
`cloud-cover` for the first five days, `learned` afterwards.

Measured over the main scenario: mean forecast error **52.7 W/m2**, mean margin held back
**0.257 kW per hour**, **2 refusals**, **131 messages**, **52 promises made and 51 kept (98.1%)**.

**Compliance.** Battery planning is automatic and always applies. Appliance timing and pre-cooling
need someone to act, so on the 30% of days nobody does, those revert to habit and the agent logs
an `ignored` message. The 70% figure is an assumption; at 100% the main scenario reaches 53.7
units and at 30% it reaches 78.6, so the headline numbers are deliberately not a best case.

**Promises.** Each shift the family acted on is recorded and later judged against *actual* solar,
not against the forecast. The single broken promise in the main scenario was made at 57%
confidence - the agent was least certain about the one it got wrong.

---

## 10. What is not modelled at all

- Tilt, azimuth, shading, soiling and panel ageing
- Inverter clipping and standby losses
- Battery degradation
- Thermal physics - pre-cooling is a flat energy trade, not a heat model
- Any behaviour other than the modelled appliances; nobody ignores a notification
- Time-of-use pricing: the tariff is flat by hour, so moving demand between daytime hours has no direct bill effect
- Whether a family would actually defer ironing to 21:00 rather than skip it
- Taxes, duties, fuel-price adjustments and fixed charges
- The six-month consequence of losing protected status
- Day-to-day variation in load-shedding
- More than one month, one location and one weather year

---

## 11. How to replace these with real numbers

In rough order of how much each would improve the results:

1. **A real electricity bill** - fixes `calibration.low_use_target_units`, the unprotected band
   rates and `taxes_multiplier`.
2. **Survey results** - fix `usual_times`, how many homes have batteries, and typical outage hours.
3. **A measured pre-cooling trial** - fixes the 1.0 to 0.6 kWh guess.
4. **An inverter data export** - would replace the solar model and derate entirely.
5. **Local load-shedding schedules** - replace the fixed daily outage window.

After changing anything in `config/scenario.yaml`:

```bash
python -m src.simulate --all --calibrate
```
