"""Download and cache Islamabad weather; offline-first so the repo runs without network."""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
import yaml

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG_PATH = ROOT / "config" / "scenario.yaml"

# Actuals come from the archive; the forecast is the one issued a day earlier.
ACTUAL_VARS = ["shortwave_radiation", "temperature_2m", "cloud_cover"]
FORECAST_VARS = [
    "shortwave_radiation_previous_day1",
    "temperature_2m_previous_day1",
    "cloud_cover_previous_day1",
]
COLUMNS = {"shortwave_radiation": "ghi_wm2", "temperature_2m": "temp_c", "cloud_cover": "cloud_pct"}


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Read scenario.yaml."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def month_bounds(month: str) -> tuple[str, str, str]:
    """Return (first day, last day, day after last) as ISO dates for a 'YYYY-MM' string."""
    start = pd.Timestamp(f"{month}-01")
    last = start + pd.offsets.MonthEnd(0)
    return start.date().isoformat(), last.date().isoformat(), (last + pd.Timedelta(days=1)).date().isoformat()


def _request(base: str, lat: float, lon: float, start: str, end: str, tz: str, variables: list[str]) -> dict:
    """Call an Open-Meteo endpoint and return the parsed JSON."""
    query = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start,
            "end_date": end,
            "hourly": ",".join(variables),
            "timezone": tz,
        }
    )
    with urllib.request.urlopen(f"{base}?{query}", timeout=90) as response:
        return json.load(response)


def _to_frame(payload: dict, variables: list[str]) -> pd.DataFrame:
    """Turn an Open-Meteo hourly block into a tidy frame with standard column names."""
    hourly = payload["hourly"]
    frame = pd.DataFrame({"time": pd.to_datetime(hourly["time"])})
    for name in variables:
        frame[COLUMNS[name.replace("_previous_day1", "")]] = hourly[name]
    return frame


def shift_radiation_to_hour_start(frame: pd.DataFrame) -> pd.DataFrame:
    """Re-label radiation so row h is the mean over [h, h+1) instead of the preceding hour."""
    out = frame.copy()
    out["ghi_wm2"] = out["ghi_wm2"].shift(-1)
    return out


def _prepare(payload: dict, variables: list[str], start: str, end: str) -> pd.DataFrame:
    """Shift radiation, then trim the extra fetched day away."""
    frame = shift_radiation_to_hour_start(_to_frame(payload, variables))
    mask = (frame["time"] >= pd.Timestamp(start)) & (frame["time"] < pd.Timestamp(end) + pd.Timedelta(days=1))
    frame = frame.loc[mask].reset_index(drop=True)
    frame["ghi_wm2"] = frame["ghi_wm2"].clip(lower=0.0)
    return frame


def cache_paths(month: str) -> tuple[Path, Path]:
    """Where the two cached CSVs live for a given month."""
    return DATA_DIR / f"weather_actual_{month}.csv", DATA_DIR / f"weather_forecast_{month}.csv"


def download(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch actual and day-ahead-forecast weather, fetching one extra day for the shift."""
    month = str(config["month"])
    loc = config["location"]
    start, end, day_after = month_bounds(month)
    args = (loc["latitude"], loc["longitude"], start, day_after, loc["timezone"])

    actual = _prepare(_request(ARCHIVE_URL, *args, ACTUAL_VARS), ACTUAL_VARS, start, end)
    forecast = _prepare(_request(FORECAST_URL, *args, FORECAST_VARS), FORECAST_VARS, start, end)
    return actual, forecast


def load_weather(config: dict, refresh: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (actual, forecast) frames from cache, downloading only when needed."""
    month = str(config["month"])
    actual_path, forecast_path = cache_paths(month)

    if not refresh and actual_path.exists() and forecast_path.exists():
        actual = pd.read_csv(actual_path, parse_dates=["time"])
        forecast = pd.read_csv(forecast_path, parse_dates=["time"])
        return actual, forecast

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    actual, forecast = download(config)
    actual.to_csv(actual_path, index=False)
    forecast.to_csv(forecast_path, index=False)
    return actual, forecast


def forecast_error_table(actual: pd.DataFrame, forecast: pd.DataFrame) -> pd.DataFrame:
    """Per hour-of-day forecast-minus-actual solar error, the basis of the agent's margin."""
    merged = actual.merge(forecast, on="time", suffixes=("_act", "_fc"))
    merged["hour"] = merged["time"].dt.hour
    merged["error"] = merged["ghi_wm2_fc"] - merged["ghi_wm2_act"]
    grouped = merged.groupby("hour").agg(
        mean_actual_ghi=("ghi_wm2_act", "mean"),
        mean_error=("error", "mean"),
        p80_abs_error=("error", lambda s: s.abs().quantile(0.80)),
    )
    return grouped.round(1)


def _plot_check(actual: pd.DataFrame, days: int = 3) -> Path:
    """Save a solar-vs-temperature sanity plot for the first few days."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    window = actual.head(days * 24)
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(window["time"], window["ghi_wm2"], color="#E8A33D", label="Solar radiation (W/m2)")
    ax.set_ylabel("Solar radiation (W/m2)", color="#B8761A")
    ax.set_xlabel("Time (Asia/Karachi)")
    twin = ax.twinx()
    twin.plot(window["time"], window["temp_c"], color="#C2453B", label="Temperature (C)")
    twin.set_ylabel("Temperature (C)", color="#C2453B")
    ax.set_title(f"Islamabad, first {days} days: solar radiation vs temperature (actual)")
    fig.autofmt_xdate()
    fig.tight_layout()
    out = ROOT / "results" / "data_check.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def main() -> None:
    """Fetch or load the month's weather, then print a short verification report."""
    parser = argparse.ArgumentParser(description="Fetch and cache weather for the simulation month.")
    parser.add_argument("--refresh", action="store_true", help="re-download even if cached")
    args = parser.parse_args()

    config = load_config()
    actual, forecast = load_weather(config, refresh=args.refresh)

    print(f"month: {config['month']}   location: {config['location']['name']}")
    print(f"actual rows:   {len(actual)}  {actual['time'].min()} -> {actual['time'].max()}")
    print(f"forecast rows: {len(forecast)}  {forecast['time'].min()} -> {forecast['time'].max()}")
    print(f"missing values: actual={int(actual.isna().sum().sum())} forecast={int(forecast.isna().sum().sum())}")
    print(f"mean daily solar energy: {actual['ghi_wm2'].sum() / 1000 / (len(actual) / 24):.2f} kWh/m2")
    print(f"temperature: mean {actual['temp_c'].mean():.1f} C, max {actual['temp_c'].max():.1f} C")
    print("\nDay-ahead forecast error by hour of day (W/m2):")
    print(forecast_error_table(actual, forecast).to_string())
    mean_abs = (forecast["ghi_wm2"] - actual["ghi_wm2"]).abs().mean()
    print(f"\nmonth mean |forecast error|: {mean_abs:.1f} W/m2")
    print(f"saved plot: {_plot_check(actual)}")


if __name__ == "__main__":
    main()
