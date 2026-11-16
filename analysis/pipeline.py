"""Reproducible, source-independent pipeline for synthetic transaction analysis.

The functions operate on a transaction table with the canonical schema.  A
future SQL Server adapter only needs to return the same columns as
``load_transactions``; the analytical stages do not depend on the source.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import polars as pl
from sklearn.cluster import (
    AgglomerativeClustering,
    DBSCAN,
    KMeans,
    MiniBatchKMeans,
)
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PowerTransformer, RobustScaler, StandardScaler

TRANSACTION_COLUMNS = [
    "codigo_cliente",
    "fecha_transaccion",
    "tipo_transaccion",
    "subtipo_transaccion",
    "monto",
    "tipo_movimiento",
    "glosa",
    "banco_destino",
]


def load_transactions(path: str | Path) -> pl.DataFrame:
    """Read the canonical CSV without modifying the source file."""
    return pl.read_csv(
        path,
        try_parse_dates=True,
        schema_overrides={
            "codigo_cliente": pl.Int64,
            "tipo_transaccion": pl.Int64,
            "subtipo_transaccion": pl.Int64,
            "monto": pl.Float64,
        },
        null_values=[""],
    )


def load_catalogs(types_path: str | Path, banks_path: str | Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Read both interpretation catalogs."""
    return (
        pl.read_csv(types_path, schema_overrides={"tipo_transaccion": pl.Int64, "subtipo_transaccion": pl.Int64}),
        pl.read_csv(banks_path),
    )


def validate_transactions(
    transactions: pl.DataFrame,
    types: pl.DataFrame,
    banks: pl.DataFrame,
) -> dict[str, object]:
    """Return explicit quality checks; raise only for an invalid schema."""
    missing = sorted(set(TRANSACTION_COLUMNS) - set(transactions.columns))
    if missing:
        raise ValueError(f"Missing transaction columns: {missing}")
    expected_types = set(types["tipo_transaccion"].unique().to_list())
    observed_types = set(transactions["tipo_transaccion"].unique().to_list())
    catalog_pairs = types.select(["tipo_transaccion", "subtipo_transaccion"])
    duplicate_catalog_pairs = types.height - types.unique(
        ["tipo_transaccion", "subtipo_transaccion"]
    ).height
    invalid_pairs = transactions.join(
        catalog_pairs.unique(),
        on=["tipo_transaccion", "subtipo_transaccion"],
        how="anti",
    ).height
    sign_mismatches = transactions.filter(
        ((pl.col("tipo_movimiento") == "D") & (pl.col("monto") >= 0))
        | ((pl.col("tipo_movimiento") == "C") & (pl.col("monto") < 0))
        | (~pl.col("tipo_movimiento").is_in(["D", "C"]))
    ).height
    return {
        "rows": transactions.height,
        "unique_clients": transactions["codigo_cliente"].n_unique(),
        "observed_transaction_types": len(observed_types),
        "catalog_transaction_types": len(expected_types),
        "missing_transaction_types": sorted(expected_types - observed_types),
        "catalog_duplicate_pairs": duplicate_catalog_pairs,
        "missing_values": {c: transactions[c].null_count() for c in TRANSACTION_COLUMNS},
        "duplicate_rows": transactions.height - transactions.unique().height,
        "invalid_catalog_pairs": invalid_pairs,
        "sign_mismatches": sign_mismatches,
        "invalid_dates": transactions["fecha_transaccion"].is_null().sum(),
        "date_min": transactions["fecha_transaccion"].min(),
        "date_max": transactions["fecha_transaccion"].max(),
    }


def _share_hhi(values: pl.Expr, total: pl.Expr) -> pl.Expr:
    return ((values / total).pow(2)).sum()


def _entropy(values: pl.Expr, total: pl.Expr) -> pl.Expr:
    share = values / total
    return (-(share * share.log())).sum()


