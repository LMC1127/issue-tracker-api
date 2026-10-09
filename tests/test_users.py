import os

import psycopg
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from psycopg.rows import dict_row


load_dotenv(".env.test", override=True)

from main import app


TEST_DATABASE_URL = os.getenv("DATABASE_URL")

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_users_table():
    with psycopg.connect(TEST_DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE TABLE users RESTART IDENTITY;"
            )

    yield

    with psycopg.connect(TEST_DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE TABLE users RESTART IDENTITY;"
            )


def test_register_user_success():
    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "user"

    assert "password" not in data
    assert "password_hash" not in data

    with psycopg.connect(
        TEST_DATABASE_URL,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    username,
                    email,
                    password_hash,
                    role
                FROM users
                WHERE username = %s;
                """,
                ("testuser",),
            )

            user = cursor.fetchone()

    assert user is not None
    assert user["username"] == "testuser"
    assert user["email"] == "testuser@example.com"
    assert user["role"] == "user"

    assert user["password_hash"] != "password123"

    assert user["password_hash"].startswith("$argon2")


def test_register_duplicate_username():
    client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "first@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "second@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email already exists"


def test_register_duplicate_email():
    client.post(
        "/users/register",
        json={
            "username": "firstuser",
            "email": "same@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/users/register",
        json={
            "username": "seconduser",
            "email": "same@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email already exists"


def test_register_short_username():
    response = client.post(
        "/users/register",
        json={
            "username": "ab",
            "email": "valid@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422

    with psycopg.connect(TEST_DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM users;
                """
            )

            count = cursor.fetchone()[0]

    assert count == 0


def test_register_invalid_email():
    response = client.post(
        "/users/register",
        json={
            "username": "validuser",
            "email": "not-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_short_password():
    response = client.post(
        "/users/register",
        json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_register_multiple_invalid_fields():
    response = client.post(
        "/users/register",
        json={
            "username": "ab",
            "email": "not-email",
            "password": "123",
        },
    )

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert len(errors) == 3

    fields = [error["loc"][-1] for error in errors]

    assert "username" in fields
    assert "email" in fields
    assert "password" in fields

def test_login_success():
    client.post(
        "/users/register",
        json={
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/login",
        json={
            "username": "loginuser",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "loginuser"
    assert data["email"] == "loginuser@example.com"
    assert data["role"] == "user"

def test_login_user_not_found():
    response = client.post(
        "/login",
        json={
            "username": "notexist",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_login_wrong_password():
    client.post(
        "/users/register",
        json={
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/login",
        json={
            "username": "loginuser",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"