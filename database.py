from psycopg2 import pool


class Database:
    __connection_pool = None

    @staticmethod
    def initialise(**kwargs):
        Database.__connection_pool = pool.SimpleConnectionPool(1,
                                                               10,
                                                               **kwargs)

    @classmethod
    def get_connection(cls):
        return cls.__connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        cls.__connection_pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        cls.__connection_pool.closeall()


class CursorFromConnectionFromPool:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connection = Database.get_connection()
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:  # TypeError, AttributeError, ValueError
            self.connection.rollback()
        else:
            self.cursor.close
            self.connection.commit()
        Database.return_connection(self.connection)