def build_customer_features(transactions: pl.DataFrame) -> pl.DataFrame:
    """Aggregate transaction records into interpretable customer features."""
    if transactions.schema["fecha_transaccion"] == pl.String:
        transactions = transactions.with_columns(
            pl.col("fecha_transaccion").str.to_datetime(strict=True)
        )
    base = transactions.with_columns(
        pl.when(pl.col("monto") < 0).then(-pl.col("monto")).otherwise(0).alias("debit_abs"),
        pl.when(pl.col("monto") >= 0).then(pl.col("monto")).otherwise(0).alias("credit_abs"),
        pl.col("fecha_transaccion").dt.month().alias("month"),
    )
    totals = base.group_by("codigo_cliente").agg(
        pl.len().alias("transaction_count"),
        pl.col("debit_abs").sum().alias("debit_total"),
        pl.col("credit_abs").sum().alias("credit_total"),
        pl.col("monto").sum().alias("net_amount"),
        pl.col("monto").mean().alias("amount_mean"),
        pl.col("monto").median().alias("amount_median"),
        pl.col("monto").std().fill_null(0).alias("amount_std"),
        pl.col("monto").quantile(0.25).alias("amount_p25"),
        pl.col("monto").quantile(0.75).alias("amount_p75"),
        (pl.col("tipo_movimiento") == "D").mean().alias("debit_ratio"),
        (pl.col("tipo_movimiento") == "C").mean().alias("credit_ratio"),
        pl.col("tipo_transaccion").n_unique().alias("transaction_type_count"),
        pl.col("subtipo_transaccion").n_unique().alias("subtype_count"),
        pl.col("banco_destino").drop_nulls().n_unique().alias("bank_count"),
    )
    by_type = base.group_by(["codigo_cliente", "tipo_transaccion"]).agg(
        pl.len().alias("n"),
        pl.col("debit_abs").sum().alias("debit_amount"),
        pl.col("credit_abs").sum().alias("credit_amount"),
    )
    type_stats = by_type.group_by("codigo_cliente").agg(
        _share_hhi(pl.col("n"), pl.col("n").sum()).alias("type_hhi"),
        _entropy(pl.col("n"), pl.col("n").sum()).alias("type_entropy"),
        _share_hhi(pl.col("debit_amount"), pl.col("debit_amount").sum()).alias(
            "debit_type_hhi"
        ),
        _share_hhi(pl.col("credit_amount"), pl.col("credit_amount").sum()).alias(
            "credit_type_hhi"
        ),
    )
    by_subtype = base.group_by(["codigo_cliente", "subtipo_transaccion"]).agg(
        pl.len().alias("n"),
        pl.col("debit_abs").sum().alias("debit_amount"),
        pl.col("credit_abs").sum().alias("credit_amount"),
    )
    subtype_stats = by_subtype.group_by("codigo_cliente").agg(
        _share_hhi(pl.col("n"), pl.col("n").sum()).alias("subtype_hhi"),
        _entropy(pl.col("n"), pl.col("n").sum()).alias("subtype_entropy"),
        _share_hhi(pl.col("debit_amount"), pl.col("debit_amount").sum()).alias(
            "debit_subtype_hhi"
        ),
        _share_hhi(pl.col("credit_amount"), pl.col("credit_amount").sum()).alias(
            "credit_subtype_hhi"
        ),
    )
    return (
        totals.join(type_stats, on="codigo_cliente", how="left")
        .join(subtype_stats, on="codigo_cliente", how="left")
        .with_columns(
            (pl.col("debit_total") + pl.col("credit_total")).alias("gross_amount"),
            (pl.col("amount_p75") - pl.col("amount_p25")).alias("amount_iqr"),
            (pl.col("type_entropy") / np.log(57)).alias("type_entropy_normalized"),
            (pl.col("subtype_entropy") / np.log(57)).alias(
                "subtype_entropy_normalized"
            ),
        )
        .sort("codigo_cliente")
    )


