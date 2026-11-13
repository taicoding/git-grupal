-- Replace dbo.transactions and the source column names if necessary.
-- Parameters are intentionally left to the notebook/driver.
SELECT
    customer_id,
    transaction_date,
    transaction_id,
    transaction_type,
    transaction_subtype,
    CAST(amount AS decimal(19, 4)) AS amount,
    movement_type,
    NULLIF(LTRIM(RTRIM(description)), '') AS description,
    NULLIF(LTRIM(RTRIM(destination_bank)), '') AS destination_bank
FROM dbo.transactions
WHERE transaction_date >= :start_date
  AND transaction_date < :end_date;

-- A compact customer-period summary for large extracts. Use this query when
-- transaction-level analysis is not required downstream.
-- SELECT customer_id, DATEFROMPARTS(YEAR(transaction_date), MONTH(transaction_date), 1) AS period,
--        COUNT_BIG(*) AS transaction_count,
--        SUM(CASE WHEN movement_type = 'D' THEN 1 ELSE 0 END) AS debit_count,
--        SUM(CASE WHEN movement_type = 'C' THEN 1 ELSE 0 END) AS credit_count,
--        SUM(amount) AS net_amount, SUM(ABS(amount)) AS gross_amount
-- FROM dbo.transactions
-- WHERE transaction_date >= :start_date AND transaction_date < :end_date
-- GROUP BY customer_id, DATEFROMPARTS(YEAR(transaction_date), MONTH(transaction_date), 1);
