"""Statistical analysis using Pandas and SciPy."""
from __future__ import annotations

from typing import Any

import numpy as np


class StatisticalAnalyzer:
    """Comprehensive statistical analysis engine."""

    def analyze(self, data: list[list[float]], columns: list[str], operations: list[str]) -> dict[str, Any]:
        import pandas as pd
        from scipy import stats as scipy_stats

        df = pd.DataFrame(data, columns=columns if columns else [f"col_{i}" for i in range(len(data[0]))])
        results: dict[str, Any] = {"shape": list(df.shape), "columns": list(df.columns)}

        for op in operations:
            if op == "describe":
                desc = df.describe().to_dict()
                results["describe"] = {k: {kk: round(vv, 6) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in desc.items()}

            elif op == "correlation":
                corr = df.corr()
                results["correlation"] = {k: {kk: round(vv, 6) for kk, vv in v.items()} for k, v in corr.to_dict().items()}

            elif op == "covariance":
                cov = df.cov()
                results["covariance"] = {k: {kk: round(vv, 6) for kk, vv in v.items()} for k, v in cov.to_dict().items()}

            elif op == "histogram":
                histograms = {}
                for col in df.columns:
                    counts, bin_edges = np.histogram(df[col].dropna(), bins="auto")
                    histograms[col] = {"counts": counts.tolist(), "bin_edges": [round(b, 6) for b in bin_edges.tolist()]}
                results["histogram"] = histograms

            elif op == "outliers":
                outliers = {}
                for col in df.select_dtypes(include=[np.number]).columns:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - 1.5 * IQR
                    upper = Q3 + 1.5 * IQR
                    mask = (df[col] < lower) | (df[col] > upper)
                    outlier_indices = df[mask].index.tolist()
                    outliers[col] = {
                        "count": int(mask.sum()),
                        "indices": outlier_indices[:50],
                        "bounds": {"lower": round(float(lower), 6), "upper": round(float(upper), 6)},
                        "iqr": round(float(IQR), 6),
                    }
                results["outliers"] = outliers

            elif op == "normality":
                normality = {}
                for col in df.select_dtypes(include=[np.number]).columns:
                    col_data = df[col].dropna()
                    if len(col_data) >= 8:
                        stat, p_value = scipy_stats.shapiro(col_data[:5000])
                        skew = float(scipy_stats.skew(col_data))
                        kurt = float(scipy_stats.kurtosis(col_data))
                        normality[col] = {
                            "shapiro_stat": round(float(stat), 6),
                            "shapiro_p_value": round(float(p_value), 6),
                            "is_normal": bool(p_value > 0.05),
                            "skewness": round(skew, 6),
                            "kurtosis": round(kurt, 6),
                        }
                results["normality"] = normality

            elif op == "distribution_fit":
                fits = {}
                for col in df.select_dtypes(include=[np.number]).columns:
                    col_data = df[col].dropna().values
                    distributions = ["norm", "expon", "lognorm", "gamma"]
                    best_fit = {"name": "", "params": {}, "ks_stat": float("inf")}
                    for dist_name in distributions:
                        try:
                            dist = getattr(scipy_stats, dist_name)
                            params = dist.fit(col_data)
                            ks_stat, _ = scipy_stats.kstest(col_data, dist_name, args=params)
                            if ks_stat < best_fit["ks_stat"]:
                                best_fit = {"name": dist_name, "params": [round(p, 6) for p in params], "ks_stat": round(float(ks_stat), 6)}
                        except Exception:
                            continue
                    fits[col] = best_fit
                results["distribution_fit"] = fits

        return results