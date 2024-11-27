CREATE TEMPORARY TABLE ebay AS (
SELECT
    *
FROM
    supplier_stock_ranked ps
LIMIT 5
);
