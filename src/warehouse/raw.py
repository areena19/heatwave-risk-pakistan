import pandas as pd

def load_raw(con):
    df = pd.read_csv("manifest.csv")
    con.register("temp_manifest", df)
    con.execute("CREATE OR REPLACE TABLE raw_manifest AS SELECT * FROM temp_manifest")
    con.unregister("temp_manifest")