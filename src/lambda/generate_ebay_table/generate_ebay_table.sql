SELECT 
    sd.ebay_store,
    rd.custom_label,
    rd.quantity,
    COALESCE(MAX(CASE WHEN rd.row_number = 1 THEN rd.quantity END) - MAX(CASE WHEN rd.row_number = 2 THEN rd.quantity END), MAX(CASE WHEN rd.row_number = 1 THEN rd.quantity END)) AS quantity_delta,
    MAX(rd.updated_date) AS updated_date,
    sd.item_id
FROM 
    (
        SELECT 
            ps.part_number,
            ps.quantity,
            ps.updated_date,
            p.custom_label,
            ROW_NUMBER() OVER (PARTITION BY p.custom_label ORDER BY ps.updated_date DESC) AS row_number
        FROM 
            "rtg_automotive"."supplier_stock" ps
        LEFT JOIN 
            "rtg_automotive"."product" p ON ps.part_number = p.part_number
    ) rd
LEFT JOIN 
    (
        SELECT custom_label, item_id, supplier, ebay_store 
        FROM "rtg_automotive"."store"
    ) sd ON rd.custom_label = sd.custom_label
GROUP BY 
    sd.item_id, sd.ebay_store, rd.quantity, rd.custom_label;