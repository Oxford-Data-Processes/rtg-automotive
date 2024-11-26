CREATE DATABASE rtg_automotive;

USE rtg_automotive;

CREATE TABLE supplier_stock (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    custom_label VARCHAR(255),
    part_number VARCHAR(255),
    supplier VARCHAR(255),
    quantity INT,
    updated_date VARCHAR(255)
);

CREATE TABLE store (
    item_id BIGINT PRIMARY KEY,
    brand VARCHAR(255),
    custom_label VARCHAR(255),
    current_quantity INT,
    title VARCHAR(255),
    current_price DOUBLE,
    prefix VARCHAR(255),
    uk_rtg VARCHAR(255),
    fps_wds_dir VARCHAR(255),
    payment_profile_name VARCHAR(255),
    shipping_profile_name VARCHAR(255),
    return_profile_name VARCHAR(255),
    supplier VARCHAR(255),
    ebay_store VARCHAR(255)
);

CREATE TABLE store_filtered AS (
    SELECT item_id, custom_label, ebay_store
    FROM store
);

 -- Drop the existing table if it exists
DROP TABLE IF EXISTS supplier_stock_ranked;

-- Create the new table
CREATE TABLE supplier_stock_ranked AS
WITH ranked_supplier_stock AS (
    SELECT
        ps.part_number,
        ps.supplier,
        ps.quantity,
        ps.updated_date,
        ps.custom_label,
        ROW_NUMBER() OVER (PARTITION BY ps.supplier, ps.custom_label ORDER BY ps.updated_date DESC) AS rn
    FROM
        supplier_stock ps
)

SELECT
    r.custom_label,
    r.quantity,
    COALESCE(
        MAX(CASE WHEN r.rn = 1 THEN r.quantity END) -
        MAX(CASE WHEN r.rn = 2 THEN r.quantity END),
        MAX(CASE WHEN r.rn = 1 THEN r.quantity END)
    ) AS quantity_delta,
    MAX(r.updated_date) AS updated_date,
    r.supplier
FROM
    ranked_supplier_stock r
GROUP BY
    r.custom_label, r.supplier;
