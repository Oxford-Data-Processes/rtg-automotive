import pandas as pd
import streamlit as st
from typing import List, Tuple
import io
import zipfile
from config import CONFIG, DB_CONFIG, LOGIN_CREDENTIALS
from database import create_mysql_engine, read_from_mysql, append_mysql_table


def prepare_stock_data(engine):
    df = read_from_mysql("supplier_stock_history", engine)
    df = df.drop_duplicates(subset=["product_id", "updated_date"], keep="first")
    df = df.sort_values(["product_id", "updated_date"], ascending=[True, False])
    df_grouped = df.groupby("product_id").head(2)

    return df_grouped


def process_stock_data(engine):
    df_grouped = prepare_stock_data(engine)
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

    df_delta = df_delta.rename(columns={"quantity": "quantity_delta"})
    df_delta["Quantity"] = df_grouped.groupby("product_id")["quantity"].first().values
    df_delta = df_delta[
        (df_delta["quantity_delta"] != 0) & (df_delta["quantity_delta"].notnull())
    ]

    return df_delta


def process_dataframe(config_key, file, processed_date):
    df = pd.read_excel(file)

    config_data = CONFIG[config_key]
    code_column = df.iloc[:, config_data["code_column_number"] - 1]
    stock_column = df.iloc[:, config_data["stock_column_number"] - 1]

    df_output = pd.DataFrame(
        {
            "stock_id": code_column.apply(
                lambda x: f"{processed_date}-{config_key}-{x}"
            ),
            "product_id": code_column.apply(lambda x: f"{config_key}-{x}"),
            "quantity_raw": stock_column,
            "quantity": stock_column.apply(config_data["process_func"]),
            "last_updated": processed_date,
        }
    )

    return df_output


def merge_stock_with_product_and_store(stock_df, engine):
    product_df = read_from_mysql("product", engine)
    store_df = read_from_mysql("store", engine)

    ebay_df = pd.merge(
        stock_df.copy(),
        product_df[["product_id", "custom_label"]],
        on="product_id",
        how="inner",
    )

    ebay_df = pd.merge(
        ebay_df,
        store_df[["custom_label", "item_id", "store"]],
        on="custom_label",
        how="inner",
    )

    return ebay_df[["product_id", "item_id", "Quantity", "custom_label", "store"]]


def create_ebay_dataframe(stock_df, engine):
    ebay_df = merge_stock_with_product_and_store(stock_df, engine)
    ebay_df = ebay_df.rename(
        columns={
            "product_id": "ProductID",
            "custom_label": "CustomLabel",
            "item_id": "ItemID",
            "store": "Store",
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
            "Store",
        ]
    ]
    ebay_df["Quantity"] = ebay_df["Quantity"].astype(int)
    ebay_df["ItemID"] = ebay_df["ItemID"].astype(int)
    return ebay_df


def process_stock_history_data(df):
    df_copy = df.copy()[["product_id", "quantity", "last_updated"]]
    df_copy["updated_date"] = df_copy["last_updated"]
    df_copy.drop(columns=["last_updated"], inplace=True)
    return df_copy


def process_and_upload_files(uploaded_folder, processed_date, engine):
    processed_dataframes = []
    for file in uploaded_folder:
        supplier = file.name.split()[0]
        if supplier in CONFIG:
            df_output = process_dataframe(supplier, file, processed_date)
            df_stock_history = process_stock_history_data(df_output)

            append_mysql_table(df_output, "supplier_stock", engine)
            append_mysql_table(df_stock_history, "supplier_stock_history", engine)

            processed_dataframes.append((df_output, supplier))
        else:
            st.warning(f"No configuration found for {supplier}. Skipping this file.")
    return processed_dataframes


def zip_dataframes(dataframes: List[Tuple[pd.DataFrame, str]]) -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for df, name in dataframes:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr(f"{name}.csv", csv_buffer.getvalue())
    return zip_buffer


def main():
    st.title("Excel File Processor")

    uploaded_folder = st.file_uploader(
        "Upload folder containing Excel files", type="xlsx", accept_multiple_files=True
    )

    processed_date = st.date_input("Date", value=pd.Timestamp.now().date())
    process_files_button = st.button("Process Files")

    if process_files_button:
        st.write("Processing files...")
        engine = create_mysql_engine(**DB_CONFIG)
        processed_dataframes = process_and_upload_files(
            uploaded_folder, processed_date, engine
        )
        zip_buffer = zip_dataframes(processed_dataframes)

        st.success("All files processed!")
        st.download_button(
            label="Download All CSVs", 
            data=zip_buffer.getvalue(),
            file_name="processed_files.zip",
            mime="application/zip",
        )

    if st.button("Generate eBay Upload Files"):
        engine = create_mysql_engine(**DB_CONFIG)
        stock_df = process_stock_data(engine)
        ebay_df = create_ebay_dataframe(stock_df, engine)
        stores = list(ebay_df["Store"].unique())
        ebay_dfs = [
            (ebay_df[ebay_df["Store"] == store].drop(columns=["Store"]), store)
            for store in stores
        ]

        zip_buffer = zip_dataframes(ebay_dfs)

        st.download_button(
            label="Download eBay Upload Files",
            data=zip_buffer.getvalue(),
            file_name="ebay_upload_files.zip",
            mime="application/zip",
        )


def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if (
                username == LOGIN_CREDENTIALS["username"] and 
                password == LOGIN_CREDENTIALS["password"]
            ):
                st.session_state.logged_in = True
                st.success("Logged in as {}".format(username))
                st.rerun()
            else:
                st.error("Incorrect username or password")

    return st.session_state.logged_in


if __name__ == "__main__":
    if login():
        main()
