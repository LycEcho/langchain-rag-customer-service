from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from service.logic import Logic
from typing import Optional, Dict, List, Any, Union
from constant.chatRequest import ChatHistoryConstant
app = FastAPI(
    title="通用ai客服 API",
    description="通用ai客服 API 的详细描述",
    version="1.0.0",
    docs_url="/docs",  # 自定义 Swagger UI 的访问路径
    redoc_url="/redoc" # 自定义 ReDoc 的访问路径)
)
logic = Logic()


class ChatRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    chat_history: Optional[List[ChatHistoryConstant]] = None
    use_history: bool = True

@app.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    #try:
    response = logic.generate_text_agent(
        question=request.question,
        user_id=request.user_id,
        chat_history=request.chat_history,
        use_history=request.use_history
    )
    return {"success": True, "data": response}
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize/{user_id}")
async def summarize(user_id: str) -> Dict[str, Any]:
    try:
        success = logic.summarize_user_history(user_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))