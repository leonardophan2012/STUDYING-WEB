import mysql.connector
from mysql.connector import Error
from flask import current_app


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
        )
    except Error as error:
        raise RuntimeError(f"Database connection failed: {error}") from error
