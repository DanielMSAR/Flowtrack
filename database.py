# database.py
import mysql.connector
from config import DB_CONFIG

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as err:
            print(f"Error de conexión a la base de datos: {err}")
            # Aquí podrías lanzar una excepción o manejar el error
            self.connection = None

    def get_connection(self):
        if self.connection is None or not self.connection.is_connected():
            self.connect()
        return self.connection

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    # Métodos genéricos para ejecutar consultas
    def execute_query(self, query, params=None):
        conn = self.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        return None

    def execute_non_query(self, query, params=None):
        conn = self.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        return -1