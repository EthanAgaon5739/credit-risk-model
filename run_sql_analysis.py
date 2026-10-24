"""
run_sql_analysis.py

Runs every query in analysis.sql against MySQL, prints the results, and saves
each one as a CSV in outputs/sql_results/ so the findings are easy to share.
"""

import os
import re
from database import query_to_df

SQL_FILE = "analysis.sql"
RESULTS_DIR = "outputs/sql_results"


def load_queries(path: str = SQL_FILE):
    """Split analysis.sql into (title, sql) pairs."""
    with open(path) as f:
        text = f.read()

    queries = []
    for chunk in text.split(";"):
        lines = chunk.strip().splitlines()
        comment_lines = [l.strip() for l in lines if l.strip().startswith("--")]
        sql = "\n".join(l for l in lines if not l.strip().startswith("--")).strip()
        if not sql:
            continue
        # Use the last comment line before the query as its title (e.g. "-- Q2: ...")
        title = comment_lines[-1].lstrip("- ").strip() if comment_lines else "Query"
        queries.append((title, sql))
    return queries


if __name__ == "__main__":
    os.makedirs(RESULTS_DIR, exist_ok=True)

    for title, sql in load_queries():
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

        df = query_to_df(sql)
        print(df.to_string(index=False))

        filename = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:50] + ".csv"
        df.to_csv(os.path.join(RESULTS_DIR, filename), index=False)

    print(f"\nSaved all results to {RESULTS_DIR}/")