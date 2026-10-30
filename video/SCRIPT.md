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

I watched your demo by pulling frames out of `D:\FGHackathon\AGENTIC-ARBITER-demo.mp4`
(2:58.56, 2560x1440, 30 fps, 100 MB). Reference stills for each shot below are in
`video/arbiter_refs/`.

### What's in your existing video

| Time | Screen |
|---|---|
| 0:00–0:28 | Landing page, rotating globe, title and tagline |
| 0:28–0:34 | "Initialize Arbiter" click |
| 0:34–1:00 | Main dashboard: 238 campuses, $42.4M–$84.8M, +92,988 free-cooling hours, the five-stage loop, site cards |
| 1:00–1:06 | US map with site pins, Ashburn callout |
| 1:06–1:16 | Configuration & Setup |
| **1:16–1:34** | **Hourly Schedule & Reasoning** — hourly bound chart, agent 12 h vs incumbent 13 h, **unsafe declarations 0 vs 1**, **hours refused**, "the agent's own reasoning, checkable" |
| 1:34–1:50 | Configuration & Setup again |
| **1:50–2:06** | **Economic Impact** — 5,375 h/yr, **+406 h/yr**, **10.7%**, 94.1%, 65.6%, tariff sweep |
| 2:06–2:20 | Plume & Geometry — wind rose, **bearings refused 0 of 72** |
| **2:20–2:40** | **Self-Scoring** — "grades its own promise against what actually happened, **and widens its margin when it was wrong**", margin moved −0.739 → 0.191 °C |
| 2:40–2:58 | Back to dashboard and map, closing |

### The three beats to cut

| New video | Take from | Why |
|---|---|---|
| **0:07–0:16** the problem | **0:00–0:10** | The globe, and the burned-in line *"Data centres run chillers when the air outside is already cold enough"* is almost word for word what the new voiceover says here. Overlay: **"238 data-centre campuses · 36 US states."** |
| **0:16–0:27** it checks itself, and refuses | **2:22–2:32** (first choice) or **1:18–1:28** | Self-Scoring literally reads *"widens its margin when it was wrong"* — that is the line "it checks its own accuracy first" landing on screen. The Hourly Schedule shot is the alternative, since it shows **hours refused** and **unsafe declarations 0 vs 1** side by side. Overlay: **"Refuses when it can't prove it's safe."** |
| **0:27–0:35** the result | **1:52–2:00**, then **0:38–0:44** | Economic Impact has **+406 h/yr** and **10.7%** on one screen, which is the number you say aloud. Cut to the dashboard's **+92,988 hours** for the last two seconds to show scale. Overlay: **"2nd of 842 teams · FortyGuard '26."** |

### Three things to fix before you reuse any of it

1. **The subtitles are burned into the picture**, in the bottom ~8% of frame, and they are the *old*
   narration. Over a new voiceover they will contradict you. Crop the bottom 10% of the frame
   (2560x1440 → 2560x1300, then scale to 1920x1080), or pick only the shots above where the old
   line happens to match the new one.
2. **Mute it.** The file carries your original voice track. Export video-only, or set its volume to
   zero in the timeline.
3. **Resolution differs.** The Arbiter video is 2560x1440; the Solar Home Agent recording is
   1920x1080. Set the project to 1080p and scale the Arbiter clips down, or the cut will jump in
   sharpness halfway through.

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
