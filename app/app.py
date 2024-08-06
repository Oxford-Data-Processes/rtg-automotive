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


def process_stock_data():
    # Read the supplier_stock_history table from the database
    df = read_from_sqlite("supplier_stock_history")

    # Remove duplicates based on product_id and updated_date
    df = df.drop_duplicates(subset=["product_id", "updated_date"], keep="first")

    # Sort the dataframe by product_id and updated_date
    df = df.sort_values(["product_id", "updated_date"], ascending=[True, False])

    # Group by product_id and get the two most recent entries for each
    df_grouped = df.groupby("product_id").head(2)

    # Calculate the quantity delta and get the most recent quantity
    df_delta = (
        df_grouped.groupby("product_id")
        .agg(
            {
                "quantity": lambda x: (
                    x.iloc[0] - x.iloc[1] if len(x) > 1 else x.iloc[0]
                ),
                "updated_date": "first",
            }
        )
        .reset_index()
    )

    # Rename the quantity column to quantity_delta
    df_delta = df_delta.rename(columns={"quantity": "quantity_delta"})

    # Add the most recent quantity
    df_delta["Quantity"] = df_grouped.groupby("product_id")["quantity"].first().values

    # Filter for values with non-zero delta
    df_delta = df_delta[
        (df_delta["quantity_delta"] != 0) & (df_delta["quantity_delta"].notnull())
    ]

    return df_delta


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


def create_ebay_dataframe(stock_df):

    # Read the product table from the database
    product_df = read_from_sqlite("product")

    # Merge stock_df with product_df
    ebay_df = pd.merge(
        stock_df.copy(),
        product_df[["product_id", "custom_label"]],
        on="product_id",
        how="inner",
    )

    # Read the store table from the database
    store_df = read_from_sqlite("store")

    # Merge ebay_df with store_df to get item_id
    ebay_df = pd.merge(
        ebay_df, store_df[["custom_label", "item_id"]], on="custom_label", how="inner"
    )

    # Select and rename the required columns
    ebay_df = ebay_df[["product_id", "item_id", "Quantity", "custom_label"]]
    ebay_df = ebay_df.rename(
        columns={
            "product_id": "ProductID",
            "custom_label": "CustomLabel",
            "item_id": "ItemID",
        }
    )

    ebay_df["Action"] = "Revise"
    ebay_df["SiteID"] = "UK"
    ebay_df["Currency"] = "GBP"

    ebay_df = ebay_df[
        [
            "Action",
            "ItemID",
            "SiteID",
            "Currency",
            "Quantity",
        ]
    ]

    # Convert Quantity to integer type
    ebay_df["Quantity"] = ebay_df["Quantity"].astype(int)

    return ebay_df


def process_stock_history_data(df):
    df_copy = df.copy()[["product_id", "quantity", "last_updated"]]
    df_copy["updated_date"] = df_copy["last_updated"].apply(lambda x: x[:10])
    df_copy.drop(columns=["last_updated"], inplace=True)
    return df_copy


st.title("Excel File Processor")

uploaded_folder = st.file_uploader(
    "Upload folder containing Excel files", type="xlsx", accept_multiple_files=True
)

product = pd.read_csv("product.csv")
upload_to_sqlite(product, "product", "replace")


def process_and_upload_files(uploaded_folder):
    processed_dataframes = []
    for file in uploaded_folder:
        supplier = file.name.split()[0]
        if supplier in config:
            df_output = process_dataframe(supplier, file)
            df_stock_history = process_stock_history_data(df_output)

            upload_to_sqlite(df_output, "supplier_stock", "append")
            upload_to_sqlite(df_stock_history, "supplier_stock_history", "append")

            processed_dataframes.append((df_output, supplier))
        else:
            st.warning(f"No configuration found for {supplier}. Skipping this file.")
    return processed_dataframes


def zip_dataframes(dataframes):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for df, name in dataframes:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr(f"{name}.csv", csv_buffer.getvalue())
    return zip_buffer


if uploaded_folder:
    st.write("Processing files...")
    processed_dataframes = process_and_upload_files(uploaded_folder)
    zip_buffer = zip_dataframes(processed_dataframes)

    st.success("All files processed!")
    st.download_button(
        label="Download All CSVs",
        data=zip_buffer.getvalue(),
        file_name="processed_files.zip",
        mime="application/zip",
    )


if st.button("Generate eBay Upload File"):

    stock_df = process_stock_data()
    ebay_df = create_ebay_dataframe(stock_df)
    st.dataframe(ebay_df)


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