def make_preprocessor(
    features: pl.DataFrame,
    scaler: str = "robust",
) -> tuple[Pipeline, list[str]]:
    """Create a numeric-only, imputed and scaled preprocessing pipeline."""
    columns = [c for c in features.columns if c != "codigo_cliente"]
    if scaler == "standard":
        scale = StandardScaler()
    elif scaler == "power":
        scale = PowerTransformer()
    elif scaler == "robust":
        scale = RobustScaler()
    else:
        raise ValueError("scaler must be one of: standard, robust, power")
    return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", scale)]), columns


def transform_features(features: pl.DataFrame, scaler: str = "robust") -> tuple[np.ndarray, list[str]]:
    preprocessor, columns = make_preprocessor(features, scaler)
    return preprocessor.fit_transform(features.select(columns).to_numpy()), columns


def detect_anomalies(matrix: np.ndarray, contamination: float = 0.02, random_state: int = 20261116) -> np.ndarray:
    """Return Isolation Forest labels (1 normal, -1 anomaly) without deletion."""
    return IsolationForest(contamination=contamination, random_state=random_state, n_jobs=-1).fit_predict(matrix)


def run_clustering(matrix: np.ndarray, algorithm: str, n_clusters: int = 4, random_state: int = 20261116) -> np.ndarray:
    """Fit one configured clustering algorithm and return labels."""
    models = {
        "kmeans": KMeans(n_clusters=n_clusters, n_init=20, random_state=random_state),
        "minibatch_kmeans": MiniBatchKMeans(n_clusters=n_clusters, n_init=10, random_state=random_state),
        "gmm": GaussianMixture(n_components=n_clusters, random_state=random_state),
        "agglomerative": AgglomerativeClustering(n_clusters=n_clusters),
        "dbscan": DBSCAN(eps=0.8, min_samples=10),
    }
    try:
        from hdbscan import HDBSCAN
    except ImportError:
        HDBSCAN = None
    if HDBSCAN is not None:
        models["hdbscan"] = HDBSCAN(min_cluster_size=25)
    if algorithm not in models:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    model = models[algorithm]
    return model.fit_predict(matrix)


def evaluate_labels(matrix: np.ndarray, labels: Iterable[int]) -> dict[str, float | int]:
    """Compute clustering metrics, excluding noise for density methods."""
    labels = np.asarray(list(labels))
    mask = labels != -1
    unique = np.unique(labels[mask])
    result: dict[str, float | int] = {
        "clusters": int(len(unique)),
        "noise_count": int((~mask).sum()),
        "assigned_count": int(mask.sum()),
    }
    if len(unique) < 2 or mask.sum() <= len(unique):
        result.update({"silhouette": float("nan"), "davies_bouldin": float("nan"), "calinski_harabasz": float("nan")})
        return result
    result.update(
        {
            "silhouette": float(silhouette_score(matrix[mask], labels[mask])),
            "davies_bouldin": float(davies_bouldin_score(matrix[mask], labels[mask])),
            "calinski_harabasz": float(calinski_harabasz_score(matrix[mask], labels[mask])),
        }
    )
    return result


def reduce_for_visualization(matrix: np.ndarray, random_state: int = 20261116) -> np.ndarray:
    """Produce a deterministic two-dimensional PCA view, not a clustering input."""
    return PCA(n_components=2, random_state=random_state).fit_transform(matrix)


def profile_clusters(features: pl.DataFrame, labels: Iterable[int]) -> pl.DataFrame:
    """Attach labels and summarize interpretable features per cluster."""
    labeled = features.with_columns(pl.Series("cluster", list(labels)))
    return labeled.group_by("cluster").agg(
        pl.len().alias("customers"),
        (pl.len() / features.height).alias("customer_share"),
        *[pl.col(c).mean().alias(f"{c}_mean") for c in features.columns if c != "codigo_cliente"],
    ).sort("cluster")


def save_table(table: pl.DataFrame, path: str | Path) -> None:
    """Persist an analytical artifact, creating only the requested directory."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    table.write_csv(destination)
