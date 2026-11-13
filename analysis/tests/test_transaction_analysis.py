from datetime import datetime

import polars as pl

from src.transaction_analysis import (
    build_customer_features,
    build_transaction_flags,
    segment_customers,
)


def sample_transactions() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "customer_id": ["a", "a", "b", "b", "c", "c"],
            "transaction_date": [datetime(2024, 1, i) for i in [1, 2, 1, 4, 1, 7]],
            "transaction_type": [51, 51, 20, 20, 51, 51],
            "transaction_subtype": [12, 12, 1, 1, 12, 12],
            "amount": [-10.0, -20.0, 100.0, -5.0, -11.0, -12.0],
            "movement_type": ["D", "D", "C", "D", "D", "D"],
            "description": ["gas", "gas", "salary", None, "gas", "gas"],
            "destination_bank": ["bank1", "bank1", None, None, "bank1", "bank1"],
        }
    )


def test_customer_features_have_expected_behavior():
    features = build_customer_features(sample_transactions(), as_of=datetime(2024, 1, 10))
    customer_a = features.filter(pl.col("customer_id") == "a").row(0, named=True)
    assert customer_a["transaction_count"] == 2
    assert customer_a["debit_share"] == 1.0
    assert customer_a["recency_days"] == 8


def test_transaction_flags_are_explainable():
    flagged = build_transaction_flags(sample_transactions(), z_threshold=0)
    assert flagged["reason_code"].drop_nulls().to_list()


def test_segmentation_returns_customer_assignments():
    features = build_customer_features(sample_transactions())
    columns = ["transaction_count", "gross_amount", "debit_share", "transaction_type_count"]
    assignments, metadata = segment_customers(features, columns, n_clusters=2)
    assert assignments.height == 3
    assert metadata["profiles"].height == 2
