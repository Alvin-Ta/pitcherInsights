import os
from contextlib import contextmanager

import psycopg2

DB_CONFIG = {
    "host":   "localhost",
    "port":   5432,
    "dbname": "mlb_pipeline",
    "user":   os.getenv("USER"),
}

@contextmanager
def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()