import pandas as pd
from pathlib import Path


def process_dataframe(df):
    df = df.iloc[:, :7]
    df.columns = [
        "item_id",
        "brand",
        "custom_label",
        "current_quantity",
        "title",
        "current_price",
        "prefix",
    ]
    df["supplier"] = df["prefix"].fillna("").astype(str)
    df["supplier"] = df["supplier"].apply(lambda x: x.split("-")[-1] if x else "")
    return df


def read_excel_files(directory):
    dfs = {}
    for file in directory.glob("*.xlsx"):
        store = file.stem.split(" ")[0]
        excel = pd.ExcelFile(file)
        sheet_dfs = [
            process_dataframe(excel.parse(sheet)) for sheet in excel.sheet_names
        ]
        combined_df = pd.concat(sheet_dfs, ignore_index=True)
        combined_df["store"] = store
        dfs[store] = combined_df

        print(f"Store: {store}")
        print(combined_df.head())
    return dfs


def main():
    data_dir = Path("data/store_database")
    dfs = read_excel_files(data_dir)

    df_store = pd.concat(dfs.values(), ignore_index=True)

    df_store.drop_duplicates(subset=["item_id", "custom_label", "store"], inplace=True)
    df_store["custom_label"] = df_store["custom_label"].str.upper().str.strip()
    df_store.to_csv("data/tables/store.csv", index=False)


if __name__ == "__main__":
    main()
