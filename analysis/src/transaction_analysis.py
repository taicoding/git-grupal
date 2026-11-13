"""Reusable, data-source-agnostic transaction analysis functions.

The functions use Polars for tabular work. Model fitting converts only the
small customer feature matrix to NumPy, keeping raw transaction data in Polars.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any

import polars as pl
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

REQUIRED_COLUMNS = {
    "customer_id",
    "transaction_date",
    "transaction_type",
    "transaction_subtype",
    "amount",
    "movement_type",
    "description",
    "destination_bank",
}


def load_extract(path: str | Path) -> pl.DataFrame:
    """Load a CSV or Parquet extract and normalize its date column."""
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        frame = pl.read_parquet(path)
    elif path.suffix.lower() in {".csv", ".txt"}:
        frame = pl.read_csv(path, try_parse_dates=True)
    else:
        raise ValueError(f"Unsupported extract format: {path.suffix}")
    return normalize_transactions(frame)


def load_sql_server(
    query: str,
    *,
    connection_string: str,
    parameters: Sequence[Any] | Mapping[str, Any] | None = None,
) -> pl.DataFrame:
    """Execute a parameterized query with mssql_python and return Polars data.

    The import is local so EDA and tests can run against extracts without the
    SQL Server driver installed.
    """
    try:
        import mssql_python
    except ImportError as exc:
        raise ImportError(
            "Install mssql-python to load SQL Server data, or use load_extract."
        ) from exc

    with mssql_python.connect(connection_string) as connection:
        cursor = connection.cursor()
        cursor.execute(query, parameters or ())
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
    return normalize_transactions(pl.DataFrame(rows, schema=columns, orient="row"))


def normalize_transactions(frame: pl.DataFrame) -> pl.DataFrame:
    """Validate canonical columns and normalize types/categorical whitespace."""
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return frame.with_columns(
        pl.col("transaction_date").cast(pl.Datetime, strict=False),
        pl.col("amount").cast(pl.Float64, strict=False),
        pl.col("movement_type")
        .cast(pl.String)
        .str.strip_chars()
        .str.to_uppercase(),
        pl.col("description").cast(pl.String, strict=False).str.strip_chars(),
        pl.col("destination_bank").cast(pl.String, strict=False).str.strip_chars(),
    )


def profile_transactions(frame: pl.DataFrame) -> dict[str, Any]:
    """Return compact quality and coverage metrics suitable for EDA."""
    frame = normalize_transactions(frame)
    duplicate_columns = [c for c in ("transaction_id",) if c in frame.columns]
    duplicate_count = (
        frame.height - frame.unique(subset=duplicate_columns).height
        if duplicate_columns
        else None
    )
    return {
        "rows": frame.height,
        "customers": frame["customer_id"].n_unique(),
        "date_min": frame["transaction_date"].min(),
        "date_max": frame["transaction_date"].max(),
        "null_counts": {
            column: frame[column].null_count() for column in frame.columns
        },
        "invalid_movement_types": frame.filter(
            ~pl.col("movement_type").is_in(["D", "C"])
        ).height,
        "negative_amounts": frame.filter(pl.col("amount") < 0).height,
        "duplicate_count": duplicate_count,
    }


def build_customer_features(frame: pl.DataFrame, as_of: date | datetime | None = None) -> pl.DataFrame:
    """Create one interpretable behavioral row per customer."""
    frame = normalize_transactions(frame).with_columns(
        pl.col("transaction_date").dt.date().alias("_date"),
        pl.col("amount").abs().alias("_abs_amount"),
        (pl.col("movement_type") == "D").cast(pl.Int8).alias("_is_debit"),
        (pl.col("movement_type") == "C").cast(pl.Int8).alias("_is_credit"),
    )
    if frame.height == 0:
        return pl.DataFrame({"customer_id": []})
    cutoff = as_of or frame["_date"].max()
    if isinstance(cutoff, datetime):
        cutoff = cutoff.date()
    return (
        frame.group_by("customer_id")
        .agg(
            pl.len().alias("transaction_count"),
            pl.col("_date").min().alias("first_transaction_date"),
            pl.col("_date").max().alias("last_transaction_date"),
            pl.col("_abs_amount").sum().alias("gross_amount"),
            pl.col("amount").sum().alias("net_amount"),
            pl.col("_abs_amount").mean().alias("mean_transaction_amount"),
            pl.col("_abs_amount").median().alias("median_transaction_amount"),
            pl.col("_is_debit").sum().alias("debit_count"),
            pl.col("_is_credit").sum().alias("credit_count"),
            pl.col("transaction_type").n_unique().alias("transaction_type_count"),
            pl.col("transaction_subtype").n_unique().alias("transaction_subtype_count"),
            pl.col("destination_bank").drop_nulls().n_unique().alias("destination_bank_count"),
            pl.col("description").drop_nulls().n_unique().alias("description_count"),
        )
        .with_columns(
            (pl.col("debit_count") / pl.col("transaction_count")).alias("debit_share"),
            (pl.col("credit_count") / pl.col("transaction_count")).alias("credit_share"),
            (pl.col("gross_amount") / pl.col("transaction_count")).alias("amount_per_transaction"),
            (pl.lit(cutoff) - pl.col("last_transaction_date")).dt.total_days().alias("recency_days"),
            (pl.col("last_transaction_date") - pl.col("first_transaction_date"))
            .dt.total_days()
            .alias("active_days"),
        )
        .with_columns(
            pl.when(pl.col("active_days") > 0)
            .then(pl.col("transaction_count") / pl.col("active_days"))
            .otherwise(pl.col("transaction_count"))
            .alias("transactions_per_active_day"),
        )
    )


def build_transaction_flags(frame: pl.DataFrame, z_threshold: float = 6.0) -> pl.DataFrame:
    """Flag explainable transaction-level outliers using median/MAD."""
    frame = normalize_transactions(frame)
    median = frame["amount"].abs().median()
    mad = (frame["amount"].abs() - median).abs().median()
    scale = 1.4826 * mad if mad and mad > 0 else max(abs(median or 0), 1.0)
    return frame.with_columns(
        (((pl.col("amount").abs() - median) / scale).abs()).alias("robust_amount_score")
    ).with_columns(
        (pl.col("robust_amount_score") >= z_threshold).alias("is_amount_anomaly"),
        pl.when(pl.col("robust_amount_score") >= z_threshold)
        .then(pl.lit("extreme_amount"))
        .otherwise(pl.lit(None, dtype=pl.String))
        .alias("reason_code"),
    )


def choose_k(features: pl.DataFrame, feature_columns: Sequence[str], k_values: Sequence[int] = range(2, 7), random_state: int = 42) -> pl.DataFrame:
    """Score candidate cluster counts with inertia and silhouette."""
    matrix = StandardScaler().fit_transform(features.select(feature_columns).fill_null(0).to_numpy())
    results = []
    for k in k_values:
        if k >= len(features):
            continue
        model = KMeans(n_clusters=k, n_init=20, random_state=random_state)
        labels = model.fit_predict(matrix)
        results.append({"k": k, "inertia": float(model.inertia_), "silhouette": float(silhouette_score(matrix, labels))})
    return pl.DataFrame(results)


def segment_customers(
    features: pl.DataFrame,
    feature_columns: Sequence[str],
    n_clusters: int,
    random_state: int = 42,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Fit a reproducible K-Means model and return assignments and profiles."""
    if n_clusters < 2 or n_clusters >= features.height:
        raise ValueError("n_clusters must be >= 2 and smaller than customer count")
    matrix = StandardScaler().fit_transform(features.select(feature_columns).fill_null(0).to_numpy())
    model = KMeans(n_clusters=n_clusters, n_init=20, random_state=random_state)
    labels = model.fit_predict(matrix)
    assignments = features.select("customer_id").with_columns(pl.Series("segment", labels))
    profile = assignments.join(features, on="customer_id").group_by("segment").agg(
        pl.len().alias("customers"),
        *[pl.col(column).mean().alias(column) for column in feature_columns],
    ).sort("segment")
    return assignments, {"model": model, "profiles": profile, "silhouette": silhouette_score(matrix, labels)}


def detect_customer_anomalies(features: pl.DataFrame, feature_columns: Sequence[str], contamination: float = 0.02, random_state: int = 42) -> pl.DataFrame:
    """Rank unusual customer feature combinations with Isolation Forest."""
    if not 0 < contamination < 0.5:
        raise ValueError("contamination must be between 0 and 0.5")
    matrix = StandardScaler().fit_transform(features.select(feature_columns).fill_null(0).to_numpy())
    model = IsolationForest(contamination=contamination, random_state=random_state)
    return features.with_columns(
        pl.Series("anomaly_label", model.fit_predict(matrix)),
        pl.Series("anomaly_score", -model.score_samples(matrix)),
    ).sort("anomaly_score", descending=True)
