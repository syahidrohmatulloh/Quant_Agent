
import numpy as np
import pandas as pd
from typing import Optional

class HRPAllocator:
    """Simplified Hierarchical Risk Parity.
    If scipy is unavailable, uses simple quasi-diagonalization."""
    def __init__(self):
        pass

    def allocate(self, cov: pd.DataFrame, corr: Optional[pd.DataFrame] = None) -> pd.Series:
        if corr is None:
            corr = cov.corr()
        # Distance matrix
        dist = np.sqrt(0.5 * (1 - corr))
        # Simple linkage via single-linkage on distance
        # If scipy unavailable, use a simple ordering heuristic
        try:
            from scipy.cluster.hierarchy import linkage, leaves_list
            from scipy.spatial.distance import squareform
            condensed = squareform(dist.values, checks=False)
            link = linkage(condensed, method="single")
            order = leaves_list(link)
        except Exception:
            # Fallback: sort by sum of distances
            order = np.argsort(dist.sum(axis=1).values)
        # Recursive bisection allocation
        w = pd.Series(1.0, index=cov.index)
        clusters = [list(cov.index[order])]
        while clusters:
            new_clusters = []
            for cluster in clusters:
                if len(cluster) == 1:
                    continue
                mid = len(cluster) // 2
                left = cluster[:mid]
                right = cluster[mid:]
                left_var = self._cluster_var(cov, left)
                right_var = self._cluster_var(cov, right)
                alpha = 1 - left_var / (left_var + right_var) if (left_var + right_var) > 0 else 0.5
                w[left] *= alpha
                w[right] *= (1 - alpha)
                new_clusters.extend([left, right])
            clusters = [c for c in new_clusters if len(c) > 1]
        w = w / w.sum()
        return w

    def _cluster_var(self, cov: pd.DataFrame, cluster: list) -> float:
        sub = cov.loc[cluster, cluster]
        w = np.ones(len(cluster)) / len(cluster)
        return float(w @ sub.values @ w)
