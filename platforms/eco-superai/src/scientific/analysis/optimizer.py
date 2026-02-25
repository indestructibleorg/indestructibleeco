"""Scientific optimization using SciPy."""
from __future__ import annotations
from typing import Any
import numpy as np


class ScientificOptimizer:
    def solve(self, method: str, objective: str, bounds: list[list[float]], constraints: list[dict[str, Any]], initial_guess: list[float], parameters: dict[str, Any]) -> dict[str, Any]:
        from scipy import optimize as sci_opt

        safe_ns = {"sin": np.sin, "cos": np.cos, "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "pi": np.pi, "abs": np.abs, "sum": np.sum}

        try:
            if method == "minimize":
                def obj_func(x: np.ndarray) -> float:
                    ns = {**safe_ns, "x": x}
                    for i, val in enumerate(x):
                        ns[f"x{i}"] = val
                    return float(eval(objective, {"__builtins__": {}}, ns))

                x0 = np.array(initial_guess) if initial_guess else np.zeros(parameters.get("dimensions", 2))
                scipy_bounds = [(b[0], b[1]) for b in bounds] if bounds else None
                scipy_constraints = []
                for c in constraints:
                    scipy_constraints.append({"type": c.get("type", "ineq"), "fun": lambda x, expr=c.get("expression", "0"): float(eval(expr, {"__builtins__": {}}, {**safe_ns, "x": x}))})

                result = sci_opt.minimize(obj_func, x0, bounds=scipy_bounds, constraints=scipy_constraints or None, method=parameters.get("scipy_method", "SLSQP"), options={"maxiter": parameters.get("max_iterations", 1000)})

                return {
                    "method": "minimize",
                    "optimal_value": round(float(result.fun), 10),
                    "optimal_point": result.x.tolist(),
                    "converged": bool(result.success),
                    "message": result.message,
                    "iterations": int(result.nit) if hasattr(result, "nit") else int(result.nfev),
                    "function_evaluations": int(result.nfev),
                }

            elif method == "root":
                def root_func(x: np.ndarray) -> float:
                    ns = {**safe_ns, "x": x if len(x) > 1 else x[0]}
                    return float(eval(objective, {"__builtins__": {}}, ns))

                x0 = np.array(initial_guess) if initial_guess else np.array([1.0])
                result = sci_opt.root(root_func, x0)
                return {"method": "root", "root": result.x.tolist(), "converged": bool(result.success), "function_value": result.fun.tolist() if hasattr(result.fun, "tolist") else float(result.fun)}

            elif method == "linprog":
                c = parameters.get("c", [])
                A_ub = parameters.get("A_ub")
                b_ub = parameters.get("b_ub")
                A_eq = parameters.get("A_eq")
                b_eq = parameters.get("b_eq")
                result = sci_opt.linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds or None)
                return {"method": "linprog", "optimal_value": round(float(result.fun), 10), "optimal_point": result.x.tolist(), "converged": bool(result.success), "message": result.message}

            elif method == "curve_fit":
                x_data = np.array(parameters.get("x_data", []))
                y_data = np.array(parameters.get("y_data", []))
                def model_func(x: np.ndarray, *params: float) -> np.ndarray:
                    ns = {**safe_ns, "x": x}
                    for i, p in enumerate(params):
                        ns[f"a{i}"] = p
                    return eval(objective, {"__builtins__": {}}, ns)
                p0 = initial_guess or [1.0] * parameters.get("num_params", 2)
                popt, pcov = sci_opt.curve_fit(model_func, x_data, y_data, p0=p0)
                residuals = y_data - model_func(x_data, *popt)
                return {"method": "curve_fit", "parameters": popt.tolist(), "covariance": pcov.tolist(), "residual_std": float(np.std(residuals)), "r_squared": round(float(1 - np.sum(residuals**2) / np.sum((y_data - np.mean(y_data))**2)), 6)}

            else:
                return {"error": f"Unknown method: {method}"}

        except Exception as e:
            return {"error": str(e)}