"""Clustering Analysis Engine.

Groups similar data points to discover latent patterns, topics, or
categories. Supports K-Means, DBSCAN, and hierarchical clustering
with automatic parameter tuning.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ClusteringEngine:
    """Performs clustering analysis on vector collections.

    Algorithms:
    - K-Means: Centroid-based partitioning with elbow detection.
    - DBSCAN: Density-based spatial clustering for arbitrary shapes.
    - Hierarchical: Agglomerative clustering with dendrogram support.
    """

    def cluster(
        self,
        vectors: list[list[float]],
        ids: list[str],
        algorithm: str = "kmeans",
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute clustering on a set of vectors.

        Args:
            vectors: List of embedding vectors.
            ids: Corresponding identifiers.
            algorithm: One of kmeans, dbscan, hierarchical.
            params: Algorithm-specific parameters.

        Returns:
            Dict with clusters, metadata, and quality metrics.
        """
        start = time.perf_counter()
        params = params or {}
        matrix = np.array(vectors, dtype=np.float32)

        if algorithm == "kmeans":
            labels, centroids, inertia = self._kmeans(matrix, params)
        elif algorithm == "dbscan":
            labels, centroids, inertia = self._dbscan(matrix, params)
        elif algorithm == "hierarchical":
            labels, centroids, inertia = self._hierarchical(matrix, params)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        clusters = self._build_cluster_output(labels, ids, matrix, centroids)
        quality = self._compute_quality_metrics(matrix, labels)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "clusters": clusters,
            "metadata": {
                "algorithm": algorithm,
                "params": params,
                "total_points": len(vectors),
                "num_clusters": len(clusters),
                "inertia": round(float(inertia), 4) if inertia is not None else None,
                "query_time_ms": round(elapsed_ms, 2),
                **quality,
            },
        }

    def auto_cluster(
        self,
        vectors: list[list[float]],
        ids: list[str],
        max_k: int = 20,
    ) -> dict[str, Any]:
        """Automatically determine optimal cluster count via elbow method.

        Args:
            vectors: List of embedding vectors.
            ids: Corresponding identifiers.
            max_k: Maximum number of clusters to evaluate.

        Returns:
            Clustering result with optimal k.
        """
        matrix = np.array(vectors, dtype=np.float32)
        n = matrix.shape[0]
        max_k = min(max_k, n)

        if n <= 2:
            return self.cluster(vectors, ids, "kmeans", {"n_clusters": 1})

        inertias = []
        for k in range(2, max_k + 1):
            _, _, inertia = self._kmeans(matrix, {"n_clusters": k})
            inertias.append((k, float(inertia)))

        optimal_k = self._find_elbow(inertias)
        logger.info("Auto-cluster: optimal k=%d (evaluated 2..%d)", optimal_k, max_k)

        return self.cluster(vectors, ids, "kmeans", {"n_clusters": optimal_k})

    @staticmethod
    def _kmeans(matrix: np.ndarray, params: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, float]:
        """K-Means clustering."""
        from sklearn.cluster import KMeans

        n_clusters = params.get("n_clusters", 5)
        max_iter = params.get("max_iter", 300)
        n_clusters = min(n_clusters, matrix.shape[0])

        model = KMeans(n_clusters=n_clusters, max_iter=max_iter, n_init=10, random_state=42)
        labels = model.fit_predict(matrix)
        return labels, model.cluster_centers_, model.inertia_

    @staticmethod
    def _dbscan(matrix: np.ndarray, params: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, float | None]:
        """DBSCAN density-based clustering."""
        from sklearn.cluster import DBSCAN

        eps = params.get("eps", 0.5)
        min_samples = params.get("min_samples", 5)

        model = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
        labels = model.fit_predict(matrix)

        unique_labels = set(labels) - {-1}
        centroids = np.array([
            matrix[labels == lbl].mean(axis=0) for lbl in sorted(unique_labels)
        ]) if unique_labels else np.empty((0, matrix.shape[1]))

        return labels, centroids, None

    @staticmethod
    def _hierarchical(matrix: np.ndarray, params: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, float | None]:
        """Agglomerative hierarchical clustering."""
        from sklearn.cluster import AgglomerativeClustering

        n_clusters = params.get("n_clusters", 5)
        linkage = params.get("linkage", "ward")
        n_clusters = min(n_clusters, matrix.shape[0])

        model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        labels = model.fit_predict(matrix)

        unique_labels = sorted(set(labels))
        centroids = np.array([matrix[labels == lbl].mean(axis=0) for lbl in unique_labels])

        return labels, centroids, None

    @staticmethod
    def _build_cluster_output(
        labels: np.ndarray,
        ids: list[str],
        matrix: np.ndarray,
        centroids: np.ndarray,
    ) -> list[dict[str, Any]]:
        """Build structured cluster output."""
        clusters: dict[int, list[str]] = {}
        for idx, label in enumerate(labels):
            label_int = int(label)
            if label_int not in clusters:
                clusters[label_int] = []
            clusters[label_int].append(ids[idx])

        result = []
        for cluster_id in sorted(clusters.keys()):
            members = clusters[cluster_id]
            entry: dict[str, Any] = {
                "cluster_id": cluster_id,
                "members": members,
                "size": len(members),
            }
            if cluster_id >= 0 and cluster_id < len(centroids):
                entry["centroid"] = centroids[cluster_id].tolist()

            member_indices = [i for i, lbl in enumerate(labels) if int(lbl) == cluster_id]
            if len(member_indices) > 1:
                member_vecs = matrix[member_indices]
                centroid = member_vecs.mean(axis=0)
                dists = np.linalg.norm(member_vecs - centroid, axis=1)
                entry["density"] = round(1.0 / (1.0 + float(dists.mean())), 6)

            result.append(entry)

        return result

    @staticmethod
    def _compute_quality_metrics(matrix: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
        """Compute clustering quality metrics."""
        unique = set(labels)
        unique.discard(-1)

        if len(unique) < 2 or len(unique) >= matrix.shape[0]:
            return {"silhouette_score": None}

        try:
            from sklearn.metrics import silhouette_score
            score = silhouette_score(matrix, labels, metric="cosine", sample_size=min(5000, matrix.shape[0]))
            return {"silhouette_score": round(float(score), 4)}
        except Exception:
            return {"silhouette_score": None}

    @staticmethod
    def _find_elbow(inertias: list[tuple[int, float]]) -> int:
        """Find elbow point using maximum curvature method."""
        if len(inertias) < 3:
            return inertias[0][0] if inertias else 2

        ks = np.array([x[0] for x in inertias], dtype=np.float64)
        vals = np.array([x[1] for x in inertias], dtype=np.float64)

        p1 = np.array([ks[0], vals[0]])
        p2 = np.array([ks[-1], vals[-1]])
        line_vec = p2 - p1
        line_len = np.linalg.norm(line_vec) + 1e-10
        line_unit = line_vec / line_len

        max_dist = -1.0
        best_k = int(ks[0])

        for i in range(len(ks)):
            point = np.array([ks[i], vals[i]])
            proj = np.dot(point - p1, line_unit)
            proj_point = p1 + proj * line_unit
            dist = np.linalg.norm(point - proj_point)
            if dist > max_dist:
                max_dist = dist
                best_k = int(ks[i])

        return best_k