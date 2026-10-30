# Voiceover script — IRENA Youth Forum 2027

**Bold** = stress it. **/** = breathe here. Word count and timing checked at the bottom.

> Read a little slower than feels natural. If you run long, cut the line marked *(cut first)*.

---

## 0:00–0:07 — The idea in one line

**[ON SCREEN]** Black card: *"Energy gets wasted when nobody trusts the forecast."*

> Energy gets wasted for a boring reason: / **nobody trusts the forecast enough to act on it**.

---

## 0:07–0:35 — Agentic Arbiter

**[ON SCREEN]** Clips from the FortyGuard demo — see the edit guide.

> Last year I built **Agentic Arbiter**, solo. / Data centres run chillers when the air outside is
> already cold enough. / Mine decides, each hour, whether it's safe to shut them off.
>
> And **it checks its own accuracy first**. / If it can't show it's safe, / it **refuses**. / That
> found about **four hundred** extra hours a year.
>
> **Second of eight hundred and forty-two teams**, / and the UN's Cool Coalition picked it up.

---

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

I couldn't watch your FortyGuard video — YouTube returned only the title to me, no description or
chapters — so this is by **kind of moment**, not timestamps. Three beats, about nine seconds each:

1. **The problem (0:07–0:16).** The shot showing chillers running while outside air is already cold.
   Overlay: **"238 data-centre campuses · 36 US states."**
2. **The agent deciding (0:16–0:27).** The hour-by-hour decision view — ideally the moment it says
   *no*, because the voiceover lands on "it refuses" right here. The deployed app at
   `agentic-arbiter.onrender.com` will screen-record cleaner than old footage; grab it fresh if you
   can. Overlay: **"Checks its own accuracy. Refuses when it can't prove it's safe."**
3. **The result (0:27–0:35).** The results chart. Overlay: **"+406 chiller-hours a year · 913
   held-out days"**, then **"2nd of 842 teams · FortyGuard '26"**.

Keep the unspoken numbers (238 campuses, 913 days, 10.7%) **on screen only**. The script is at its
five-number budget, and reading them aloud turns it into a press release.

---

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

**279 spoken words**, counted from the blockquote lines only (on-screen cues excluded).

| Pace | Runtime |
|---|---|
| 145 wpm (slow, clear) | **1:55** |
| 150 wpm (natural) | **1:51** |
| 155 wpm | **1:48** |

| Section | Words | At 150 wpm | Slot |
|---|---|---|---|
| 0:00-0:07 opening | 16 | 6.4s | 7s |
| 0:07-0:35 Agentic Arbiter | 69 | 27.6s | 28s |
| 0:35-0:45 where it goes next | 21 | 8.4s | 10s |
| 0:45-0:55 why Pakistan | 24 | 9.6s | 10s |
| 0:55-1:35 Solar Home Agent | 98 | 39.2s | 40s |
| 1:35-1:55 next steps and close | 51 | 20.4s | 20s |

Every section fits its slot. The demo section is the tightest; if you overrun there, the recording
has more footage than you need, so slow down and drop a clip rather than rushing the words.
