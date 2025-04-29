"""
This file contains all request models.
"""
from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email_id: str
    password: str

class UserLogin(BaseModel):
    email_id: str
    password: str