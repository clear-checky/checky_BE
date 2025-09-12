from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas.chat.types import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    챗봇과 대화하는 엔드포인트
    
    Args:
        request: 사용자 메시지와 대화 기록이 포함된 요청
        
    Returns:
        AI 응답과 업데이트된 대화 기록
    """
    try:
        # 사용자 메시지 검증
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="메시지가 비어있습니다.")
        
        # AI 응답 생성
        ai_response = await chat_service.get_chat_response(
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        # 대화 기록 업데이트
        updated_history = chat_service.format_conversation_history(
            user_message=request.message,
            ai_response=ai_response,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            message=ai_response,
            conversation_history=updated_history,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류가 발생했습니다: {str(e)}")


