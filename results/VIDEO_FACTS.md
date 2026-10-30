# Facts for the video

<!-- Generated from results/summary.json and results/compliance_sweep.json. Every number here comes from a simulation run; none are typed by hand. -->

**Simulated month:** 2025-06 - **Location:** Islamabad
**Default scenario:** `at_risk_nobattery_none`
**Forecast source:** Open-Meteo historical-forecast API, *_previous_day1 (day-ahead forecast)

> Everything below is output from a **simulation**, not measurements from a real home.
> Assumptions are listed in ASSUMPTIONS.md; several are rough estimates.

---

## Every scenario (usual -> agent)

Only the `none` export mode is shown: export mode changes the bill, never the units bought.

| Scenario | Grid units | Evening units | Pricing band | Est. bill before taxes (Rs) | Protected kept | 6-month figure (Rs) | Hours w/o power | Promises kept | Refusals |
|---|---|---|---|---|---|---|---|---|---|
| `low_use_nobattery_none` | 175 -> **140.5** | 103.2 -> **68.9** | protected -> **protected** | 3,530 -> **3,081** | True -> **True** | - | 30 -> 30 | 98.1% | 2 |
| `low_use_battery_none` | 69.7 -> **53.4** | 10.1 -> **3.9** | protected -> **protected** | 1,735 -> **1,563** | True -> **True** | - | 0 -> 0 | 98.1% | 2 |
| `at_risk_nobattery_none` | 215 -> **181.4** | 121.4 -> **86.9** | unprotected -> **protected** | 8,867 -> **3,614** | False -> **True** | 18,788 | 30 -> 30 | 98.1% | 2 |
| `at_risk_battery_none` | 108.4 -> **88.3** | 23.4 -> **8.8** | protected -> **protected** | 2,664 -> **1,931** | True -> **True** | - | 5 -> 2 | 98.1% | 2 |
| `high_use_nobattery_none` | 479.2 -> **449.6** | 240.6 -> **208.8** | unprotected -> **unprotected** | 21,166 -> **20,012** | False -> **False** | - | 30 -> 30 | 98.1% | 2 |
| `high_use_battery_none` | 365 -> **338.8** | 162.2 -> **106.1** | unprotected -> **unprotected** | 15,309 -> **14,351** | False -> **False** | - | 26 -> 22 | 98.1% | 2 |

All **18 scenarios** (household x battery x export mode) reduce both total and evening grid units. Full numbers: `results/summary.csv`.

## The default scenario at different compliance rates

How much the family actually acts on. The battery plans itself either way.

| Suggestions followed | Grid units | Evening units | Est. bill (Rs) | Pricing band | 6-month figure (Rs) | Refusals |
|---|---|---|---|---|---|---|
| 30% | 215 -> **199.4** | 121.4 -> **105.6** | 8,867 -> **3,848** | **protected** | 20,505 | 0 |
| 70% | 215 -> **181.4** | 121.4 -> **86.9** | 8,867 -> **3,614** | **protected** | 18,788 | 2 |
| 100% | 215 -> **165.4** | 121.4 -> **71.2** | 8,867 -> **3,404** | **protected** | 17,261 | 2 |

**The result holds even at 30%.** The home stays under the limit and keeps protected pricing whether the family acts on 3 suggestions in 10 or all of them.

---

## The five points worth saying

### 1. A small home crosses a price cliff, and the agent keeps it under

- **Number:** 215 units becomes 181.4 units, which moves the home from **unprotected** to **protected** pricing
- **Source:** `results/summary.json -> scenarios.at_risk_nobattery_none`
- **Caveat:** The 215-unit starting point is an assumption, to be set from a real bill.

### 2. Crossing costs twice, and the second cost is the bigger one

- **Number:** Rs 5,253 this month, and about Rs 18,788 across the following 6 months
- **Source:** `results/summary.json -> scenarios.at_risk_nobattery_none.comparison`
- **Caveat:** The six-month figure prices those months at 181.4 units and assumes usage holds steady. An estimate, not a forecast.

### 3. The evening is where the grid feels it

- **Number:** Evening units (18:00-22:00) fall from 121.4 to 86.9, a drop of 34.5
- **Source:** `results/summary.json -> scenarios.at_risk_nobattery_none`
- **Caveat:** Evening units fall in all 18 scenarios; this is the one result that never breaks.

### 4. The agent says no, and says why

- **Number:** 2 refusals in the month, and 98.1% of its 52 promises kept, judged against what the sun actually did
- **Source:** `results/notifications_at_risk_nobattery_none.csv`
- **Caveat:** The one broken promise was made at 57% confidence: it was least sure about the one it got wrong.

### 5. Scheduling cannot close the gap on its own

- **Number:** The home still throws away 540 kWh of its own solar, using only 26.9% of the 738.3 kWh it generates
- **Source:** `results/summary.json (solar_wasted_kwh) and the app's hourly breakdown`
- **Caveat:** This is the honest limit of the household side, and the case for storage and for sharing surplus over the grid.

---

## Survey findings

**PLACEHOLDER - NO SURVEY RESULTS YET.**

`survey/survey_summary.md` does not exist, so there is nothing to quote. The helper is
built and tested but has not been run on real responses.

To fill this in:

```bash
python survey/survey_summary.py path/to/responses.csv
```

Then quote the three findings with their N from the generated file. Until then, **do not
state any survey number in the video.** If the survey is still open at recording time, say
only that it is running and how many people have answered so far, with no percentages.

The three findings most worth quoting, once they exist:

1. Share of solar homes that do **not** know whether they are registered for net metering.
2. Share of solar homes with a **battery**.
3. Share who would allow an app to act automatically **only if it explains each decision**.

---

## Numbers NOT to use in the video

- The per-message rupee amounts in the family view (Rs 88, Rs 59). They are a split of the monthly total, not independent savings, and quoting them alongside the monthly figure double-counts.
- The 1,000-home scale-up as a forecast. It is arithmetic on one simulated home.
- Any tariff rate as confirmed. They are reported figures, still to be verified against NEPRA.
- Any survey percentage, until `survey/survey_summary.md` exists.
