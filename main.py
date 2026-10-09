from fastapi import FastAPI, HTTPException
from psycopg.errors import UniqueViolation
from pydantic import BaseModel, EmailStr, Field
from security import hash_password
from database import create_user
app = FastAPI()



class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8)


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