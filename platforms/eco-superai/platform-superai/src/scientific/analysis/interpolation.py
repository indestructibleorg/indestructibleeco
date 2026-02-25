"""Interpolation using SciPy."""
from __future__ import annotations
from typing import Any
import numpy as np


class Interpolator:
    def interpolate(self, x_data: list[float], y_data: list[float], x_new: list[float], method: str) -> dict[str, Any]:
        from scipy import interpolate as sci_interp
        x = np.array(x_data)
        y = np.array(y_data)
        x_n = np.array(x_new)
        try:
            if method == "linear":
                f = sci_interp.interp1d(x, y, kind="linear", fill_value="extrapolate")
            elif method == "cubic":
                f = sci_interp.interp1d(x, y, kind="cubic", fill_value="extrapolate")
            elif method == "quadratic":
                f = sci_interp.interp1d(x, y, kind="quadratic", fill_value="extrapolate")
            elif method == "nearest":
                f = sci_interp.interp1d(x, y, kind="nearest", fill_value="extrapolate")
            elif method == "pchip":
                f = sci_interp.PchipInterpolator(x, y)
            else:
                return {"error": f"Unknown method: {method}"}
            y_new = f(x_n)
            return {"method": method, "x_new": x_n.tolist(), "y_interpolated": y_new.tolist(), "points_count": len(x_new)}
        except Exception as e:
            return {"error": str(e)}