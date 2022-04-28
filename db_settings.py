import psycopg2
import os

DB_URL= os.environ.get('DATABASE_URL', 'dbname=quiz_api_db')

def connectToDB():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    return conn, cur

def closeDB(conn, cur):
    cur.close()
    conn.close()
