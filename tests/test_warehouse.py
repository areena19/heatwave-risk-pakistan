import duckdb


def get_con():
    return duckdb.connect("data/warehouse/heatwave.duckdb", read_only=True)


def count(con, table):
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_row_counts():
    con = get_con()
    assert count(con, "cleaned_hourly") >= 70176
    assert count(con, "gold_daily") >= 2920
    assert count(con, "gold_features") >= 2888
    con.close()


def test_four_cities_equal_hours():
    con = get_con()
    n_cities, lo, hi = con.execute(
        "SELECT COUNT(DISTINCT city), MIN(c), MAX(c) FROM "
        "(SELECT city, COUNT(*) AS c FROM cleaned_hourly GROUP BY city)"
    ).fetchone()
    assert n_cities == 4
    assert lo == hi
    con.close()