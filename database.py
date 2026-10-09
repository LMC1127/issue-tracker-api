import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def test_connection():
    with psycopg.connect(DATABASE_URL,row_factory=dict_row,) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            print(result)


def create_user(username: str, email: str, password_hash: str):
    with psycopg.connect(DATABASE_URL,row_factory=dict_row,) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    email,
                    password_hash
                )
                VALUES (%s, %s, %s)
                RETURNING id, username, email, role, created_at;
                """,
                (username, email, password_hash),
            )

            return cursor.fetchone()


if __name__ == "__main__":
    test_connection()