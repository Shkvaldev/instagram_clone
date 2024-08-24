from pydantic import BaseModel

class Account4Login(BaseModel):
    login: str
    password: str

