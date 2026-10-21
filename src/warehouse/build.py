import os

import duckdb

from src.warehouse.cleaned import load_cleaned
from src.warehouse.gold import load_gold
from src.warehouse.raw import load_raw


def main():
    os.makedirs("data/warehouse", exist_ok=True)
    con = duckdb.connect("data/warehouse/heatwave.duckdb")

    load_raw(con)
    load_cleaned(con)
    load_gold(con)

    print(con.execute("""
        SELECT 'raw_manifest' AS tbl, COUNT(*) AS rows FROM raw_manifest
        UNION ALL
        SELECT 'cleaned_hourly', COUNT(*) FROM cleaned_hourly
        UNION ALL
        SELECT 'gold_daily', COUNT(*) FROM gold_daily
        UNION ALL
        SELECT 'gold_features', COUNT(*) FROM gold_features
    """).df())

    print(con.execute("""
        SELECT city, COUNT(*) AS days, ROUND(AVG(max_hi), 2) AS avg_hi, ROUND(MAX(max_hi), 2) AS max_hi
        FROM gold_features
        GROUP BY city
        ORDER BY city
    """).df())

    con.close()


if __name__ == "__main__":
    main()