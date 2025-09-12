"""
챗봇 API 테스트 스크립트
사용법: python test_chat_api.py
"""

import asyncio
import httpx
import json


async def test_chat_api():
    """챗봇 API 테스트"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. 서버 상태 확인
        print("1. 서버 상태 확인...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"서버 상태: {response.json()}")
        except Exception as e:
            print(f"서버 연결 실패: {e}")
            return
        
        # 2. 챗봇 대화 테스트
        print("\n2. 챗봇 대화 테스트...")
        
        # 첫 번째 메시지
        chat_data = {
            "message": "안녕하세요! 오늘 날씨가 어떤가요?",
            "conversation_history": []
        }
        
        try:
            response = await client.post(
                f"{base_url}/chat/",
                json=chat_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"사용자: {chat_data['message']}")
                print(f"AI: {result['message']}")
                print(f"응답 시간: {result['timestamp']}")
                
                # 두 번째 메시지 (대화 기록 포함)
                chat_data2 = {
                    "message": "고마워요! 그럼 내일은 어떨까요?",
                    "conversation_history": result['conversation_history']
                }
                
                response2 = await client.post(
                    f"{base_url}/chat/",
                    json=chat_data2,
                    headers={"Content-Type": "application/json"}
                )
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    print(f"\n사용자: {chat_data2['message']}")
                    print(f"AI: {result2['message']}")
                    print(f"응답 시간: {result2['timestamp']}")
                    
                    print(f"\n총 대화 기록 수: {len(result2['conversation_history'])}")
                    
                else:
                    print(f"두 번째 메시지 실패: {response2.status_code} - {response2.text}")
            else:
                print(f"첫 번째 메시지 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"챗봇 대화 테스트 실패: {e}")


if __name__ == "__main__":
    print("챗봇 API 테스트를 시작합니다...")
    print("서버가 http://localhost:8000에서 실행 중인지 확인하세요.")
    print("=" * 50)
    
    asyncio.run(test_chat_api())
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
