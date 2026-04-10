from pydantic import BaseModel
from typing import Optional, Any
import datetime

class APIResponse(BaseModel):
    status: str
    code: int
    data: Optional[Any] = None
    message: Optional[str] = None


class NewUserData(BaseModel):
    first_name: str
    second_name: str
    tg_username: str
    chat_id: str
    role: int
    subgroup: int
    group_name: Optional[str] = None
    theacher_name: Optional[str] = None


class UserSchReq(BaseModel):
    chat_id: str
    date: Optional[str] = str(datetime.date.today())
    

class UserChangeTypeResSch(BaseModel):
    chat_id: str
    type: int
