from fastapi import FastAPI, HTTPException
from psycopg.errors import UniqueViolation
from pydantic import BaseModel, EmailStr, Field
from database import create_user, get_user_by_username
from security import hash_password, verify_password
app = FastAPI()



class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    username: str
    password: str


@app.post("/users/register", status_code=201)
def register_user(user: UserRegister):
    hashed_password = hash_password(user.password)

    try:
        created_user = create_user(
            user.username,
            user.email,
            hashed_password,
        )
    except UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
        )

    return created_user

@app.post("/login")
def login(user: UserLogin):
    db_user = get_user_by_username(user.username)

    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not verify_password(
        user.password,
        db_user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    return {
        "id": db_user["id"],
        "username": db_user["username"],
        "email": db_user["email"],
        "role": db_user["role"],
    }