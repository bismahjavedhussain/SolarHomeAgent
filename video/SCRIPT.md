# Voiceover script — IRENA Youth Forum 2027

**Bold** = stress it. **/** = breathe here. Word count and timing checked at the bottom.

> Read a little slower than feels natural. If you run long, cut the line marked *(cut first)*.

---

## 0:00–0:07 — The idea in one line

**[ON SCREEN]** Black card: *"Energy gets wasted when nobody trusts the forecast."*

> Energy gets wasted for a boring reason: / **nobody trusts the forecast enough to act on it**.

---

## 0:07–0:35 — Agentic Arbiter

**[ON SCREEN]** `video/clips_arbiter/` — the live app, recorded the same way as the solar demo.
Clip order in `STORYBOARD.md`.

> Last year I built **Agentic Arbiter**, solo. / Data centres run chillers when the air outside is
> already cold enough. / Mine decides, each hour, whether it's safe to shut them off.
>
> *[a5_schedule]* It made **no unsafe calls**. / The old controller made one.
>
> *[a7_selfscoring]* And it grades itself. / Here it's **missing its own target** / and saying so.
> / That's the part I'm proudest of.
>
> **Second of eight hundred and forty-two teams.** / The UN's Cool Coalition picked it up.

## 0:35–0:45 — Where that goes next

**[ON SCREEN]** The live app at `agentic-arbiter.onrender.com`, then a simple diagram.

> If cooling can wait for the right hour, / data centres become **flexible**, not fixed. / Same for
> cold storage in hot countries.

---

## 0:45–0:55 — Why Pakistan

**[ON SCREEN]** Rooftop solar, then the 200-unit cliff as plain text.

> Pakistan has solar on millions of roofs, / but **the grid can't see it**. / Go over **two hundred
> units** a month, / every unit gets re-priced.

---

## 0:55–1:35 — Solar Home Agent

**[ON SCREEN]** Your recording. Clip order in `STORYBOARD.md`.

> So I'm building a **Solar Home Agent**. / It reads tomorrow's weather, / then picks when to run
> the water motor and the iron.
>
> Same habit: / it remembers how wrong it's been. / When it isn't sure, / **it says no, and tells
> you why**.
>
> *[green box]* Moving a few jobs into the afternoon keeps this home **under the limit**. / About
> **five thousand rupees** this month, / nearly **nineteen thousand** over the next six.
>
> It's **a simulation**, / on one real month of Islamabad weather. **[SURVEY LINE]**
>
> *[grid box]* But look what it **can't** fix. / It still wastes most of its midday sun, / and buys
> after dark. / **Storage** closes that.

---

## 1:35–1:55 — What's next, and the close

**[ON SCREEN]** Islamabad map, COMSATS, IRENA NewGen, IESCO, then your name.

> Next: **five to ten homes in Islamabad**, over WhatsApp. / I'm starting an Energy-and-AI circle at
> COMSATS, / and I'd join IRENA NewGen. *(cut first)* / Then add those homes into one neighbourhood
> forecast, / with our distribution company.
>
> **The solar is already on Pakistan's roofs.** / I want to help the grid **see it** / and **trust
> it**.

---

## The survey line

`survey/survey_summary.md` **does not exist yet**, so there is no survey number to quote. Pick one:

- **Default, if the survey is still open when you record** (6 words):
  > "I'm surveying Pakistani homes to replace my guesses."

- **If you have results**, run `python survey/survey_summary.py <responses.csv>` first, then say the
  most striking finding **with its N** (keep it under 15 words):
  > "I asked around a hundred homes. / Most with solar **didn't know** if they were registered."

**Do not state a survey percentage that isn't in the generated file.** It is the one number here you
cannot check.

---

## Edit guide for 0:07–0:35

**You don't need the old hackathon video.** I recorded the live deployment at
`agentic-arbiter.onrender.com` the same way as the solar demo — real cursor, real clicks, nothing
staged — so this section is motion footage, not stills.

| Clip | Length | Shows |
|---|---|---|
| `a1_landing.mp4` | 13.6s | Landing page, then Initialize Arbiter clicked |
| `a2_pick_site.mp4` | 8.1s | The map of real campuses, picking one |
| `a3_configure.mp4` | 10.0s | What the agent may change: limit, humidity gate, switching rules |
| `a4_agent_running.mp4` | 9.2s | The agent working through its stages |
| `a5_schedule.mp4` | 6.7s | **The decision. Agent 12 h vs incumbent 13 h, unsafe declarations 0 vs 1, hours refused 0** |
| `a6_economic.mp4` | 6.8s | Five real years, measured |
| `a7_selfscoring.mp4` | 6.9s | **65.6% coverage against its own 90% promise. "Margin moved itself, after the miss, unprompted"** |

**The 28-second cut**, already assembled in `rough_cut_full.mp4`:

| Take | From | Why |
|---|---|---|
| 5.0s | `a1_landing` @1.0 | Establishes what it is, and that it is live |
| 6.0s | `a4_agent_running` @0.5 | The agent actually working |
| 4.0s | `a3_configure` @1.0 | What it is allowed to touch |
| 6.2s | `a5_schedule` @0.3 | **0 unsafe calls vs the old controller's 1** — the safety claim, on screen |
| 6.6s | `a7_selfscoring` @0.3 | **It misses its own 90% promise and says so.** Strongest shot in either project |

**Why the self-scoring shot leads the section.** It would be easy to show only the wins. That screen
shows the bound measuring **65.6%** against a **90%** promise it set itself, explains *why*
(4 calibration days where it needs about 10), and shows the margin widening on its own after the
miss. An agent that reports its own shortfall is the whole argument, in both projects.

**Note:** the app's live header reads *"LIVE agent is also attached"* in the recording, so the
footage shows the deployed app with the live path available, not a replay.

## Numbers in this script

Five spoken, all rounded and checkable:

| Said | Exact | Source |
|---|---|---|
| "about four hundred hours" | 406 chiller-hours/year | Agentic Arbiter test site |
| "second out of eight hundred and forty-two" | 2nd / 842 teams | FortyGuard Hackathon '26 |
| "two hundred units" | 200-unit protected limit | 2026 tariff, as reported |
| "about five thousand rupees" | Rs 5,253 this month | `results/VIDEO_FACTS.md` |
| "nearly nineteen thousand" | Rs 18,788 over six months | `results/VIDEO_FACTS.md` |

**Deliberately not spoken:** the per-message rupee figures in the family view (Rs 88, Rs 59). They
are a split of the monthly total, so saying them next to "five thousand rupees" counts the same
money twice.

---

## Verified length

**283 spoken words**, counted from the blockquote lines only (on-screen cues excluded).

| Pace | Runtime |
|---|---|
| 145 wpm (slow, clear) | **1:57** |
| 150 wpm (natural) | **1:53** |
| 155 wpm | **1:49** |

| Section | Words | At 150 wpm | Slot |
|---|---|---|---|
| 0:00-0:07 opening | 16 | 6.4s | 7s |
| 0:07-0:35 Agentic Arbiter | 71 | 28.4s | 28s |
| 0:35-0:45 where it goes next | 21 | 8.4s | 10s |
| 0:45-0:55 why Pakistan | 24 | 9.6s | 10s |
| 0:55-1:35 Solar Home Agent | 98 | 39.2s | 40s |
| 1:35-1:55 next steps and close | 51 | 20.4s | 20s |

Every section fits its slot. The demo section is the tightest; if you overrun there, the recording
has more footage than you need, so slow down and drop a clip rather than rushing the words.
