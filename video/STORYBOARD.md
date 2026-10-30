# Storyboard: Solar Home Agent screen recording

<!-- Generated from the recording run. Lengths are measured, not estimated. -->

**Full recording:** `video/demo_full.mp4` - **61.4 seconds**, 1920x1080, H.264, 25 fps, no audio.
**Per-step clips:** `video/clips/` (9 files). **Stills:** `video/stills/` (1920x1080 PNG per step).

A dark arrow cursor was injected into the page, because Playwright recordings do not capture the real pointer. Clicks show an expanding ring, and the element being discussed gets a thin blue box around it.

## Clips

| # | Clip | Length | In full video | What it shows |
|---|---|---|---|---|
| 1 | `01_metrics.mp4` | 9.2s | 4.9-14.1s | Opens on the at-risk home. Simulation banner, then grid units, evening units, bill. |
| 2 | `02_month_chart.mp4` | 6.4s | 13.7-20.1s | Cumulative units over the month, with the 200-unit line. |
| 3 | `03_savings_box.mp4` | 5.1s | 19.6-24.7s | Crossing the limit counts twice: this month, and the next six months. |
| 4 | `04_grid_insight.mp4` | 5.2s | 24.2-29.4s | Solar thrown away at midday against units bought after dark, plus the 1,000-home scale-up. |
| 5 | `05_family_view.mp4` | 5.2s | 28.9-34.1s | What the household actually sees, with a rupee figure per suggestion. |
| 6 | `06_day_detail.mp4` | 7.7s | 33.6-41.3s | A day the agent refused to move anything, at 16% confidence, then the day's load. |
| 7 | `07_promises.mp4` | 4.0s | 40.9-44.9s | The agent marking its own homework against what the sun actually did. |
| 8 | `08_sidebar_switches.mp4` | 13.6s | 44.5-58.0s | Results move with how often the family acts, and with the household. |
| 9 | `09_assumptions.mp4` | 3.9s | 57.5-61.4s | The assumptions and limits, opened on camera. |

Clips total **60.4s** (they overlap slightly by design: each carries a 0.35 s lead-in and tail so cuts do not clip the cursor mid-move).

## Fitting the 40-second demo slot

The voiceover gives the demo **0:55-1:35, so 40 seconds**. The full recording is longer than that, so pick from the clips rather than using the whole thing.

**Suggested 40-second cut:**

| Clip | Keep | Running total |
|---|---|---|
| `01_metrics.mp4` | 7.0s | 7.0s |
| `02_month_chart.mp4` | 5.0s | 12.0s |
| `03_savings_box.mp4` | 5.0s | 17.0s |
| `04_grid_insight.mp4` | 5.0s | 22.0s |
| `06_day_detail.mp4` | 7.0s | 29.0s |
| `07_promises.mp4` | 3.5s | 32.5s |
| `08_sidebar_switches.mp4` | 5.5s | 38.0s |
| `09_assumptions.mp4` | 2.0s | 40.0s |

That lands at **40 seconds**. `05_family_view` is the one to drop first: it is the nicest to look at but the rupee figures on those cards are a split of the monthly total, so talking over them risks double-counting the saving.

**If you need to lose more:** trim the second half of `08_sidebar_switches` (the household switch) and keep only the compliance slider moving, which is the more surprising moment.

## Notes for editing

- Clips have **no audio**. Record the voiceover separately and lay it under them.
- `08_sidebar_switches` has dead time while the app recomputes after each change. Speeding that clip to 1.5x looks natural and buys back about 4 seconds.
- The stills in `video/stills/` are full-resolution frames, useful for the application form or for holding a frame while you talk.
- Nothing in the recording is sped up or cut mid-step; what you see is the app running at normal speed from the cached data, with no network access.

---

## Agentic Arbiter, recorded live (0:07-0:35)

