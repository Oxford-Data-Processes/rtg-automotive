CREATE DATABASE IF NOT EXISTS rtg_automotive;

USE rtg_automotive;

CREATE TABLE IF NOT EXISTS product (
    product_id VARCHAR(255),
    part_number VARCHAR(255),
    custom_label VARCHAR(255),
    supplier VARCHAR(255),
    last_updated VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS store (
    item_id INT,
    brand VARCHAR(255),
    custom_label VARCHAR(255),
    current_quantity INT,
    store VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS supplier_stock (
    stock_id VARCHAR(255),
    product_id VARCHAR(255),
    quantity_raw VARCHAR(255),
    quantity INT,
    last_updated VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS supplier_stock_history (
    product_id VARCHAR(255),
    quantity INT,
    updated_date VARCHAR(255)
);