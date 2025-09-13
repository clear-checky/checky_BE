from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from app.schemas.contract.types import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import (
    classify_articles,
    compute_counts,
    safety_percent,
)
import re
import os
from typing import Optional

router = APIRouter(prefix="/contract", tags=["contract"])

def group_articles_by_clause(articles):
    """조항별로 그룹화하는 함수 - 문장 안에서 '제N조' 패턴 찾기"""
    from app.schemas.contract.types import Article, Sentence
    
    grouped = {}
    current_clause = None
    current_sentences = []
    
    for article in articles:
        for sentence in article.sentences:
            # 문장 안에서 "제n조 (내용)" 패턴 찾기
            clause_match = re.search(r'제\s*(\d+)\s*조\s*(\([^)]+\))?', sentence.text)
            
            if clause_match:
                # 새로운 조항이 시작됨
                if current_clause and current_sentences:
                    # 이전 조항 저장 (제목은 이미 생성됨)
                    grouped[current_clause] = {
                        'title': grouped[current_clause]['title'],
                        'sentences': current_sentences.copy()
                    }
                
                # 새 조항 시작
                clause_num = clause_match.group(1)
                clause_content = clause_match.group(2)  # 괄호 내용
                
                # 제목 생성 (괄호 내용 포함)
                if clause_content:
                    title = f'제{clause_num}조 {clause_content}'
                else:
                    title = f'제{clause_num}조'
                
                current_clause = clause_num
                current_sentences = []
                
                # 제목을 저장 (나중에 사용하기 위해)
                grouped[clause_num] = {
                    'title': title,
                    'sentences': []
                }
                
                # 문장에서 "제n조 (내용)" 부분을 제거하고 실제 내용만 추출
                clean_text = re.sub(r'제\s*\d+\s*조\s*\([^)]+\)\s*', '', sentence.text).strip()
                
                # 문장 시작의 불필요한 숫자 제거 (예: "1 근로시간은..." → "근로시간은...")
                clean_text = re.sub(r'^\s*\d+\s*', '', clean_text).strip()
                
                if clean_text:
                    sentence_obj = Sentence(
                        id=sentence.id,
                        text=clean_text,
                        risk=sentence.risk,
                        why=sentence.why,
                        fix=sentence.fix
                    )
                    current_sentences.append(sentence_obj)
                    grouped[clause_num]['sentences'].append(sentence_obj)
            else:
                # 조항 내 문장들
                if current_clause:
                    clean_text = sentence.text.strip()
                    
                    # 괄호 내용 뒤의 불필요한 숫자 제거 (예: "(근로시간 및 휴게시간) 1" → "(근로시간 및 휴게시간)")
                    clean_text = re.sub(r'(\([^)]+\))\s*\d+\s*', r'\1', clean_text).strip()
                    
                    # 문장 시작의 불필요한 숫자 제거 (예: "1 근로시간은..." → "근로시간은...")
                    clean_text = re.sub(r'^\s*\d+\s*', '', clean_text).strip()
                    
                    if clean_text:
                        sentence_obj = Sentence(
                            id=sentence.id,
                            text=clean_text,
                            risk=sentence.risk,
                            why=sentence.why,
                            fix=sentence.fix
                        )
                        current_sentences.append(sentence_obj)
                        grouped[current_clause]['sentences'].append(sentence_obj)
    
    # 마지막 조항은 이미 grouped에 저장되어 있음
    # 추가 처리 불필요
    
    # Article 객체로 변환
    result = []
    for clause_num, data in grouped.items():
        result.append(Article(
            id=int(clause_num),
            title=data['title'],
            sentences=data['sentences']
        ))
    
    return result

@router.post("/analyze-debug")
async def analyze_contract_debug(request: Request):
    """디버깅용 엔드포인트 - 원시 데이터 확인"""
    try:
        body = await request.json()
        print(f"받은 원시 데이터: {body}")
        print(f"데이터 타입: {type(body)}")
        
        # 스키마 검증 시도
        try:
            payload = AnalyzeRequest(**body)
            print(f"스키마 검증 성공: {payload}")
            return {"success": True, "message": "데이터 형식이 올바릅니다."}
        except Exception as e:
            print(f"스키마 검증 실패: {str(e)}")
            return {"success": False, "error": str(e), "received_data": body}
            
    except Exception as e:
        print(f"JSON 파싱 실패: {str(e)}")
        return {"success": False, "error": f"JSON 파싱 실패: {str(e)}"}

@router.post("/analyze", response_model=AnalyzeResponse, summary="계약서 문장 위험도 분석")
async def analyze_contract(payload: AnalyzeRequest, file_name: Optional[str] = None) -> AnalyzeResponse:
    """
    프론트에서 보낸 계약서 조항/문장 배열을 분석하여
    각 문장의 risk/why/fix를 채워 반환합니다.
    """
    try:
        print(f"받은 데이터: {payload}")
        print(f"articles 개수: {len(payload.articles)}")
        
        # 1) 조항별로 그룹화
        grouped_articles = group_articles_by_clause(payload.articles)
        print(f"그룹화된 조항 개수: {len(grouped_articles)}")
        
        # 2) 문장 분석 (OpenAI 연동 또는 mock/fallback)
        articles = await classify_articles(grouped_articles)

        # 3) 카운트/안전지수 계산
        counts = compute_counts(articles)
        sp = safety_percent(counts)

        # 4) 응답 (파일명 정보 포함)
        response = AnalyzeResponse(
            articles=articles,
            counts=counts,
            safety_percent=sp,
        )
        
        # 파일명이 있으면 로그에 출력 (디버깅용)
        if file_name:
            print(f"분석된 파일명: {file_name}")
            # 파일명에서 확장자 제거
            clean_filename = os.path.splitext(file_name)[0]
            print(f"제목으로 사용될 이름: {clean_filename}")
        
        return response
    except HTTPException:
        # FastAPI용 예외는 그대로 전달
        raise
    except Exception as e:
        # 예기치 못한 에러는 500으로 래핑 (로그는 서버 콘솔에서 확인)
        print(f"에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analyze failed: {type(e).__name__}")