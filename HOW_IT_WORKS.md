# How it works

A plain-language guide to the energy ideas in this project and to how the agent decides.
No energy background assumed. Read this before the code.

---

## Part 1: The energy ideas

### A "unit" is a kilowatt-hour

Your bill counts **units**. One unit = one kilowatt-hour (kWh) = running a 1000-watt appliance
for one hour. A 1.5 kW air conditioner running for one hour uses 1.5 units.

Two words that are easy to mix up:

- **kW (power)** is how fast energy flows *right now* - like the width of a tap.
- **kWh (energy)** is how much flowed *in total* - like the water in the bucket.

Because this simulation steps forward one hour at a time, a flow of 2 kW for that hour delivers
exactly 2 kWh. That is why the code often treats the two numbers as interchangeable.

### Solar panels follow the sun, not your family

Panel output depends on **irradiance** - how much sunlight lands on a square metre, measured in
watts per square metre (W/m2). At noon in Islamabad in June it reaches about 900 W/m2; at night
it is zero.

The model is deliberately simple:

```
panel output (kW) = system size (kW) x irradiance / 1000 x 0.80
```

The `0.80` is a **derate**: panels lose roughly a fifth of their rated output to heat, dust and
wiring. Panels get *less* efficient as they get hotter, which is a quiet irony of solar in a hot
country.

### The mismatch, which is the whole problem

Look at `results/data_check.png`. Two things peak at different times:

- **Sunlight** peaks around 11:00-12:00.
- **Temperature** peaks around 14:00-15:00 and stays high into the night.

Your air conditioner follows the *temperature*, not the sunlight. So the panels are flat out at
noon when the house is relatively comfortable, and asleep at 21:00 when the house is hottest and
the AC is working hardest. That gap is the problem this project exists to narrow.

### Why extra noon solar is simply thrown away

When panels make more than the house is using, that surplus has to go somewhere:

1. **Charge a battery** - if there is one, and if it isn't already full.
2. **Go out to the grid** - only if the home is *registered*. Most Pakistani solar homes are not.
3. **Vanish.** The inverter detects there is nowhere for the power to go and simply backs off.
   The sunlight still falls on the panels; they just decline to convert it.

Option 3 is what `export_mode: none` models, and it is the common case. In the main scenario the
home throws away **433.5 kWh in a month** - far more than the 63.6 units it buys. It is not
losing money on that power; it just never gets it.

### Net metering vs net billing

- **Net metering** (older, being withdrawn for new users): a unit you send out cancels a unit you
  later bring in, one for one. Generous, because you effectively "bank" power at retail value.
- **Net billing** (2026 rules, for new users): you are *paid* for what you send out, at a much
  lower rate than you pay to buy - reportedly around Rs 11 per unit, which is **contested**.

Either way, the lesson is the same: **using your own solar in your own house beats selling it.**
That is why the agent tries to move demand into sunny hours rather than optimising exports.

### The 200-unit cliff

This is the part worth understanding properly, because it is unusual.

- Stay at or under **200 units a month** (for six months running) and you get **protected**
  rates: Rs 10.54 for the first 100 units, Rs 13.01 for the next 100.
- Go over 200 even once and you become **unprotected** for the next six months.

Unprotected pricing is **non-telescopic**, and that word does the damage. Telescopic means each
slice of units is billed at its own rate. Non-telescopic means **the band you land in sets the
price for every single unit you used.**

From this project's own tariff module:

| Units used | Bill |
|---|---|
| 199 | Rs 2,342 |
| 201 | Rs 5,932 |

Two extra units, and the bill more than doubles - not because those two units are expensive, but
because all 201 are suddenly re-priced. This is why the agent watches that threshold and warns
the family *before* they cross it, rather than reporting it afterwards.

### The evening peak, and why the grid cares

Across a whole city, solar homes behave alike: self-sufficient at noon, then all reaching for the
grid at once after sunset. Demand seen by the grid therefore sags in the middle of the day and
spikes sharply in the evening - the shape people call a **duck curve**.

That spike is expensive and dirty, because it has to be met by fast-reacting plants. Pakistan's
regulator cited exactly this when it made batteries mandatory for new solar and wind projects in
September 2026. So **evening units are the number that matters to the grid**, which is why this
project reports them separately everywhere. In all 12 scenarios the agent reduces them.

### Why "unmet load" has to be reported too

During a power cut the grid gives you nothing. If the battery is empty, the house simply goes
dark. That electricity was never delivered - so it never appears on the bill.

This creates a trap when comparing two strategies. A home that fails its family looks
**cheaper**. In the `high_use` home with a battery, the agent buys 4.2 units *more* than usual
behaviour - but it serves **46.2 kWh more of the family's actual demand** and cuts time without
power from 28 hours to 21.

So this project always reports **units bought**, **unmet load**, and **units per 100 kWh actually
served** together. Any one of them alone can mislead.

---

## Part 2: How the agent decides

The agent is plain rules - no machine learning. Every decision can be read off in one line.
It lives in `src/agent.py`.

### Step 1: Predict (`predicted_solar`, `predicted_fixed_load`)

Each evening at 20:00 it reads tomorrow's forecast and works out, hour by hour, how much solar it
expects and how much the house will use no matter what (fridge, fans, lights, AC).

### Step 2: Doubt itself (`margin`) - the important part

A forecast is not a fact. So the agent keeps a diary of how wrong it has been, **at each hour of
the day separately**, and holds back a margin:

```
margin[h] = 80th percentile of past absolute errors at hour h
```

Why the 80th percentile and not the average? Because the agent wants to be right most of the
time, not on average. Planning against the average means being disappointed half the time.

