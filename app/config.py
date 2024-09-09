import streamlit as st
import pandas as pd


def process_numerical(x):
    if not isinstance(x, (int, float)):
        return 0
    elif x <= 0:
        return 0
    elif x > 10:
        return 10
    else:
        return x


# Database configuration
DB_CONFIG = {
    "user": st.secrets["db_config"]["user"],
    "password": st.secrets["db_config"]["password"],
    "host": st.secrets["db_config"]["host"],
    "port": st.secrets["db_config"]["port"],
    "database": st.secrets["db_config"]["database"],
}


# Login credentials (consider using a more secure method in production)
LOGIN_CREDENTIALS = {
    "username": st.secrets["login_credentials"]["username"],
    "password": st.secrets["login_credentials"]["password"],
}


CONFIG = {
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
        "process_func": lambda x: 10 if x == "Y" else 0,
    },
    "MOT": {
        "code_column_number": 1,
        "stock_column_number": 3,
        "process_func": process_numerical,
    },
    "RFX": {
        "code_column_number": 1,
        "stock_column_number": 4,
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
        "process_func": lambda x: 10 if x is None or pd.isna(x) else 0,
    },
    "SMP": {
        "code_column_number": 1,
        "stock_column_number": 1,
        "process_func": lambda _: 10,
    },
    "ELR": {
        "code_column_number": 1,
        "stock_column_number": 4,
        "process_func": process_numerical,
    },
}
