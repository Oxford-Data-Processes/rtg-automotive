CREATE INDEX idx_supplier_custom_label ON supplier_stock(supplier, custom_label);
CREATE INDEX idx_updated_date ON supplier_stock(updated_date);

CREATE INDEX idx_supplier_stock_ranked_custom_label ON supplier_stock_ranked(custom_label);

CREATE INDEX idx_store_filtered_item_id ON store_filtered(item_id);
CREATE INDEX idx_store_filtered_custom_label ON store_filtered(custom_label);
