WITH store_data AS (
    SELECT custom_label, item_id, supplier, ebay_store 
    FROM "rtg_automotive"."store"
),
ranked_data AS (
    SELECT 
        custom_label,
        quantity,
        updated_date,
        ROW_NUMBER() OVER (PARTITION BY custom_label ORDER BY updated_date DESC) AS row_number
    FROM 
        "rtg_automotive"."supplier_stock"
)
SELECT 
    sd.ebay_store,
    rd.custom_label,
    COALESCE(MAX(CASE WHEN rd.row_number = 1 THEN rd.quantity END) - MAX(CASE WHEN rd.row_number = 2 THEN rd.quantity END), MAX(CASE WHEN rd.row_number = 1 THEN rd.quantity END)) AS quantity_delta,
    MAX(rd.updated_date) AS updated_date,
    sd.item_id
FROM 
    ranked_data rd
LEFT JOIN 
    store_data sd ON rd.custom_label = sd.custom_label
GROUP BY 
    rd.custom_label, sd.item_id, sd.ebay_store;