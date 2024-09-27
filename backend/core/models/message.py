from pydantic import BaseModel
from datetime import datetime


class RequestMessage(BaseModel):
    id: str
    message: str
    timestamp: datetime
    session_id: str
    model: str
    architecture_choice: str
    history_management_choice: str
    is_user_message: bool = True

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ResponseMessage(BaseModel):
    id: str
    session_id: str
    message: str
    is_complete: bool
    model: str
    architecture_choice: str
    history_management_choice: str
    is_user_message: bool = False


class Message(RequestMessage, ResponseMessage):
    pass
