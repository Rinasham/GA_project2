import psycopg2
from db_settings import connectToDB, closeDB

def get_user(id):
    # get name with id in session
  try:
    conn, cur = connectToDB()
    cur.execute(f"SELECT id, name FROM users WHERE id={id}")
    found_user = cur.fetchone()
    print(f'User found. {found_user}')
    id = found_user[0]
    if found_user[1] != None:
      name = found_user[1]
    else:
      name = None
    return id, name
  except (Exception, psycopg2.Error) as error:
    if (conn):
      print("Failed to search the data.", error)
  finally:
    if (conn):
      closeDB(conn,cur)





def check_is_admin(userID):
  conn, cur = connectToDB()
  try:
      cur.execute(f"SELECT is_admin FROM users WHERE id='{userID}'")
      is_admin = cur.fetchone()[0]

      # if the password is correct, set user-id to session
      if is_admin:
          print('This user is admin.')

          return True

      else:
          print('This user is not admin.')
          return False

  except TypeError as error:
      print('No such user.')

  except  (Exception, psycopg2.Error) as error:
      if (conn):
          print("Failed to search the data.", error)

  finally:
      if (conn):
          closeDB(conn,cur)