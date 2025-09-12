import os
from typing import List
from datetime import datetime
from app.schemas.chat.types import ChatMessage
from .openai_client import chat_completion


class ChatService:
    def __init__(self):
        self.system_prompt = """당신은 친근하고 도움이 되는 AI 어시스턴트입니다. 
        사용자의 질문에 대해 정확하고 유용한 답변을 제공해주세요. 
        한국어로 대화하며, 친근하고 자연스러운 톤을 유지해주세요."""
    
    async def get_chat_response(self, user_message: str, conversation_history: List[ChatMessage] = None) -> str:
        """
        사용자 메시지에 대한 AI 응답을 생성합니다.
        
        Args:
            user_message: 사용자가 입력한 메시지
            conversation_history: 이전 대화 기록
            
        Returns:
            AI가 생성한 응답 메시지
        """
        try:
            # 대화 기록을 OpenAI API 형식으로 변환
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # 이전 대화 기록 추가
            if conversation_history:
                for msg in conversation_history[-10:]:  # 최근 10개 메시지만 사용 (토큰 제한 고려)
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # 현재 사용자 메시지 추가
            messages.append({"role": "user", "content": user_message})
            
            # OpenAI API 호출
            response = await chat_completion(messages, temperature=0.7)
            
            # 응답 추출
            ai_response = response["choices"][0]["message"]["content"]
            
            return ai_response
            
        except Exception as e:
            # 에러 발생 시 기본 응답 반환
            return f"죄송합니다. 현재 응답을 생성하는 중에 오류가 발생했습니다. 다시 시도해주세요. (오류: {str(e)})"
    
    def format_conversation_history(self, user_message: str, ai_response: str, 
                                  conversation_history: List[ChatMessage] = None) -> List[ChatMessage]:
        """
        대화 기록을 업데이트합니다.
        
        Args:
            user_message: 사용자 메시지
            ai_response: AI 응답
            conversation_history: 기존 대화 기록
            
        Returns:
            업데이트된 대화 기록
        """
        current_time = datetime.now()
        
        # 기존 대화 기록 복사
        updated_history = conversation_history.copy() if conversation_history else []
        
        # 사용자 메시지 추가
        updated_history.append(ChatMessage(
            role="user",
            content=user_message,
            timestamp=current_time
        ))
        
        # AI 응답 추가
        updated_history.append(ChatMessage(
            role="assistant",
            content=ai_response,
            timestamp=current_time
        ))
        
        return updated_history


# 전역 인스턴스 생성
chat_service = ChatService()
