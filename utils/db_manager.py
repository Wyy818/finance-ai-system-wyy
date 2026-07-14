import sqlite3
import pandas as pd
import os

DB_PATH = "data.db"

def save_to_db(df: pd.DataFrame, table_name: str):
    """将 DataFrame 存入数据库"""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(name=table_name, con=conn, if_exists="replace", index=False)
    conn.close()

def load_from_db(table_name: str) -> pd.DataFrame:
    """从数据库读取数据"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def get_all_tables() -> list:
    """获取数据库中所有的表名"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables