"""Streamlit demo: flip the switches and compare usual behaviour with the agent."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.fetch_weather import load_config, load_weather
from src.metrics import summarise
from src.simulate import base_scenario, run_month

st.set_page_config(page_title="Solar Home Agent (Pakistan)", page_icon="sun", layout="wide")


@st.cache_data(show_spinner=False)
def _config() -> dict:
    """Load the scenario config once."""
    return load_config()


@st.cache_data(show_spinner=False)
def _weather(month: str) -> tuple:
    """Load the cached weather once; no API calls."""
    return load_weather(_config())


@st.cache_data(show_spinner="Simulating the month...")
def _simulate(household: str, has_battery: bool, export_mode: str, solar_kw: float,
              power_cuts: bool) -> dict:
    """Run both modes for one scenario and return frames, metrics and messages."""
    config = _config()
    scenario = base_scenario(config, household=household, has_battery=has_battery,
                             export_mode=export_mode, solar_kw=solar_kw, power_cuts=power_cuts)
    weather = _weather(str(config["month"]))
    out = {}
    for mode in ("usual", "agent"):
        run = run_month(config, scenario, mode, weather)
        out[mode] = {
            "hourly": run["hourly"],
            "metrics": summarise(run, config, scenario),
            "notifications": run["notifications"],
        }
    return out


config = _config()

st.title("Solar Home Agent - Pakistan (prototype v0)")
st.warning(
    "**This is a simulation, not a real home.** It runs one real month of Islamabad weather "
    "(June 2025) against modelled appliances. Several inputs are rough estimates and some tariff "
    "rates are placeholders. No claim is made about real-world savings. See ASSUMPTIONS.md.",
    icon=":material/warning:",
)

with st.sidebar:
    st.header("Scenario")
    household = st.radio(
        "Household", ["low_use", "high_use"],
        format_func=lambda v: "Low use (1 AC, protected-eligible)" if v == "low_use" else "High use (2 ACs)",
        help="Low use is calibrated to a configurable monthly target; see ASSUMPTIONS.md.",
    )
    has_battery = st.toggle("Battery (5 kWh)", value=True)
    export_mode = st.selectbox(
        "Can the home sell power?", ["none", "net_billing", "net_metering"],
        format_func=lambda v: {
            "none": "No - not registered (surplus is wasted)",
            "net_billing": "Net billing (~Rs 11/unit, contested)",
            "net_metering": "Net metering 1:1 (comparison only)",
        }[v],
    )
    solar_kw = st.slider("Solar system size (kW)", 1.0, 10.0, float(config["solar_kw"]), 0.5)
    power_cuts = st.toggle("Daily power cut (20:00-21:00)", value=True)
    st.caption("Runs from cached weather. No internet needed.")

results = _simulate(household, has_battery, export_mode, solar_kw, power_cuts)
usual, agent = results["usual"], results["agent"]
um, am = usual["metrics"], agent["metrics"]


def delta_text(before: float, after: float, unit: str = "") -> str:
    """Signed change, phrased so that less is better."""
    difference = after - before
    return f"{difference:+.1f}{unit}" if difference else "no change"


st.subheader("The month at a glance")
columns = st.columns(5)
columns[0].metric("Grid units bought", f"{am['grid_units_month']:g}",
                  delta_text(um["grid_units_month"], am["grid_units_month"]),
                  delta_color="inverse", help=f"Usual behaviour: {um['grid_units_month']:g} units")
columns[1].metric("Evening units (18-22)", f"{am['evening_grid_units']:g}",
                  delta_text(um["evening_grid_units"], am["evening_grid_units"]),
                  delta_color="inverse", help=f"Usual behaviour: {um['evening_grid_units']:g} units")
columns[2].metric("Peak grid draw", f"{am['peak_grid_kw']:g} kW",
                  delta_text(um["peak_grid_kw"], am["peak_grid_kw"], " kW"),
                  delta_color="inverse", help=f"Usual behaviour: {um['peak_grid_kw']:g} kW")
columns[3].metric("Hours with no power", f"{am['unmet_hours']}",
                  delta_text(um["unmet_hours"], am["unmet_hours"]),
                  delta_color="inverse", help="During power cuts, when the battery cannot cover the load")
columns[4].metric("Cost of units bought", f"Rs {am['energy_cost_rs']:,.0f}",
                  delta_text(um["energy_cost_rs"], am["energy_cost_rs"]),
                  delta_color="inverse",
                  help=f"Usual behaviour: Rs {um['energy_cost_rs']:,.0f}. Excludes taxes, duties and "
                       f"fuel adjustments, so a real bill would be higher.")

fair = st.columns(3)
fair[0].metric("Units per 100 kWh actually served", f"{am['grid_units_per_100kwh_served']:g}",
               delta_text(um["grid_units_per_100kwh_served"], am["grid_units_per_100kwh_served"]),
               delta_color="inverse",
               help="A home that goes dark in a power cut looks cheaper, so units bought are "
                    "shown per kWh actually delivered.")
fair[1].metric("Solar wasted", f"{am['solar_wasted_kwh']:g} kWh",
               delta_text(um["solar_wasted_kwh"], am["solar_wasted_kwh"], " kWh"),
               delta_color="inverse", help="Surplus the home could neither use, store nor sell")
fair[2].metric("Agent refusals", f"{am['refusals']}",
               help="Times the agent declined to move an appliance because it was not confident enough")

if export_mode != "none":
    st.info(
        f"**Selling surplus is shown separately, not netted into one figure.** Units bought cost "
        f"**Rs {am['energy_cost_rs']:,.0f}**; the modelled credit for "
        f"**{am['solar_exported_kwh']:g} kWh** exported is **Rs {am['export_credit_rs']:,.0f}**. "
        "The Rs 11/unit net-billing rate is **reported and contested**, applies to new users from "
        "Feb 2026, and real schemes may carry a credit forward rather than pay it out. Treat the "
        "credit as an illustration of scale, not an income estimate.",
        icon=":material/info:",
    )

if am["grid_units_month"] > um["grid_units_month"]:
    st.info(
        f"In this scenario the agent buys **{am['grid_units_month'] - um['grid_units_month']:.1f} more units** "
        f"but serves **{am['load_served_kwh'] - um['load_served_kwh']:.1f} kWh more** of the home's demand, "
        f"cutting time without power from {um['unmet_hours']} to {am['unmet_hours']} hours. It holds battery "
        "charge back for the power cut instead of spending it in the afternoon - a trade-off, not a win.",
        icon=":material/info:",
    )

if not am["protected_kept"] and household == "low_use":
    st.error(f"This home crosses the 200-unit limit, so it pays **unprotected** rates on every unit "
             f"and loses protected status for six months.", icon=":material/warning:")

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("A day in detail")
    days = sorted(agent["hourly"]["time"].dt.date.unique())
    day = st.select_slider("Day", options=days, value=days[19],
                           format_func=lambda d: d.strftime("%d %b"))
    day_str = str(day)

    frames = []
    for mode, payload in (("Usual", usual), ("Agent", agent)):
        slice_ = payload["hourly"][payload["hourly"]["time"].dt.date.astype(str) == day_str]
        frames.append(pd.DataFrame({
            "Hour": slice_["hour"],
            f"{mode}: household load": slice_["load_kwh"].values,
            f"{mode}: bought from grid": slice_["grid_import_kwh"].values,
        }).set_index("Hour"))
    solar_slice = agent["hourly"][agent["hourly"]["time"].dt.date.astype(str) == day_str]
    chart = pd.concat(frames, axis=1)
    chart["Solar generated"] = solar_slice["solar_kwh"].values
    st.line_chart(chart, height=320)
    st.caption("Solar peaks at midday; the agent lifts demand into those hours and flattens the evening.")

    if has_battery:
        battery = pd.DataFrame({
            "Hour": solar_slice["hour"],
            "Usual": usual["hourly"][usual["hourly"]["time"].dt.date.astype(str) == day_str]["soc_kwh"].values,
            "Agent": solar_slice["soc_kwh"].values,
        }).set_index("Hour")
        st.caption("Battery charge through the day (kWh)")
        st.area_chart(battery, height=180)

with right:
    st.subheader("Units bought over the month")
    cumulative = pd.DataFrame({
        "Date": agent["hourly"]["time"],
        "Usual": usual["hourly"]["grid_import_kwh"].cumsum().values,
        "Agent": agent["hourly"]["grid_import_kwh"].cumsum().values,
        "200-unit protected limit": config["agent"]["guard_threshold_units"],
    }).set_index("Date")
    st.line_chart(cumulative, height=320)
    st.caption(
        f"Usual behaviour ends the month at {um['grid_units_month']:g} units, the agent at "
        f"{am['grid_units_month']:g}. Crossing 200 re-prices every unit at unprotected rates."
    )

    st.subheader("What the agent told the family")
    messages = [m for m in agent["notifications"] if m["date"] == day_str]
    if not messages:
        st.caption("No messages for this day.")
    for message in sorted(messages, key=lambda m: m["hour"]):
        icon = {"shifted": ":material/schedule:", "refused": ":material/block:",
                "precool": ":material/ac_unit:", "battery": ":material/battery_charging_full:",
                "guard": ":material/warning:"}.get(message["kind"], ":material/info:")
        with st.container(border=True):
            st.markdown(f"{icon} **{message['time']} - {message['kind'].upper()}**  \n{message['message']}")
            st.caption(f"confidence {message['confidence_pct']}% - margin from {message['margin_source']}")

st.divider()
with st.expander("Assumptions and limits for this run"):
    st.markdown(
        f"""
- Forecast is the **real day-ahead forecast** (Open-Meteo `*_previous_day1`), wrong by
  **{am['mean_forecast_error_wm2']} W/m2** on average, so the agent's margin and refusals are real.
- The agent held back **{am['mean_margin_kw']} kW** per hour on average as a safety margin.
- Pre-cooling (1.0 kWh spent to save 0.6 kWh in the evening) is **a rough estimate, not measured**.
- Tariff: protected rates are as reported; **six of the eight unprotected band rates are
  placeholders** (interpolated). Taxes and fuel adjustments are **excluded**, so bills here are
  lower than real ones.
- Net billing at ~Rs 11/unit is **reported and contested**, and is never used as a headline figure.
- `low_use` is calibrated to a configurable monthly target (currently **assumed**, to be set from a
  real bill).
- Assumes a **hybrid inverter** that keeps running in a power cut; many real systems shut down.
"""
    )
