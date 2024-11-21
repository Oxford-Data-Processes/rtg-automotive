import requests

items = [
    {
        "custom_label": "Item A",
        "part_number": "A123",
        "supplier": "Supplier X",
        "quantity": 10,
        "updated_date": "2023-10-01",
    },
    {
        "custom_label": "Item B",
        "part_number": "B456",
        "supplier": "Supplier Y",
        "quantity": 5,
        "updated_date": "2023-10-01",
    },
    {
        "custom_label": "Item C",
        "part_number": "C789",
        "supplier": "Supplier Z",
        "quantity": 20,
        "updated_date": "2023-10-01",
    },
]

API_ID = "tsybspea31"
STAGE_LOWER = "dev"


def add_items_to_supplier_stock(items) -> list:
    chunk_size = 100

    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        response = requests.post(
            f"https://{API_ID}.execute-api.eu-west-2.amazonaws.com/{STAGE_LOWER}/items/?table_name=supplier_stock&type=append",
            headers={"Content-Type": "application/json"},
            json={"items": chunk},
        )
        if response.status_code != 200:
            print(f"Failed to add items: {response.text}")
