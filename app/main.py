import streamlit as st
from typing import List, Tuple
import io
import zipfile
import pandas as pd
from config import CONFIG, DB_CONFIG, LOGIN_CREDENTIALS
from database import create_mysql_engine, append_mysql_table
from data_processing import (
    process_stock_data,
    process_dataframe,
    create_ebay_dataframe,
    process_stock_history_data,
)
from sqlalchemy.engine.base import Engine

def process_and_upload_files(uploaded_folder: List[pd.ExcelFile], processed_date: str, engine: Engine) -> List[Tuple[pd.DataFrame, str]]:
    """
    Process and upload files to the database.

    Args:
        uploaded_folder (List[pd.ExcelFile]): List of uploaded Excel files.
        processed_date (str): Date of processing.
        engine (Engine): SQLAlchemy engine for database connection.

    Returns:
        List[Tuple[pd.DataFrame, str]]: List of processed dataframes and their corresponding supplier names.
    """
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
    """
    Zip multiple dataframes into a single BytesIO object.

    Args:
        dataframes (List[Tuple[pd.DataFrame, str]]): List of tuples containing dataframes and their names.

    Returns:
        io.BytesIO: BytesIO object containing the zipped dataframes.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for df, name in dataframes:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr(f"{name}.csv", csv_buffer.getvalue())
    return zip_buffer

def process_files() -> None:
    """
    Handle file uploading, processing, and downloading of processed files.
    """
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

def generate_ebay_files() -> None:
    """
    Generate and provide download for eBay upload files.
    """
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

def main() -> None:
    """
    Main function to run the Streamlit app.
    """
    st.title("Excel File Processor")
    process_files()
    generate_ebay_files()

def login() -> bool:
    """
    Handle user login.

    Returns:
        bool: True if user is logged in, False otherwise.
    """
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