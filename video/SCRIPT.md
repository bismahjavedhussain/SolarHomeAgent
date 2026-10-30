# Voiceover script — IRENA Youth Forum 2027

**The subtitles burned into `rough_cut_full.mp4` are exactly these lines.** Read them aloud as
they appear.

Total **1:59.43**, measured from the assembled cut.

---

### 0:00.00–0:07.00 (7.00s) — **Your card** · `c1_title`

> Energy gets wasted for a boring reason:
> nobody trusts the forecast enough to act on it.

### 0:07.00–0:11.50 (4.50s) — Agentic Arbiter (live app) · `a1_landing`

> In September 2026, I built Agentic Arbiter.
> It covers 238 real data-centre campuses across 36 US states.

### 0:11.50–0:16.00 (4.50s) — Agentic Arbiter (live app) · `a2_site`

> Data centres run chillers even when
> the air outside is already cold enough.

### 0:16.00–0:17.80 (1.80s) — Agentic Arbiter (live app) · `a3_config`

> _(no line - visual beat)_

### 0:17.80–0:21.30 (3.50s) — Agentic Arbiter (live app) · `a4_working`

> It works hour by hour, deciding when it's safe to shut the chillers off.

### 0:21.30–0:25.60 (4.30s) — Agentic Arbiter (live app) · `a5_schedule`

> It made no unsafe calls.
> The old controller made one.

### 0:25.60–0:29.60 (4.00s) — Agentic Arbiter (live app) · `a6_economic`

> Over five real years, that's about four hundred extra hours a year.

### 0:29.60–0:36.10 (6.50s) — Agentic Arbiter (live app) · `a7_selfscore`

> And it grades itself.
> Here it's missing its target, because the data was patchy during the hackathon window.
> It says so itself.

### 0:36.10–0:44.10 (8.00s) — **Your card** · `c2_coalition`

> Second of 842 teams, out of nearly four thousand people,
> at FortyGuard's hackathon, sponsored by NVIDIA.
> The UN-backed Cool Coalition featured it.

### 0:44.10–0:48.10 (4.00s) — Agentic Arbiter (live app) · `a8_future`

> Next I want it running live on real sites, not just measured on them.

### 0:48.10–0:55.60 (7.50s) — **Your card** · `c3_pakistan`

> Then I looked at home.
> Pakistan has solar on millions of roofs, but the grid can't see it.
> Go over two hundred units a month, and every unit gets re-priced.

### 0:55.60–1:01.60 (6.00s) — **Survey visual** · `s1_demand`

> I asked twenty-one families.
> Seven of the ten with solar have changed habits or are getting a battery.

### 1:01.60–1:08.80 (7.20s) — Solar Home Agent · `h1_metrics`

> So I'm building a Solar Home Agent.
> It helps most in a solar home with no battery that can't sell its spare power.

### 1:08.80–1:14.80 (6.00s) — Solar Home Agent · `h2_month`

> It reads tomorrow's weather, picks when to run the motor and the iron, and remembers how wrong it's been.

### 1:14.80–1:21.80 (7.00s) — Solar Home Agent · `h3_savings`

> Moving a few jobs into the sunny hours keeps this home under the limit.
> About five thousand rupees this month.

### 1:21.80–1:26.30 (4.50s) — Solar Home Agent · `h4_grid`

> Nearly nineteen thousand over the next six.
> It's a simulation, on one real month of Islamabad weather.

### 1:26.30–1:31.30 (5.00s) — **Survey visual** · `s2_trust`

> Thirteen said they'd only trust an app that explains itself.
> So mine does.

### 1:31.30–1:36.00 (4.70s) — Solar Home Agent · `h5_day`

> When it isn't sure, it says no,
> and tells you why.

### 1:36.00–1:39.00 (3.00s) — Solar Home Agent · `h6_promises`

> It keeps score against what the sun actually did.

### 1:39.00–1:43.00 (4.00s) — Solar Home Agent · `h7_switches`

> But look what it can't fix: it still wastes most of its midday sun,
> and buys after dark.

### 1:43.00–1:45.50 (2.50s) — Solar Home Agent · `h8_assume`

> Storage closes that.

### 1:45.50–1:53.50 (8.00s) — **Your card** · `c4_next`

> Next: five to ten homes in Islamabad, over WhatsApp.
> Then add them into one neighbourhood forecast, with our distribution company.

### 1:53.50–1:59.50 (6.00s) — **Your card** · `c5_close`

> The solar is already on Pakistan's roofs.
> I want to help the grid see it, and trust it.

---

## Claims table

Lines changed in this revision are marked **(revised)**.

| Said | Verified against |
|---|---|
| "In September 2026, I built Agentic Arbiter" | your correction |
| "238 real data-centre campuses across 36 US states" | Cool Coalition article, on screen at 0:37 |
| "no unsafe calls, the old controller made one" | the app's panel: unsafe declarations 0 vs 1 |
| "Over five real years, that's about four hundred extra hours a year" | **kept**: the Economic Impact panel says "five real years" in its subtitle, heading and section title, and the highlighted card reads "CHILLER-HOURS AVOIDED +406 h/yr" |
| "missing its target, because the data was patchy during the hackathon window" | your correction; panel shows 65.6% against a 90% promise |
| **(revised)** "out of nearly four thousand people" | the article's "nearly 4,000 participants", on screen |
| **(revised)** "The UN-backed Cool Coalition featured it" | the article masthead: "a UNEP-convened initiative" |
| "FortyGuard's hackathon, sponsored by NVIDIA" | your correction |
| "two hundred units" | 200-unit protected limit, 2026 tariff as reported |
| "I asked twenty-one families" | `survey/survey_summary.md`, N = 21 |
| **(revised)** "Seven of the ten with solar have changed habits or are getting a battery" | `survey/survey_summary.md`: 4 use more sun by day + 3 bought or plan a battery = 7 of 10 |
| **(revised)** "It helps most in a solar home with no battery that can't sell its spare power" | README "Who this is for"; the stand-down rule and `results/survey_scenario.json` |
| **(revised)** "picks when to run the motor and the iron, and remembers how wrong it's been" | the agent's learned margin: p80 of its own past error per hour, `src/agent.py` |
| **(revised)** "Moving a few jobs into the sunny hours keeps this home under the limit" | `results/summary.json`: 215.0 -> 181.4 units, unprotected -> protected |
| "About five thousand rupees this month" | Rs 5,253, `results/VIDEO_FACTS.md` |
| "Nearly nineteen thousand over the next six" | Rs 18,788 over six months, `results/VIDEO_FACTS.md` |
| "Thirteen said they'd only trust an app that explains itself" | `survey/survey_summary.md`: 13 of 21 |

## Survey caveat, if asked

21 households from my own student network, mostly better-off, 12 of the 21 in Islamabad or
Rawalpindi. Next I want to survey beyond my network, including renters and families with no
solar at all.
