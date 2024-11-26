CREATE TEMPORARY TABLE ebay AS (
SELECT
    ts.item_id,
    ps.custom_label,
    ps.quantity,
    ps.quantity_delta,
    ts.ebay_store,
    ps.supplier
FROM
    supplier_stock_ranked ps
LEFT JOIN
    store_filtered ts ON ps.custom_label = ts.custom_label
);
