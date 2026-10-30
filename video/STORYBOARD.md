# Storyboard

**`video/rough_cut_full.mp4` — 1:55, 1920x1080, 30 fps, silent, subtitles burned in.**

Both live apps recorded with an injected cursor, click rings and highlight boxes. The old
hackathon video is not used. Subtitles are the spoken script, so you can read them aloud.

| # | Segment | Start | Length | Source |
|---|---|---|---|---|
| 1 | `t00` | 0:00 | 7.0s | Title card |
| 2 | `t01_landing` | 0:07 | 5.5s | Agentic Arbiter (live app) |
| 3 | `t02_site` | 0:12 | 5.0s | Agentic Arbiter (live app) |
| 4 | `t03_config` | 0:17 | 4.5s | Agentic Arbiter (live app) |
| 5 | `t04_working` | 0:22 | 4.0s | Agentic Arbiter (live app) |
| 6 | `t05_schedule` | 0:26 | 6.0s | Agentic Arbiter (live app) |
| 7 | `t06_economic` | 0:32 | 4.5s | Agentic Arbiter (live app) |
| 8 | `t07_selfscore` | 0:36 | 7.0s | Agentic Arbiter (live app) |
| 9 | `t08_coalition` | 0:43 | 8.0s | **Cool Coalition article screenshot** |
| 10 | `t09_future` | 0:51 | 4.5s | Agentic Arbiter (live app) |
| 11 | `t10_pakistan` | 0:56 | 7.5s | **[ YOUR FOOTAGE HERE ]** |
| 12 | `t11_sha_metrics` | 1:03 | 6.5s | Solar Home Agent |
| 13 | `t12_sha_month` | 1:10 | 4.5s | Solar Home Agent |
| 14 | `t13_sha_savings` | 1:14 | 5.0s | Solar Home Agent |
| 15 | `t14_sha_grid` | 1:19 | 5.0s | Solar Home Agent |
| 16 | `t15_sha_day` | 1:24 | 6.0s | Solar Home Agent |
| 17 | `t16_sha_promises` | 1:30 | 3.5s | Solar Home Agent |
| 18 | `t17_sha_switches` | 1:34 | 3.5s | Solar Home Agent |
| 19 | `t18_sha_assume` | 1:37 | 3.5s | Solar Home Agent |
| 20 | `t19_next` | 1:41 | 8.0s | **[ YOUR FOOTAGE HERE ]** |
| 21 | `t20_close` | 1:49 | 6.0s | Title card |

## Structure

- **0:00–0:07** opening card
- **0:07–0:43** Agentic Arbiter, in product order: landing, pick a site, configure, run, decision, worth, self-score
- **0:43–0:51** the Cool Coalition article, for the recognition
- **0:51–0:56** the future goal, over the map of sites
- **0:56–1:03** bridge to Pakistan **(your footage)**
- **1:03–1:43** Solar Home Agent
- **1:43–1:51** next steps **(your footage)**
- **1:51–1:55** closing card

## Source files

| File | Length | What |
|---|---|---|
| `arbiter_full.mp4` | 70.0s | The live Arbiter app, 7 beats |
| `demo_full.mp4` | 61.4s | The Solar Home Agent app, 9 beats |
| `clips_arbiter/*.mp4` | 7 | Per-beat Arbiter cuts |
| `clips/*.mp4` | 9 | Per-beat Solar cuts |
| `assets/cool_coalition.png` | - | The article screenshot |
| `script_subtitles.srt` / `.ass` | 38 cues | Subtitles, plain and styled |

## Notes

- Clips are **silent**. Record the voiceover separately.
- Subtitle size is set in the `.ass` as literal pixels because `PlayResY: 1080` is declared.
  Without that line libass assumes 288 and scales the font up about 3.75x.
