def load_gold(con):
    con.execute("""
        CREATE OR REPLACE TABLE gold_daily AS
        SELECT * FROM read_parquet('data/processed/daily.parquet')
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold_features AS
        SELECT * FROM read_parquet('data/processed/features.parquet')
    """)