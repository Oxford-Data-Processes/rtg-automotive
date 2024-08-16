SELECT * 
FROM rtg_automotive.supplier_stock_history 
WHERE product_id = (
    SELECT product_id 
    FROM rtg_automotive.product 
    WHERE custom_label = (
        SELECT custom_label 
        FROM rtg_automotive.store 
        WHERE item_id = 'item_id_from_ebay'
        LIMIT 1
    )
);
