import mysql.connector
from mysql.connector import Error
import pandas as pd

# ─────────────────────────────────────────────
#  DATABASE CONFIG
# ─────────────────────────────────────────────

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "MYSQL_PASSWORD"
}

DB_NAME = "credit_risk_db"

# ─────────────────────────────────────────────
#  CONNECTION HELPERS
# ─────────────────────────────────────────────
 
def get_connection(use_database=True):
    """Create and return a MySQL connection."""
    config = DB_CONFIG.copy()
    if use_database:
        config["database"] = DB_NAME
    return mysql.connector.connect(**config)
 
 
def create_database():
    """Create the credit_risk_db database if it doesn't already exist."""
    try:
        conn = get_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"Database '{DB_NAME}' ready.")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"Error creating database: {e}")
 
 
# ─────────────────────────────────────────────
#  TABLE CREATION
# ─────────────────────────────────────────────
 
def create_loans_table():
    """
    Create the loans table.
    NOTE: Columns are based on the common Kaggle Loan Default dataset.
    We'll adjust these once we inspect your actual CSV columns.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id           VARCHAR(50) PRIMARY KEY,
                age               INT,
                income            FLOAT,
                loan_amount       FLOAT,
                credit_score      INT,
                months_employed   INT,
                num_credit_lines  INT,
                interest_rate     FLOAT,
                loan_term         INT,
                dti_ratio         FLOAT,
                education         VARCHAR(50),
                employment_type   VARCHAR(50),
                marital_status    VARCHAR(50),
                has_mortgage      VARCHAR(10),
                has_dependents    VARCHAR(10),
                loan_purpose      VARCHAR(50),
                has_cosigner      VARCHAR(10),
                default_flag      INT
            )
        """)
 
        conn.commit()
        print("Table 'loans' created successfully.")
        cursor.close()
        conn.close()
 
    except Error as e:
        print(f"Error creating table: {e}")
 
 
# ─────────────────────────────────────────────
#  LOAD CSV INTO MYSQL
# ─────────────────────────────────────────────
 
def load_csv_to_mysql(csv_path: str):
    """
    Read the loan dataset CSV and insert it into the MySQL loans table.
    """
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")
 
        # Map the CSV's exact column names (from your dataset) to our table's column order
        column_order = [
            "LoanID", "Age", "Income", "LoanAmount", "CreditScore",
            "MonthsEmployed", "NumCreditLines", "InterestRate", "LoanTerm",
            "DTIRatio", "Education", "EmploymentType", "MaritalStatus",
            "HasMortgage", "HasDependents", "LoanPurpose", "HasCoSigner", "Default"
        ]
        df = df[column_order]
 
        conn = get_connection()
        cursor = conn.cursor()
 
        cursor.execute("TRUNCATE TABLE loans")
 
        insert_query = """
            INSERT INTO loans (
                loan_id, age, income, loan_amount, credit_score,
                months_employed, num_credit_lines, interest_rate, loan_term,
                dti_ratio, education, employment_type, marital_status,
                has_mortgage, has_dependents, loan_purpose, has_cosigner, default_flag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
 
        batch_size = 5000
        rows = df.to_records(index=False).tolist()
 
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            print(f"  Inserted rows {i} to {i + len(batch)}...")
 
        print(f"Finished inserting {len(rows)} total rows into the loans table.")
 
        cursor.close()
        conn.close()
 
    except Error as e:
        print(f"Error loading CSV into MySQL: {e}")
    except FileNotFoundError:
        print(f"Could not find file at {csv_path}")
 
 
# ─────────────────────────────────────────────
#  QUICK TEST QUERY
# ─────────────────────────────────────────────
 
def test_connection():
    """Print the first 5 rows from the loans table to confirm everything works."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loans LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        cursor.close()
        conn.close()
    except Error as e:
        print(f"Error testing connection: {e}")
 
 
# ─────────────────────────────────────────────
#  RUN ANY SQL QUERY -> PANDAS DATAFRAME
# ─────────────────────────────────────────────
 
def query_to_df(sql: str) -> pd.DataFrame:
    """Run a SQL query against MySQL and return the result as a DataFrame."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = cursor.column_names
        cursor.close()
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=columns)
 
 
# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
 
if __name__ == "__main__":
    create_database()
    create_loans_table()
    load_csv_to_mysql("data/loan_data.csv")
    test_connection()
 