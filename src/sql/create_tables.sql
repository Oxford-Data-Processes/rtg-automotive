CREATE TABLE supplier_stock (
    custom_label VARCHAR(255) PRIMARY KEY,
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

CREATE TABLE ebay (
    item_id BIGINT PRIMARY KEY,
    custom_label VARCHAR(255),
    quantity INT,
    quantity_delta INT,
    updated_date VARCHAR(255),
    supplier VARCHAR(255),
    ebay_store VARCHAR(255)
);