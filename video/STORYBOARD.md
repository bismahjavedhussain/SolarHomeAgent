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

## Source footage for 0:07-0:35 (Agentic Arbiter)

Your existing demo is on disk at `D:\FGHackathon\AGENTIC-ARBITER-demo.mp4` - 2:58.56, 2560x1440,
30 fps, 100 MB, with your original voiceover on the audio track.

Reference stills for the three shots to cut are in `video/arbiter_refs/`, named by the timestamp
they came from. Timings and the three fixes needed before reuse (burned-in subtitles, the audio
track, and the resolution mismatch) are in `SCRIPT.md`.
