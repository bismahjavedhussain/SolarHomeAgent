"""Turn solar radiation into panel output."""
from __future__ import annotations

import pandas as pd


def solar_kw(ghi_wm2: pd.Series | float, solar_kw_rating: float, derate: float) -> pd.Series | float:
    """Panel output in kW: rating x (radiation / 1000) x derate. No tilt model in v0."""
    return solar_kw_rating * (ghi_wm2 / 1000.0) * derate
