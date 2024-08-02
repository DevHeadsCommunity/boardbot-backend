from pydantic import BaseModel
from datetime import datetime


class RequestMessage(BaseModel):
    id: str
    content: str
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
    content: str
    timestamp: datetime
    is_complete: bool
    input_token_count: int
    output_token_count: int
    elapsed_time: float
    is_user_message: bool = False
    model: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Message(RequestMessage, ResponseMessage):
    pass
