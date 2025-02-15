import mysql.connector
from mysql.connector import Error
from config import db_config1, db_config2, db_config3, db_config4

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config4)
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection


def execute_query(query, data=None, config=db_config4):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        if data:
            cursor.executemany(query, data)
        else:
            cursor.execute(query)
        connection.commit()
    except mysql.connector.Error as e:
        print(f"The error '{e}' occurred")
    finally:
        cursor.close()
        connection.close()

def fetch_existing_data(table_name):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    existing_data = cursor.fetchall()
    cursor.close()
    connection.close()
    return existing_data
