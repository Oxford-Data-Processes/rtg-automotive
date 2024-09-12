import pandas as pd
from pathlib import Path


def process_dataframe(df):
    df = df.iloc[:, :12]
    df.columns = [
        "item_id",
        "brand",
        "custom_label",
        "current_quantity",
        "title",
        "current_price",
        "prefix",
        "uk_rtg",
        "fps_wds_dir",
        "payment_profile_name",
        "shipping_profile_name",
        "return_profile_name",
    ]
    df["supplier"] = df["prefix"].fillna("").astype(str)
    df["supplier"] = df.apply(
        lambda row: (
            "RTG"
            if row["uk_rtg"] == "RTG"
            else (row["supplier"].split("-")[-1] if row["supplier"] else "RTG")
        ),
        axis=1,
    )
    return df


def read_excel_files(directory):
    dfs = {}
    for file in [f for f in directory.glob("*.xlsx") if not f.name.startswith("~$")]:
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
