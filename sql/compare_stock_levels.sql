SELECT p.*, s.*
FROM rtg_automotive.product p
LEFT JOIN rtg_automotive.store s
    ON s.custom_label = p.custom_label
LEFT JOIN (
    -- Subquery to get product_id with a non-zero quantity difference between 2024-08-18 and 2024-08-19
    SELECT 
        old.product_id
    FROM 
        rtg_automotive.supplier_stock_history old
    JOIN 
        rtg_automotive.supplier_stock_history new
    ON 
        old.product_id = new.product_id
        AND new.updated_date = DATE('2024-08-19')
    WHERE 
        old.updated_date = DATE('2024-08-18')
        AND new.quantity <> old.quantity
    
    UNION
    
    -- Subquery to get product_id with only one record on 2024-08-19
    SELECT 
        product_id
    FROM 
        rtg_automotive.supplier_stock_history
    WHERE 
        updated_date = DATE('2024-08-19')
    GROUP BY 
        product_id
    HAVING 
        COUNT(product_id) = 1
) relevant_product_ids ON p.product_id = relevant_product_ids.product_id
WHERE relevant_product_ids.product_id IS NOT NULL;
