import psycopg2
import os

# DB_URL= os.environ.get('DATABASE_URL', 'dbname=quiz_api_db')
DB_URL = ('dbname=quiz_api_db')

def connectToDB():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    return conn, cur

def closeDB(conn, cur):
    cur.close()
    conn.close()




def fetchData(query):
    conn, cur = connectToDB()
    try:
        cur.execute(query)
        result = cur.fetchone()

        return result

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to search the data.", error)
            return False

    finally:
        if (conn):
            closeDB(conn,cur)


def fetchAll(query):
    conn, cur = connectToDB()
    try:
        cur.execute(query)
        results = cur.fetchall()

        return results

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to search the data.", error)
            return False

    finally:
        if (conn):
            closeDB(conn,cur)





def insertData(query):
    conn, cur = connectToDB()
    try:
        cur.execute(query)
        conn.commit()
        print('Successfully inserted data.')
        return True

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to insert data.", error)
            return False

    finally:
        if (conn):
            closeDB(conn,cur)





def updateData(query):
    conn, cur = connectToDB()
    try:
        cur.execute(query)
        conn.commit()
        print('Successfully updated new game data.')
        return True

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to update new game data", error)
            return False

    finally:
        if (conn):
            closeDB(conn,cur)
