DROP TABLE IF EXISTS ebay;

CREATE TABLE ebay (
    item_id BIGINT,
    custom_label VARCHAR(255),
    quantity INT,
    quantity_delta INT,
    updated_date VARCHAR(255),
    ebay_store VARCHAR(255),
    supplier VARCHAR(255),
    last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) AS (
SELECT
    sd.ebay_store,
    rd.supplier,
    rd.custom_label,
    rd.quantity,
    COALESCE(
        MAX(CASE WHEN rn = 1 THEN rd.quantity END) -
        MAX(CASE WHEN rn = 2 THEN rd.quantity END),
        MAX(CASE WHEN rn = 1 THEN rd.quantity END)
    ) AS quantity_delta,
    MAX(rd.updated_date) AS updated_date,
    sd.item_id,
    NOW() AS last_updated_timestamp
FROM
    supplier_stock ps
LEFT JOIN
    store sd ON ps.custom_label = sd.custom_label
LEFT JOIN
    (
        SELECT
            ps.part_number,
            ps.supplier,
            ps.quantity,
            ps.updated_date,
            ps.custom_label,
            ROW_NUMBER() OVER (PARTITION BY ps.supplier, ps.custom_label ORDER BY ps.updated_date DESC) AS rn
        FROM
            supplier_stock ps
    ) rd ON ps.custom_label = rd.custom_label
GROUP BY
    sd.item_id, rd.supplier, sd.ebay_store, rd.quantity, rd.custom_label
);
