"""Machine Learning trainer using Scikit-learn."""
from __future__ import annotations

import time
import uuid
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

# In-memory model store (production: use MLflow/S3)
_MODEL_STORE: dict[str, Any] = {}


class MLTrainer:
    """Scikit-learn based ML training and prediction engine."""

    async def train(self, algorithm: str, features: list[list[float]], labels: list[float] | list[int] | None,
                    test_size: float, hyperparameters: dict[str, Any], cross_validation: int) -> dict[str, Any]:
        start = time.perf_counter()
        model_id = str(uuid.uuid4())

        try:
            from sklearn.model_selection import train_test_split, cross_val_score
            from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                                         mean_squared_error, r2_score, silhouette_score)
            from sklearn.preprocessing import StandardScaler

            X = np.array(features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model = self._create_model(algorithm, hyperparameters)
            metrics: dict[str, Any] = {}
            is_supervised = labels is not None

            if is_supervised:
                y = np.array(labels)
                X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_size, random_state=42)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                is_classification = algorithm in ("logistic_regression", "random_forest", "svm", "decision_tree", "knn", "gradient_boosting") and len(set(y.tolist())) <= 20

                if is_classification:
                    avg = "binary" if len(set(y.tolist())) == 2 else "weighted"
                    metrics = {
                        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
                        "precision": round(float(precision_score(y_test, y_pred, average=avg, zero_division=0)), 4),
                        "recall": round(float(recall_score(y_test, y_pred, average=avg, zero_division=0)), 4),
                        "f1_score": round(float(f1_score(y_test, y_pred, average=avg, zero_division=0)), 4),
                        "task": "classification",
                    }
                else:
                    metrics = {
                        "mse": round(float(mean_squared_error(y_test, y_pred)), 6),
                        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 6),
                        "r2_score": round(float(r2_score(y_test, y_pred)), 4),
                        "task": "regression",
                    }

                if cross_validation > 0:
                    scoring = "accuracy" if is_classification else "r2"
                    cv_scores = cross_val_score(self._create_model(algorithm, hyperparameters), X_scaled, y, cv=cross_validation, scoring=scoring)
                    metrics["cv_scores"] = [round(float(s), 4) for s in cv_scores]
                    metrics["cv_mean"] = round(float(cv_scores.mean()), 4)
                    metrics["cv_std"] = round(float(cv_scores.std()), 4)
            else:
                # Unsupervised
                model.fit(X_scaled)
                if algorithm == "kmeans":
                    labels_pred = model.labels_
                    metrics = {
                        "silhouette_score": round(float(silhouette_score(X_scaled, labels_pred)), 4),
                        "inertia": round(float(model.inertia_), 4),
                        "n_clusters": int(hyperparameters.get("n_clusters", 3)),
                        "cluster_sizes": [int(s) for s in np.bincount(labels_pred)],
                        "task": "clustering",
                    }
                elif algorithm == "pca":
                    metrics = {
                        "explained_variance_ratio": [round(float(v), 4) for v in model.explained_variance_ratio_],
                        "cumulative_variance": [round(float(v), 4) for v in np.cumsum(model.explained_variance_ratio_)],
                        "n_components": int(model.n_components_),
                        "task": "dimensionality_reduction",
                    }

            # Store model
            _MODEL_STORE[model_id] = {"model": model, "scaler": scaler, "algorithm": algorithm, "metrics": metrics, "created_at": time.time()}

            elapsed = (time.perf_counter() - start) * 1000
            logger.info("ml_training_completed", model_id=model_id, algorithm=algorithm, elapsed_ms=elapsed)

            return {
                "model_id": model_id,
                "algorithm": algorithm,
                "metrics": metrics,
                "hyperparameters": hyperparameters,
                "training_samples": len(features),
                "features_count": X.shape[1],
                "execution_time_ms": round(elapsed, 2),
            }
        except Exception as e:
            logger.error("ml_training_error", error=str(e))
            return {"model_id": model_id, "algorithm": algorithm, "error": str(e)}

    async def predict(self, model_id: str, features: list[list[float]]) -> dict[str, Any]:
        if model_id not in _MODEL_STORE:
            return {"error": f"Model {model_id} not found"}

        entry = _MODEL_STORE[model_id]
        model = entry["model"]
        scaler = entry["scaler"]

        X = np.array(features)
        X_scaled = scaler.transform(X)
        predictions = model.predict(X_scaled)

        result: dict[str, Any] = {"model_id": model_id, "predictions": predictions.tolist()}

        if hasattr(model, "predict_proba"):
            try:
                probabilities = model.predict_proba(X_scaled)
                result["probabilities"] = probabilities.tolist()
            except Exception:
                pass

        return result

    async def list_models(self) -> list[dict[str, Any]]:
        return [
            {"model_id": mid, "algorithm": entry["algorithm"], "metrics": entry["metrics"], "created_at": entry["created_at"]}
            for mid, entry in _MODEL_STORE.items()
        ]

    def _create_model(self, algorithm: str, hyperparameters: dict[str, Any]) -> Any:
        from sklearn.linear_model import LinearRegression, LogisticRegression
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
        from sklearn.svm import SVC
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.neighbors import KNeighborsClassifier

        models = {
            "linear_regression": lambda: LinearRegression(**hyperparameters),
            "logistic_regression": lambda: LogisticRegression(max_iter=1000, **hyperparameters),
            "random_forest": lambda: RandomForestClassifier(n_estimators=hyperparameters.get("n_estimators", 100), random_state=42),
            "svm": lambda: SVC(probability=True, **{k: v for k, v in hyperparameters.items() if k != "probability"}),
            "kmeans": lambda: KMeans(n_clusters=hyperparameters.get("n_clusters", 3), random_state=42, n_init=10),
            "pca": lambda: PCA(n_components=hyperparameters.get("n_components", 2)),
            "gradient_boosting": lambda: GradientBoostingClassifier(n_estimators=hyperparameters.get("n_estimators", 100), random_state=42),
            "decision_tree": lambda: DecisionTreeClassifier(random_state=42, **hyperparameters),
            "knn": lambda: KNeighborsClassifier(n_neighbors=hyperparameters.get("n_neighbors", 5)),
        }
        return models[algorithm]()