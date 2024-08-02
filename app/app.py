import os
import pandas as pd
import streamlit as st
import zipfile
import io
import sqlite3


def process_numerical(x):
    if not isinstance(x, (int, float)):
        return 0
    elif x <= 0:
        return 0
    elif x > 10:
        return 10
    else:
        return x


config = {
    "APE": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: 0 if x == "No" else (10 if x == "YES" else 0),
    },
    "BET": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "BGA": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "COM": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": process_numerical,
    },
    "FAI": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "FEB": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": process_numerical,
    },
    "FIR": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: 10 if x == "Y" else 0,
    },
    "FPS": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "process_func": process_numerical,
    },
    "JUR": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
    "KLA": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: x,
    },
    "KYB": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: 0 if x == "N" else (10 if x == "Y" else 0),
    },
    "MOT": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": process_numerical,
    },
    "ROL": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": lambda x: 10 if x == "In Stock" else 0,
    },
    "RTG": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": lambda x: 0 if str(x) == "B152381" else 20,
    },
    "SMP": {
        "code_column_number": 1,
        "stock_column_number": 2,
        "process_func": process_numerical,
    },
}


def upload_to_sqlite(df, table_name, if_exists, db_path="data.db"):
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)


def read_from_sqlite(table_name, db_path="data.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


def process_stock_data(days=7):
    stock_df = read_from_sqlite("supplier_stock")

    # Convert timestamp to datetime
    stock_df["last_updated"] = pd.to_datetime(stock_df["last_updated"])

    # Filter for dates in the past week
    one_week_ago = pd.Timestamp.now() - pd.Timedelta(days=days)
    stock_df = stock_df[stock_df["timestamp"] >= one_week_ago]

    # Sort the filtered data
    stock_df.sort_values(by=["supplier", "part_number", "timestamp"], inplace=True)

    # Group by supplier and part_number
    grouped_df = stock_df.groupby(["supplier", "part_number"])

    # Calculate the net delta
    net_delta_df = grouped_df.agg(
        start_stock=("stock_calculation", "first"),
        end_stock=("stock_calculation", "last"),
        start_date=("timestamp", "first"),
        end_date=("timestamp", "last"),
        custom_label=("custom_label", "first"),  # Add this line to include custom_label
    ).reset_index()

    # Calculate the delta
    net_delta_df["change"] = net_delta_df["end_stock"] - net_delta_df["start_stock"]

    # Select relevant columns for the final table
    final_df = net_delta_df[
        [
            "supplier",
            "part_number",
            "custom_label",
            "start_date",
            "end_date",
            "start_stock",
            "end_stock",
            "change",
        ]
    ]

    # Uncomment the following line if you want to filter out rows with no change
    final_df = final_df[final_df["change"] != 0]

    return final_df


def process_dataframe(config_key, file):
    st.write(f"Processing {file.name}...")
    df = pd.read_excel(file)

    config_data = config[config_key]
    code_column = df.iloc[:, config_data["code_column_number"] - 1]
    stock_column = df.iloc[:, config_data["stock_column_number"] - 1]

    last_updated = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    date_prefix = last_updated[:10]

    df_output = pd.DataFrame(
        {
            "stock_id": code_column.apply(lambda x: f"{date_prefix}-{config_key}-{x}"),
            "product_id": code_column.apply(lambda x: f"{config_key}-{x}"),
            "quantity_raw": stock_column,
            "quantity": stock_column.apply(config_data["process_func"]),
            "last_updated": pd.Series([last_updated] * len(code_column)),
        }
    )

    return df_output


def create_ebay_dataframe(stock_df, item_ids):
    # Create a new dataframe with renamed columns
    ebay_df = stock_df.rename(
        columns={
            "custom_label": "CustomLabel",
            "end_stock": "Quantity",
        }
    )

    ebay_df["Action"] = "Revise"
    ebay_df["SiteID"] = "UK"
    ebay_df["Currency"] = "GBP"

    ebay_df = ebay_df[
        [
            "Action",
            "CustomLabel",
            "SiteID",
            "Currency",
            "Quantity",
        ]
    ]

    # Remove rows with null values in the Quantity column
    ebay_df = ebay_df.dropna(subset=["Quantity"])

    # Convert Quantity to integer type
    ebay_df["Quantity"] = ebay_df["Quantity"].astype(int)

    # Join ebay_df with item_ids on the "custom_label" column
    ebay_df = ebay_df.merge(
        item_ids, left_on="CustomLabel", right_on="custom_label", how="left"
    )
    ebay_df = ebay_df.rename(columns={"item_id": "ItemID", "store": "Store"})

    ebay_df = ebay_df[["Action", "ItemID", "SiteID", "Currency", "Quantity", "Store"]]
    return ebay_df


st.title("Excel File Processor")

uploaded_folder = st.file_uploader(
    "Upload folder containing Excel files", type="xlsx", accept_multiple_files=True
)

product = pd.read_csv("product.csv")
upload_to_sqlite(product, "product", "replace")

if uploaded_folder:
    st.write("Processing files...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in uploaded_folder:
            supplier = file.name.split()[0]
            if supplier in config:
                df_output = process_dataframe(supplier, file)

                upload_to_sqlite(df_output, "supplier_stock", "append")

                csv_buffer = io.StringIO()

                df_output.to_csv(csv_buffer, index=False)
                zip_file.writestr(f"{supplier}.csv", csv_buffer.getvalue())
            else:
                st.warning(
                    f"No configuration found for {supplier}. Skipping this file."
                )

    st.success("All files processed!")
    st.download_button(
        label="Download All CSVs",
        data=zip_buffer.getvalue(),
        file_name="processed_files.zip",
        mime="application/zip",
    )


if st.button("Generate eBay Upload File"):

    stock_df = process_stock_data()

    upload_to_sqlite(stock_df, "stock_changes", "replace")

    # Create a new dataframe with renamed columns
    ebay_df = create_ebay_dataframe(
        stock_df, store_database[["item_id", "custom_label", "store"]]
    )

    st.dataframe(ebay_df)

    # Split ebay_df by Store and create a zip folder with separate CSVs
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for store, store_df in ebay_df.groupby("Store"):
            csv_buffer = io.StringIO()
            store_df.drop(columns=["Store"]).to_csv(csv_buffer, index=False)
            zip_file.writestr(
                f"ebay_upload_files/{store}_ebay_upload.csv", csv_buffer.getvalue()
            )

    # Create a download button for the zip folder containing CSVs
    st.download_button(
        label="Download eBay Upload CSVs",
        data=zip_buffer.getvalue(),
        file_name="ebay_upload_files.zip",
        mime="application/zip",
    )


if st.button("Download All Database Tables"):
    st.write("Preparing database tables for download...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr(f"{table_name}.csv", csv_buffer.getvalue())

        conn.close()

    st.success("All database tables prepared!")
    st.download_button(
        label="Download All Database Tables",
        data=zip_buffer.getvalue(),
        file_name="database_tables.zip",
        mime="application/zip",
    )
