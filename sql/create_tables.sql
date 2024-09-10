CREATE DATABASE IF NOT EXISTS rtg_automotive;

USE rtg_automotive;

CREATE TABLE IF NOT EXISTS product (
    custom_label VARCHAR(255),
    part_number VARCHAR(255),
    supplier VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS store (
    item_id INT,
    brand VARCHAR(255),
    custom_label VARCHAR(255),
    store VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS supplier_stock (
    custom_label VARCHAR(255),
    part_number VARCHAR(255),
    supplier VARCHAR(255),
    quantity INT,
    last_updated VARCHAR(255)
);
