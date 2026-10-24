"""
data_cleaning.py
 
Pulls the raw loan data out of MySQL using SQL, validates and cleans it with
pandas, and saves a model-ready file to data/loans_clean.csv.
"""
 
import os
import pandas as pd
from database import query_to_df
 
CLEAN_PATH = "data/loans_clean.csv"
 
 
def load_raw_data() -> pd.DataFrame:
    """Pull every loan from the MySQL loans table."""
    return query_to_df("SELECT * FROM loans")
 
 
def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates, missing values, and impossible values."""
    print(f"Raw rows: {len(df):,}")
 
    before = len(df)
    df = df.drop_duplicates(subset="loan_id")
    print(f"Duplicate loan IDs removed: {before - len(df):,}")
 
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("Missing values: none found")
    else:
        print("Missing values found:")
        print(missing)
        df = df.dropna()
 
    before = len(df)
    valid = (
        df["age"].between(18, 100)
        & df["credit_score"].between(300, 850)
        & (df["income"] > 0)
        & (df["loan_amount"] > 0)
        & (df["interest_rate"] > 0)
        & (df["loan_term"] > 0)
        & (df["dti_ratio"] >= 0)
        & (df["months_employed"] >= 0)
        & df["default_flag"].isin([0, 1])
    )
    df = df[valid].copy()
    print(f"Rows removed by range checks: {before - len(df):,}")
 
    text_cols = [c for c in df.select_dtypes(include=["object", "string"]).columns if c != "loan_id"]
    for col in text_cols:
        df[col] = df[col].str.strip()
 
    default_rate = df["default_flag"].mean() * 100
    print(f"Clean rows: {len(df):,}")
    print(f"Default rate: {default_rate:.2f}%  (imbalanced - accuracy alone will be misleading)")
 
    return df.reset_index(drop=True)
 
 
if __name__ == "__main__":
    raw = load_raw_data()
    clean = validate_and_clean(raw)
 
    os.makedirs("data", exist_ok=True)
    clean.to_csv(CLEAN_PATH, index=False)
    print(f"Saved cleaned data to {CLEAN_PATH}")