DROP TABLE IF EXISTS store_filtered;

CREATE TABLE store_filtered AS (
    SELECT item_id, custom_label, ebay_store
    FROM store
);