For the first 5 days it has no diary yet, so it falls back to cloud cover
(`predicted solar x cloud fraction`) and **labels every message `cloud-cover`** so nobody mistakes
a guess for experience. From day 6 the label becomes `learned`.

In this data the day-ahead forecast is **too optimistic about sun at every daylight hour**
(mean error +52.7 W/m2), so this habit of doubt is doing real work rather than decorating the code.

### Step 3: Work out what is safely spare (`conservative_surplus`)

```
confident surplus[h] = predicted solar[h] - margin[h] - unavoidable load[h]
```

Only this - not the raw forecast - is allowed to be spent. It is deliberately pessimistic.

### Step 4: Move appliances into the sun (`place_appliance`)

For each appliance, it checks every hour in that appliance's allowed window and picks the one
with the most confident surplus, as long as the surplus covers the appliance's power. The family
gets a message:

> 11:00 - Run the water motor at 11:00 instead of 19:00. Your panels should cover it then
> (confidence 90%).

### Step 5: Refuse when unsure

**If no hour in the window has enough confident surplus, the agent does not move the appliance.**
It keeps the usual time and says why:

> 19:00 - Keeping the water motor at its usual 19:00. Not enough sun expected tomorrow to be
> confident about moving it (confidence 16%).

This is the behaviour most demos leave out. An agent that always acts looks impressive and is
untrustworthy: on a cloudy day, moving the motor to noon means running it off the **grid** at
noon *and* having no stored solar for the evening - worse than doing nothing. In the main
scenario it refuses twice in the month.

### Step 6: Pre-cool on hot days (`_plan_precooling`)

If tomorrow evening is forecast to reach 35 C and there is confident surplus going spare in the
afternoon, it cools the house early while the sun is paying for it, so the AC works less later.
The energy trade (1.0 kWh now for 0.6 kWh saved) is **a rough guess** and is labelled as such in
the message itself.

### Step 7: Plan the battery (`_plan_reserve`)

The battery should be full by sunset and should cover the evening and the power cut. So during
the day the agent sets a **floor** it will not discharge below, sized from the expected evening
shortfall plus whatever the 20:00 cut will need - and raised when confidence is low.

**A bug worth knowing about, because it is instructive.** The first version held that floor
around the clock. The result: the agent bought *more* grid power than doing nothing (114.6 units
versus 85.4), because the battery loyally protected a reserve straight through the evening it was
supposed to be saving for. A reserve you never spend is just an expensive empty room. The fix is
that the floor applies **during the day only**, and from 18:00 it drops to just the power-cut
need.

### Step 8: Guard the 200-unit threshold (`_guard_active`)

For a protected-eligible home it tracks units used so far and projects the month's total. If the
projection crosses 200 it enters guard mode: shifting more aggressively and accepting hours it
would normally reject, and telling the family plainly:

> 54 units used with 22 days left. Moving more jobs into the sun to try to stay under 200 units.

**In the main scenario this never fires**, because the agent keeps the home at 63.6 units - a long
way below 200. That is reported as it is. The mechanism is verified by tests using a heavier home,
where it fires on 22 of 30 days.

### Step 9: Check its own work (`learn_from_day`)

At the end of each day it compares what it predicted with what actually happened, and files the
error. Tomorrow's margin is built from today's mistake. This is the loop that makes the
confidence figure mean something.

---

## Part 3: Reading the code

Start here and follow the order:

| File | What it does |
|---|---|
| `src/fetch_weather.py` | Downloads and caches the weather; handles the one-hour radiation shift |
| `src/solar.py` | Sunlight to panel output. Three lines. |
| `src/home.py` | Base load, temperature-driven AC, and the appliance definitions |
| `src/battery.py` | Capacity, power limits, efficiency, minimum charge level |
| `src/tariff.py` | Protected and unprotected bands, and the 200-unit cliff |
| `src/baseline.py` | "Usual" behaviour: appliances at habitual times, no forecast |
| `src/agent.py` | Everything in Part 2 above |
| `src/simulate.py` | `dispatch_hour` resolves each hour; `run_month` walks the month |
| `src/metrics.py` | Turns a month of hours into the summary numbers |
| `src/plots.py` | The three charts |

### The one function to read first

`dispatch_hour` in `src/simulate.py` is the heart of the physics. Every hour, in this order:

1. Solar serves the house first - always the cheapest electricity available.
2. Any surplus charges the battery, if it has room.
3. Anything still left over is exported, or wasted if the home cannot sell.
4. Any load solar did not cover comes from the battery, down to its floor.
5. Whatever remains comes from the grid - unless the grid is down, in which case it is
   **unmet load**.

### Energy cannot be invented

Two equations are checked for **every hour of every scenario**, in `tests/test_energy_balance.py`:

```
solar to load + battery out + grid in + unmet        = load
solar generated = solar to load + battery in + exported + wasted
```

They currently hold to about 4 x 10^-16 kWh - floating-point dust. If a future change ever
invents or loses energy, those tests fail immediately. This matters more than it sounds: a
simulation that quietly leaks energy can produce any result you like.

---

## Part 4: Honest limits

- It is a **simulation**, not a measurement. Nothing here is evidence of real savings.
- One month, one city, one weather year, one set of appliances.
- The pre-cooling figures are a guess; six of the eight unprotected tariff rates are placeholders;
  taxes are excluded, so every bill shown is lower than a real one.
- The model assumes a hybrid inverter that keeps working during a power cut. Many real systems
  shut down completely.
- Nobody ignores a notification, forgets, or is out of the house. Real families will.
- No tilt model, no shading, no battery ageing.

Full detail in `ASSUMPTIONS.md`.
