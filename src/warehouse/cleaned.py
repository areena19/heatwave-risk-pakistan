def load_cleaned(con):
    con.execute("""
        CREATE OR REPLACE TABLE cleaned_hourly AS
        SELECT * FROM read_parquet('data/cleaned/hourly_dq.parquet')
    """)