Recorded from the deployment at `agentic-arbiter.onrender.com` with the same injected cursor,
click rings and highlight boxes as the solar demo. **The old hackathon video is not used.**

**Full recording:** `video/arbiter_full.mp4` - **73.4 seconds**, 1920x1080, 30 fps, no audio.

| Clip | Length | What it shows |
|---|---|---|
| `clips_arbiter/a1_landing.mp4` | 13.6s | Landing page: free-cooling decisions, hour by hour. Clicks Initialize. |
| `clips_arbiter/a2_pick_site.mp4` | 8.1s | Picks one real data-centre campus from the map of 238. |
| `clips_arbiter/a3_configure.mp4` | 10.0s | Configuration: the temperature limit, humidity gate and switching rules. |
| `clips_arbiter/a4_agent_running.mp4` | 9.2s | The agent working through its stages on real data. |
| `clips_arbiter/a5_schedule.mp4` | 6.7s | The decision: a schedule, not a thermostat. Hours refused shown. |
| `clips_arbiter/a6_economic.mp4` | 6.8s | Five real years: chiller-hours recovered and mechanical cooling cut. |
| `clips_arbiter/a7_selfscoring.mp4` | 6.9s | The self-scoring loop, including where the bound misses its 90% promise. |

The app header reads *"LIVE agent is also attached"* throughout, so this is the deployed
app with its live path available, not a replay.

---

## The assembled rough cut

`video/rough_cut_full.mp4` - **1:54.8**, 1920x1080, 30 fps, **silent**. Both projects cut
together in script order, with captions burned in and labelled placeholder cards where you
still need to supply footage.

| # | Segment | Length | Shows |
|---|---|---|---|
| 1 | `00_title` | 7.0s | Opening title card |
| 2 | `01_arb_landing` | 5.0s | Landing page: free-cooling decisions, hour by hour |
| 3 | `02_arb_working` | 6.0s | The agent, working |
| 4 | `03_arb_configure` | 4.0s | Configuration: what the agent may change |
| 5 | `04_arb_schedule` | 6.2s | The decision: a schedule, hours refused, unsafe declarations 0 vs 1 |
| 6 | `05_arb_selfscore` | 6.6s | Self-scoring: the bound missing its own promise, margin moved unprompted |
| 7 | `06_arb_economic` | 6.4s | Economic impact over five real years |
| 8 | `07_arb_map` | 3.6s | The map of real campuses, standing in for the flexible-load idea |
| 9 | `07b_pakistan` | 10.0s | PLACEHOLDER: Pakistan rooftops and the tariff cliff |
| 10 | `08_sha_0_01_metrics` | 7.0s | Opens on the at-risk home: grid units, evening units, bill |
| 11 | `08_sha_1_02_month_chart` | 5.0s | Cumulative units with the 200-unit line |
| 12 | `08_sha_2_03_savings_box` | 5.0s | This month, and the next six months |
| 13 | `08_sha_3_04_grid_insight` | 5.0s | Midday waste vs buying after dark, and the scale-up |
| 14 | `08_sha_4_06_day_detail` | 7.0s | The day it refused, at 16% confidence |
| 15 | `08_sha_5_07_promises` | 3.5s | Promises kept: 98.1% |
| 16 | `08_sha_6_08_sidebar_switches` | 5.5s | Results move with how often the family acts |
| 17 | `08_sha_7_09_assumptions` | 2.0s | Assumptions and limits, opened on camera |
| 18 | `09_next_steps` | 14.0s | PLACEHOLDER: next steps visuals |
| 19 | `10_close` | 6.0s | Closing card |

Runs to **114.8s**.

**Two placeholder cards need your footage:**

- **0:45-0:55** rooftop solar photos and the 200-unit cliff
- **1:35-1:49** Islamabad map, COMSATS, IRENA NewGen, IESCO

Everything else is real recorded footage. Lay the voiceover from `SCRIPT.md` underneath and
replace the two cards.
