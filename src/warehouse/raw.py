def load_raw(con):
    con.execute("""
        CREATE OR REPLACE TABLE raw_manifest AS
        SELECT * FROM read_csv_auto('manifest.csv')
    """)