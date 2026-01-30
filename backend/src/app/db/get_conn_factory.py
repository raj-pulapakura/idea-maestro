from app.db.URL import DB_URL
import psycopg

def conn_factory():
    return psycopg.connect(DB_URL)  