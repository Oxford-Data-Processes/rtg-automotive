import json

LOCAL = "http://localhost:8000/items/"
LAMBDA = "https://tsybspea31.execute-api.eu-west-2.amazonaws.com/dev/items/"

GET_PARAMS = [
    {
        "table_name": "supplier_stock",
        "filters": json.dumps({"part_number": ["ABR101"]}),
        "columns": ",".join(["custom_label", "part_number"]),
        "limit": 5,
    }
]

GET_PARAMS = [
    {
        "table_name": "supplier_stock",
        "filters": json.dumps({"custom_label": ["UKD-APE-ABR101"]}),
        "columns": ",".join(["custom_label", "part_number"]),
        "limit": 5,
    },
    {
        "table_name": "supplier_stock",
        "filters": json.dumps({"updated_date": ["2024-11-21"]}),
        "limit": 5,
    },
    {
        "table_name": "store",
        "limit": 5,
    },
    {
        "table_name": "supplier_stock",
        "filters": json.dumps({"supplier": ["APE"]}),
        "columns": ",".join(["custom_label", "part_number"]),
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
                    "custom_label": "ABR104",
                    "part_number": "ABR101",
                    "supplier": "SupplierA",
                    "quantity": 10,
                    "updated_date": "2023-10-01",
                },
                {
                    "custom_label": "XYZ207",
                    "part_number": "XYZ202",
                    "supplier": "SupplierB",
                    "quantity": 5,
                    "updated_date": "2023-10-01",
                },
            ]
        },
    }
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

for params in POST_PARAMS:
    print("POST")
    print("PARAMS")
    print(params)
    response = requests.post(
        f"{url}?table_name={params['table_name']}&type={params['type']}",
        headers={"Content-Type": "application/json"},
        json=params["payload"],
    )
    print(response.json())
