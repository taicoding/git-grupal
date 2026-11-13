# Transactional Behavior Pattern Analysis

This pipeline identifies recurring customer transaction behavior, meaningful
behavioral segments, and unusual activity. It is designed to work with a SQL
Server transaction table while keeping credentials and customer data outside
the repository.

## Methodology

1. **SQL Server aggregation** reduces the raw transaction table to a portable
   transaction-level extract and a customer-period summary. The query preserves
   signed amounts, movement type, transaction type/subtype, description, and
   destination bank.
2. **EDA and quality checks** profile volume, nulls, signs, duplicate records,
   date coverage, transaction-code distributions, concentration, and customer
   activity.
3. **Feature engineering** creates robust customer features: frequency,
   monetary value, debit/credit mix, channel/category diversity, recurrence,
   destination-bank concentration, description richness, and activity
   recency. Features are computed without leaking a future observation into a
   customer's score.
4. **Segmentation** standardizes numeric features and uses K-Means over a
   small, interpretable range of `k` values. Silhouette score and an elbow
   curve guide model selection; the final cluster profile is translated into
   business labels.
5. **Anomaly detection** uses a robust, explainable customer-level score
   (median/MAD) and optional Isolation Forest. A transaction-level rules layer
   flags extreme amounts, unusual destination banks, and unusual activity
   timing. Flags are leads for review, not proof of fraud.
6. **Evaluation and action** checks stability across random seeds/time windows,
   cluster size, feature distributions, and false-positive review samples.

The expected output is a customer feature table, segment assignment/profile,
ranked anomaly candidates with reason codes, and interactive Plotly charts.
The pipeline intentionally does not hard-code transaction code meanings:
provide a mapping table when business labels for type/subtype are available.

## Layout

```text
analysis/
├── notebooks/
│   ├── 01_eda_and_quality.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_segmentation_and_anomalies.ipynb
│   └── 04_evaluation_and_reporting.ipynb
├── sql/01_customer_aggregation.sql
├── src/transaction_analysis.py
├── tests/test_transaction_analysis.py
├── requirements.txt
└── README.md
```

## Quick start

```bash
python -m pip install -r analysis/requirements.txt
jupyter lab analysis/notebooks/01_eda_and_quality.ipynb
```

Set `SQL_SERVER`, `SQL_DATABASE`, `SQL_DRIVER`, and optionally
`SQL_TRUSTED_CONNECTION` or `SQL_USERNAME`/`SQL_PASSWORD` in the notebook
environment. `mssql_python` is used by `load_sql_server`; it supports the
Microsoft Entra/ODBC connection strings supported by the installed driver.
Do not commit credentials.

Every notebook supports a `DATA_PATH` pointing to a Parquet or CSV extract.
This makes development and review reproducible without requiring access to
production SQL Server. The expected canonical columns are:

`customer_id`, `transaction_date`, `transaction_type`, `transaction_subtype`,
`amount`, `movement_type`, `description`, `destination_bank`.

An optional `transaction_id` is used for duplicate checks. Rename columns in
the SQL query or in the notebook's `COLUMN_MAP` if the source uses different
names.

## Reproducibility and interpretation

Use a fixed `random_state`, record the extraction timestamp, and save the
feature/assignment tables as Parquet. Re-run the evaluation notebook after
the first business review. Clusters describe observed behavior during the
analysis window; they are not immutable customer traits. Amount thresholds,
minimum activity thresholds, and anomaly candidates must be calibrated with
domain experts.
