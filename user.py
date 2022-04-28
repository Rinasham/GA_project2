import psycopg2
from db_settings import connectToDB, closeDB

def get_name(id):
    # get name with id in session
  try:
    conn, cur = connectToDB()
    cur.execute(f"SELECT name FROM users WHERE id={id}")
    found_name = cur.fetchone()[0]
    print(f'User found. {found_name}')
    user = found_name
    return user
  except (Exception, psycopg2.Error) as error:
    if (conn):
      print("Failed to search the data.", error)
  finally:
    if (conn):
      closeDB(conn,cur)