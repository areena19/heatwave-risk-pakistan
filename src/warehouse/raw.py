def load_raw(con):
    con.execute("""
        CREATE OR REPLACE TABLE raw_manifest AS
        SELECT * FROM read_csv(
            'manifest.csv',
            delim=',',
            header=true,
            all_varchar=true,
            ignore_errors=true
        )
    """)