from pydantic import BaseModel
class ChatHistoryConstant(BaseModel):
    user: str
    bot: str
    timestamp:str