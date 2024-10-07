import datetime
from typing import Optional
from pydantic import BaseModel, Field
from pydantic.json import timedelta_isoformat
from pydantic_core import to_jsonable_python


class RequestMessage(BaseModel):
    id: str
    message: str
    timestamp: datetime.datetime
    session_id: str
    model: str
    architecture_choice: str
    history_management_choice: str
    is_user_message: bool = True

    class Config:
        json_encoders = {datetime.datetime: lambda v: v.isoformat()}


class ResponseMessage(BaseModel):
    session_id: str
    id: str
    message: str
    is_complete: bool = True
    model: Optional[str] = None
    architecture_choice: Optional[str] = None
    history_management_choice: Optional[str] = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    is_user_message: bool = False

    model_config = {"json_encoders": {datetime.datetime: lambda v: v.isoformat(), datetime.timedelta: lambda v: str(v)}}

    def to_dict(self):
        return to_jsonable_python(self.model_dump())


class Message(RequestMessage, ResponseMessage):
    pass
