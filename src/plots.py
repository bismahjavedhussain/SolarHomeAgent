"""The three charts: a typical day, the month, and the scenario comparison."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SOLAR, LOAD, GRID, WASTE, SOC = "#E8A33D", "#2F6F8F", "#C2453B", "#9A9A9A", "#4C9A6A"


def day_chart(usual: pd.DataFrame, agent: pd.DataFrame, day: str, path, export_mode: str = "none"):
    """Side-by-side hour-by-hour view of one day, usual vs agent."""
    surplus_label = "Exported" if export_mode in ("net_billing", "net_metering") else "Wasted"
    surplus_column = "exported_kwh" if export_mode in ("net_billing", "net_metering") else "wasted_kwh"

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    handles: list = []
    for ax, frame, title in zip(axes, (usual, agent), ("Usual behaviour", "Agent")):
        slice_ = frame[frame["time"].dt.date.astype(str) == day]
        hours = slice_["hour"]
        ax.fill_between(hours, slice_["solar_kwh"], color=SOLAR, alpha=0.45, label="Solar generated")
        ax.plot(hours, slice_["load_kwh"], color=LOAD, lw=2, label="Household load")
        ax.plot(hours, slice_["grid_import_kwh"], color=GRID, lw=2, label="Bought from grid")
        ax.plot(hours, slice_[surplus_column], color=WASTE, lw=1.6, ls="--", label=f"{surplus_label} solar")
        if slice_["soc_kwh"].max() > 0:
            twin = ax.twinx()  # battery sits on its own axis, so it is named in the legend to avoid confusion
            twin.plot(hours, slice_["soc_kwh"], color=SOC, lw=1.8, ls=":", label="Battery stored (right axis)")
            twin.set_ylim(0, max(5.2, slice_["soc_kwh"].max() * 1.15))
            twin.set_ylabel("Battery stored (kWh)", color=SOC)
            if not handles:
                handles = twin.get_legend_handles_labels()[0]
        for start, end in _outage_windows(slice_):
            ax.axvspan(start, end, color="#000000", alpha=0.07)
        ax.set_title(title)
        ax.set_xlabel("Hour of day")
        ax.set_xticks(range(0, 24, 3))
    axes[0].set_ylabel("kWh per hour")
    left_handles, left_labels = axes[0].get_legend_handles_labels()
    battery_labels = [h.get_label() for h in handles]
    axes[0].legend(left_handles + handles, left_labels + battery_labels, loc="upper left", fontsize=8)
    fig.suptitle(f"A day in detail: {day}  (shaded = power cut)", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def _outage_windows(frame: pd.DataFrame) -> list[tuple[int, int]]:
    """Outage hours in a day as spans, for shading."""
    hours = sorted(frame[frame["in_outage"]]["hour"].tolist())
    return [(hour, hour + 1) for hour in hours]


def month_chart(usual: pd.DataFrame, agent: pd.DataFrame, threshold: int, path):
    """Cumulative grid units across the month, with the protected threshold marked."""
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for frame, label, colour in ((usual, "Usual behaviour", GRID), (agent, "Agent", SOC)):
        cumulative = frame["grid_import_kwh"].cumsum()
        ax.plot(frame["time"], cumulative, label=f"{label} ({cumulative.iloc[-1]:.0f} units)", lw=2, color=colour)
    ax.axhline(threshold, color="#000000", ls="--", lw=1.2, alpha=0.7)
    ax.annotate(f"{threshold}-unit protected limit", xy=(usual["time"].iloc[len(usual) // 2], threshold),
                xytext=(0, 6), textcoords="offset points", fontsize=9)
    ax.set_ylabel("Grid units bought, running total")
    ax.set_xlabel("Date")
    ax.set_title("Units bought from the grid over the month")
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def scenario_chart(summary: pd.DataFrame, path):
    """Monthly and evening grid units for usual vs agent across every scenario."""
    labels = summary["scenario"].tolist()
    positions = range(len(labels))
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    for ax, (column, title) in zip(axes, [("grid_units_month", "Grid units bought in the month"),
                                          ("evening_grid_units", "Evening grid units (18:00-22:00)")]):
        ax.bar([p - 0.2 for p in positions], summary[f"usual_{column}"], width=0.4, label="Usual", color=GRID)
        ax.bar([p + 0.2 for p in positions], summary[f"agent_{column}"], width=0.4, label="Agent", color=SOC)
        ax.set_ylabel("Units (kWh)")
        ax.set_title(title)
        ax.legend()
    axes[0].axhline(200, color="#000000", ls="--", lw=1.0, alpha=0.6)
    axes[-1].set_xticks(list(positions))
    axes[-1].set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    fig.suptitle("Every scenario: usual vs agent", y=0.98)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
