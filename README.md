# rtg-automotive

Design:

Tables:

Database: rtg_automotive

Table: product
- custom_label
- part_number
- supplier

Table: store
- item_id
- brand
- custom_label
- current_quantity
- title
- current_price
- prefix
- uk_rtg
- fps_wds_dir
- payment_profile_name
- shipping_profile_name
- return_profile_name
- supplier
- store

Table: supplier_stock
- custom_label
- part_number
- supplier
- quantity
- updated_date