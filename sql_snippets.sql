SELECT ss.*, p.custom_label
FROM "rtg_automotive"."supplier_stock" ss
JOIN "rtg_automotive"."product" p ON ss.part_number = p.part_number
WHERE p.custom_label = (
    SELECT custom_label
    FROM "rtg_automotive"."store"  
    WHERE item_id = 165363626624
);


SELECT DISTINCT supplier, year, month, day from "rtg_automotive"."supplier_stock" ORDER BY supplier, day DESC;