"""Matrix operations using NumPy."""
from __future__ import annotations

from typing import Any

import numpy as np


class MatrixOperations:
    """High-performance matrix operations."""

    def execute(self, operation: str, matrix_a: list[list[float]], matrix_b: list[list[float]] | None = None, vector_b: list[float] | None = None) -> dict[str, Any]:
        A = np.array(matrix_a)

        try:
            if operation == "multiply":
                if matrix_b is None:
                    return {"error": "matrix_b required for multiply"}
                B = np.array(matrix_b)
                result = (A @ B).tolist()
                return {"operation": "multiply", "result": result, "shape": list(np.array(result).shape)}

            elif operation == "inverse":
                inv = np.linalg.inv(A)
                verification = (A @ inv).tolist()
                return {"operation": "inverse", "result": inv.tolist(), "verification_identity": verification, "determinant": float(np.linalg.det(A))}

            elif operation == "eigenvalues":
                eigenvalues, eigenvectors = np.linalg.eigh(A) if np.allclose(A, A.T) else np.linalg.eig(A)
                return {
                    "operation": "eigenvalues",
                    "eigenvalues": [float(v) if np.isreal(v) else {"real": float(v.real), "imag": float(v.imag)} for v in eigenvalues],
                    "eigenvectors": eigenvectors.tolist(),
                    "is_symmetric": bool(np.allclose(A, A.T)),
                }

            elif operation == "svd":
                U, S, Vt = np.linalg.svd(A)
                return {
                    "operation": "svd",
                    "U": U.tolist(),
                    "singular_values": S.tolist(),
                    "Vt": Vt.tolist(),
                    "rank": int(np.linalg.matrix_rank(A)),
                    "condition_number": float(np.linalg.cond(A)),
                }

            elif operation == "determinant":
                det = np.linalg.det(A)
                return {"operation": "determinant", "result": float(det), "is_singular": bool(abs(det) < 1e-10)}

            elif operation == "transpose":
                return {"operation": "transpose", "result": A.T.tolist()}

            elif operation == "norm":
                return {
                    "operation": "norm",
                    "frobenius": float(np.linalg.norm(A, "fro")),
                    "l1": float(np.linalg.norm(A, 1)),
                    "l2": float(np.linalg.norm(A, 2)),
                    "inf": float(np.linalg.norm(A, np.inf)),
                }

            elif operation == "solve":
                if vector_b is None:
                    return {"error": "vector_b required for solve (Ax=b)"}
                b = np.array(vector_b)
                x = np.linalg.solve(A, b)
                residual = np.linalg.norm(A @ x - b)
                return {"operation": "solve", "solution": x.tolist(), "residual": float(residual)}

            else:
                return {"error": f"Unknown operation: {operation}"}

        except np.linalg.LinAlgError as e:
            return {"error": f"Linear algebra error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}