LOCAL = "http://localhost:8000/items/"
LAMBDA = "https://tsybspea31.execute-api.eu-west-2.amazonaws.com/dev/items/"

GET_PARAMS = [
    {
        "table_name": "supplier_stock",
        "filters": '{"part_number": ["ABR101"]}',  # JSON string for filters with "ABR101" in a list
        "columns": ["custom_label", "part_number"],
        "limit": 5,
    },
    {
        "table_name": "supplier_stock",
        "filters": '{"custom_label": ["UKD-APE-ABR101"]}',  # JSON string for filters with "UKD-APE-ABR101" in a list
        "columns": ["custom_label", "part_number"],
        "limit": 5,
    },
    {
        "table_name": "supplier_stock",
        "filters": '{"updated_date": ["2024-11-21"]}',  # JSON string for filters with "2024-11-21" in a list
        "limit": 5,
    },
    {
        "table_name": "store",
        "limit": 5,
    },
]

POST_PARAMS = [
    {
        "table_name": "supplier_stock",
        "type": "append",
        "payload": {
            "items": [
                {
                    "custom_label": "ABR101",
                    "part_number": "ABR101",
                    "supplier": "SupplierA",
                    "quantity": 10,
                    "updated_date": "2023-10-01",
                },
                {
                    "custom_label": "XYZ202",
                    "part_number": "XYZ202",
                    "supplier": "SupplierB",
                    "quantity": 5,
                    "updated_date": "2023-10-01",
                },
            ]
        },
    },
    {
        "table_name": "supplier_stock",
        "type": "append",
        "payload": {
            "items": [
                {
                    "custom_label": "XYZ205",
                    "part_number": "XYZ202",
                    "supplier": "SupplierB",
                    "quantity": 5,
                    "updated_date": "2023-10-20",
                }
            ]
        },
    },
]

import requests

url = LOCAL
print("URL: ", url)

for params in GET_PARAMS:
    print("GET")
    print("PARAMS")
    print(params)
    response = requests.get(url, params=params)

    data = response.json()
    print(data)
