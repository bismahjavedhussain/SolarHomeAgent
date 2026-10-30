# Storyboard

**`video/rough_cut_full.mp4` — 1:57.80, 1920x1080, 30 fps, silent, subtitles burned in.**

| # | Start | End | Length | Segment | Source |
|---|---|---|---|---|---|
| 1 | 0:00.00 | 0:07.00 | 7.00s | `c1_title` | **Your card** |
| 2 | 0:07.00 | 0:12.00 | 5.00s | `a1_landing` | Agentic Arbiter (live app) |
| 3 | 0:12.00 | 0:16.50 | 4.50s | `a2_site` | Agentic Arbiter (live app) |
| 4 | 0:16.50 | 0:19.50 | 3.00s | `a3_config` | Agentic Arbiter (live app) |
| 5 | 0:19.50 | 0:23.00 | 3.50s | `a4_working` | Agentic Arbiter (live app) |
| 6 | 0:23.00 | 0:28.50 | 5.50s | `a5_schedule` | Agentic Arbiter (live app) |
| 7 | 0:28.50 | 0:32.50 | 4.00s | `a6_economic` | Agentic Arbiter (live app) |
| 8 | 0:32.50 | 0:39.00 | 6.50s | `a7_selfscore` | Agentic Arbiter (live app) |
| 9 | 0:39.00 | 0:47.00 | 8.00s | `c2_coalition` | **Your card** |
| 10 | 0:47.00 | 0:51.00 | 4.00s | `a8_future` | Agentic Arbiter (live app) |
| 11 | 0:51.00 | 0:58.50 | 7.50s | `c3_pakistan` | **Your card** |
| 12 | 0:58.50 | 1:03.50 | 5.00s | `s1_demand` | **Survey visual** |
| 13 | 1:03.50 | 1:09.50 | 6.00s | `h1_metrics` | Solar Home Agent |
| 14 | 1:09.50 | 1:13.50 | 4.00s | `h2_month` | Solar Home Agent |
| 15 | 1:13.50 | 1:18.00 | 4.50s | `h3_savings` | Solar Home Agent |
| 16 | 1:18.00 | 1:22.50 | 4.50s | `h4_grid` | Solar Home Agent |
| 17 | 1:22.50 | 1:27.50 | 5.00s | `s2_trust` | **Survey visual** |
| 18 | 1:27.50 | 1:33.00 | 5.50s | `h5_day` | Solar Home Agent |
| 19 | 1:33.00 | 1:36.00 | 3.00s | `h6_promises` | Solar Home Agent |
| 20 | 1:36.00 | 1:40.00 | 4.00s | `h7_switches` | Solar Home Agent |
| 21 | 1:40.00 | 1:43.80 | 3.80s | `h8_assume` | Solar Home Agent |
| 22 | 1:43.80 | 1:51.80 | 8.00s | `c4_next` | **Your card** |
| 23 | 1:51.80 | 1:57.80 | 6.00s | `c5_close` | **Your card** |

## Your five cards — fixed slots

These keep the lengths you are building zoom clips to. Drop the MP4s in `assets/` and they
swap in without retiming anything.

| Card | Slot | Length | Zoom |
|---|---|---|---|
| Opening title | 0:00.00–0:07.00 | 7.0s | 100% → 106% |
| Cool Coalition | 0:39.00–0:47.00 | 8.0s | 100% → 108% |
| Pakistan's problem | 0:51.00–0:58.50 | 7.5s | 100% → 107% |
| What's next | 1:43.80–1:51.80 | 8.0s | 100% → 106% |
| Closing line | 1:51.80–1:57.80 | 6.0s | 106% → 100% |

**Note the slots moved** from the previous cut, because the two survey visuals were inserted.
The lengths are unchanged.

## Survey visuals

| Card | Slot | Length | File |
|---|---|---|---|
| Demand | 0:58.50–1:03.50 | 5.0s | `cards/survey_demand.png`, `clips/survey_demand.mp4` |
| Trust | 1:22.50–1:27.50 | 5.0s | `cards/survey_trust.png`, `clips/survey_trust.mp4` |

Both are drawn from the computed survey numbers, not typed. 5-second slow-zoom MP4s are in
`clips/` if you prefer them to the stills.
