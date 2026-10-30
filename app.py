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
              power_cuts: bool, followed_pct: int) -> dict:
    """Run both modes for one scenario and return frames, metrics and messages."""
    base = _config()
    config = dict(base, agent=dict(base["agent"], suggestions_followed_pct=followed_pct))
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

st.title("Solar Home Agent - Pakistan (prototype)")
st.warning(
    "**This is a simulation, not a real home.** It runs one real month of Islamabad weather "
    "(June 2025) against modelled appliances. Several inputs are rough estimates and some tariff "
    "rates are placeholders. No claim is made about real-world savings. See ASSUMPTIONS.md.",
    icon=":material/warning:",
)

with st.sidebar:
    st.header("Scenario")
    household_labels = {
        "low_use": "Low use - 1 AC, safely under 200 units",
        "at_risk": "At risk - 1 AC, currently just over 200 units",
        "high_use": "High use - 2 ACs, well over the limit",
    }
    household = st.radio(
        "Household", list(config["households"]),
        format_func=lambda v: household_labels.get(v, v),
        help="Each profile's baseline is calibrated to a configurable monthly target of grid units. "
             "Those targets are assumptions, to be set from a real bill. See ASSUMPTIONS.md.",
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
    followed_pct = st.slider(
        "Suggestions the family acts on (%)", 0, 100,
        int(config["agent"]["suggestions_followed_pct"]), 10,
        help="Nobody follows every suggestion. Battery planning is automatic and always applies; "
             "appliance timing and pre-cooling need someone to act. To be set from the survey.",
    )
    st.caption("Runs from cached weather. No internet needed.")

results = _simulate(household, has_battery, export_mode, solar_kw, power_cuts, followed_pct)
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

fair = st.columns(4)
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
fair[3].metric("Promises kept", f"{am['promises_kept_pct']}%" if am["promises_kept_pct"] is not None else "-",
               help=f"Of the {am['promises_made']} times it said your panels would cover an appliance, "
                    f"how often the sun actually delivered. This is the agent marking its own homework.")

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

if um["protected_loss_6mo_rs"] > 0 and am["protected_loss_6mo_rs"] == 0:
    st.success(
        f"**Usual behaviour crosses the {config['agent']['guard_threshold_units']}-unit limit and the "
        f"agent does not.** Crossing re-prices every unit at unprotected rates for "
        f"{config['tariff']['protected_status_months']} months, which on this month's usage would cost "
        f"about **Rs {um['protected_loss_6mo_rs']:,.0f} extra**, assuming usage repeats.",
        icon=":material/savings:")
elif not am["protected_kept"] and config["households"][household]["protected_eligible"]:
    st.error(
        f"This home crosses the {config['agent']['guard_threshold_units']}-unit limit in both modes, so it "
        f"pays **unprotected** rates on every unit and loses protected status for "
        f"{config['tariff']['protected_status_months']} months - about "
        f"**Rs {am['protected_loss_6mo_rs']:,.0f} extra**, if usage repeats.",
        icon=":material/warning:")

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("A day in detail")
    days = sorted(agent["hourly"]["time"].dt.date.unique())
    refusal_dates = [m["date"] for m in agent["notifications"] if m["kind"] == "refused"]
    default_day = next((d for d in days if str(d) in refusal_dates), days[len(days) // 2])
    day = st.select_slider("Day", options=days, value=default_day,
                           format_func=lambda d: d.strftime("%d %b"))
    if refusal_dates:
        st.caption("Opens on a day the agent refused to move something - the decision worth seeing.")
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
                "guard": ":material/warning:", "ignored": ":material/person_off:"}.get(
                    message["kind"], ":material/info:")
        with st.container(border=True):
            st.markdown(f"{icon} **{message['time']} - {message['kind'].upper()}**  \n{message['message']}")
            st.caption(f"confidence {message['confidence_pct']}% - margin from {message['margin_source']}")

st.divider()
top_fixed_charge = config["tariff"]["fixed_charge_per_kw"][-1]
essential_kw = config["power_cut_essential_load_kw"]
protected_months = config["tariff"]["protected_status_months"]
with st.expander("Assumptions and limits for this run"):
    st.markdown(
        f"""
- Forecast is the **real day-ahead forecast** (Open-Meteo `*_previous_day1`), wrong by
  **{am['mean_forecast_error_wm2']} W/m2** on average, so the agent's margin and refusals are real.
- The agent held back **{am['mean_margin_kw']} kW** per hour on average as a safety margin.
- Pre-cooling (1.0 kWh spent to save 0.6 kWh in the evening) is **a rough estimate, not measured**.
- Tariff: band rates are the **reported S.R.O. 279(I)/2026** figures and still need checking
  against NEPRA. Fixed charges of up to Rs {top_fixed_charge}/kW of sanctioned load apply above the lower bands. Taxes, duty and fuel
  adjustments are **excluded**, so bills here are lower than real ones.
- The family acts on **{followed_pct}%** of suggestions in this run, a deterministic pattern of days.
- Net billing at ~Rs 11/unit is **reported and contested**, and is never used as a headline figure.
- `low_use` is calibrated to a configurable monthly target (currently **assumed**, to be set from a
  real bill).
- During a power cut only **essential loads** ({essential_kw} kW of fans, lights and router) run; the
  AC and flexible appliances do not. Assumes a **hybrid inverter**; many real systems shut down
  entirely.
"""
    )
