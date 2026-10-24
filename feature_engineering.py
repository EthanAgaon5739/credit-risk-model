
"""
feature_engineering.py
 
Turns the cleaned loan data into model-ready features. Besides encoding the raw
columns, it builds ratio features that mirror how lenders actually think about
affordability (loan size vs. income, monthly payment vs. income, etc.).
"""
 
import numpy as np
import pandas as pd
 
CLEAN_PATH = "data/loans_clean.csv"
TARGET = "default_flag"
 
BINARY_COLS = ["has_mortgage", "has_dependents", "has_cosigner"]
CATEGORICAL_COLS = ["education", "employment_type", "marital_status", "loan_purpose"]
 
 
def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create new columns that capture a borrower's ability to repay."""
    df = df.copy()
 
    # How big is the loan relative to yearly income?
    df["loan_to_income"] = df["loan_amount"] / df["income"]
 
    # Estimated monthly payment using the standard amortization formula
    monthly_rate = df["interest_rate"] / 100 / 12
    n_payments = df["loan_term"]
    df["monthly_payment"] = (
        df["loan_amount"] * monthly_rate / (1 - (1 + monthly_rate) ** (-n_payments))
    )
 
    # Share of monthly income that goes to this loan payment
    df["payment_to_income"] = df["monthly_payment"] / (df["income"] / 12)
 
    # Employment stability
    df["years_employed"] = df["months_employed"] / 12
    df["employment_share_of_adult_life"] = df["years_employed"] / (df["age"] - 17).clip(lower=1)
 
    # Debt burden combined with price of credit
    df["dti_x_interest"] = df["dti_ratio"] * df["interest_rate"]
 
    return df
 
 
def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Yes/No columns to 1/0 and one-hot encode categorical columns."""
    df = df.copy()
 
    for col in BINARY_COLS:
        df[col] = (df[col] == "Yes").astype(int)
 
    df = pd.get_dummies(df, columns=CATEGORICAL_COLS, drop_first=True, dtype=int)
    return df
 
 
def build_model_data(path: str = CLEAN_PATH):
    """Load the cleaned CSV and return (X, y) ready for scikit-learn."""
    df = pd.read_csv(path)
    df = add_features(df)
    df = encode_features(df)
 
    y = df[TARGET]
    X = df.drop(columns=[TARGET, "loan_id"])
    return X, y
 
 
if __name__ == "__main__":
    X, y = build_model_data()
    print(f"Feature matrix: {X.shape[0]:,} rows x {X.shape[1]} features")
    print("\nFeatures:")
    for col in X.columns:
        print(f"  - {col}")
    print(f"\nDefault rate: {y.mean() * 100:.2f}%")