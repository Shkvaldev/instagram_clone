from pydantic import BaseModel

class LoginAccount(BaseModel):
    login: str
    password: str

