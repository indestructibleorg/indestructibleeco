"""Numerical calculus - integration and differentiation."""
from __future__ import annotations
from typing import Any
import numpy as np


class NumericalCalculus:
    def integrate(self, function: str, lower_bound: float, upper_bound: float, method: str) -> dict[str, Any]:
        from scipy import integrate as sci_integrate
        import math

        safe_ns = {"x": None, "sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp,
                    "log": np.log, "sqrt": np.sqrt, "pi": np.pi, "e": np.e, "abs": np.abs,
                    "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh, "arcsin": np.arcsin,
                    "arccos": np.arccos, "arctan": np.arctan}

        def f(x: float) -> float:
            ns = {**safe_ns, "x": x}
            return float(eval(function, {"__builtins__": {}}, ns))

        try:
            if method == "quad":
                result, error = sci_integrate.quad(f, lower_bound, upper_bound)
            elif method == "trapezoid":
                x = np.linspace(lower_bound, upper_bound, 1000)
                y = np.array([f(xi) for xi in x])
                result = float(np.trapezoid(y, x) if hasattr(np, 'trapezoid') else np.trapz(y, x))
                error = abs(result - sci_integrate.quad(f, lower_bound, upper_bound)[0])
            elif method == "simpson":
                from scipy.integrate import simpson
                x = np.linspace(lower_bound, upper_bound, 1001)
                y = np.array([f(xi) for xi in x])
                result = float(simpson(y, x=x))
                error = abs(result - sci_integrate.quad(f, lower_bound, upper_bound)[0])
            elif method == "romberg":
                if hasattr(sci_integrate, 'romberg'):
                    result = float(sci_integrate.romberg(f, lower_bound, upper_bound))
                else:
                    # scipy >= 1.14 removed romberg; fall back to quad
                    result = float(sci_integrate.quad(f, lower_bound, upper_bound)[0])
                error = abs(result - sci_integrate.quad(f, lower_bound, upper_bound)[0])
            else:
                return {"error": f"Unknown method: {method}"}

            return {
                "function": function,
                "bounds": [lower_bound, upper_bound],
                "method": method,
                "result": round(result, 10),
                "estimated_error": round(float(error), 12),
            }
        except Exception as e:
            return {"error": str(e)}