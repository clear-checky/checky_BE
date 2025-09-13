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

def extract_document_title(articles):
    """AI가 문서 내용에서 제목을 추출하는 함수"""
    if not articles or not articles[0].sentences:
        return "계약서 분석 결과"
    
    # 첫 번째 문장에서 제목 추출 시도
    first_sentence = articles[0].sentences[0].text
    print(f"첫 번째 문장에서 제목 추출 시도: {first_sentence}")
    
    # "근로계약서", "임대차계약서", "매매계약서" 등 패턴 찾기
    title_patterns = [
        r'([가-힣\s]+계약서)',
        r'([가-힣\s]+근로계약서)',
        r'([가-힣\s]+임대차계약서)',
        r'([가-힣\s]+매매계약서)',
        r'([가-힣\s]+도급계약서)',
        r'([가-힣\s]+용역계약서)',
        r'([가-힣\s]+주택\s*임대차\s*계약서)',
        r'([가-힣\s]+부동산\s*임대차\s*계약서)',
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, first_sentence)
        if match:
            return match.group(1)
    
    # 패턴이 없으면 기본값
    return "계약서 분석 결과"

def is_non_article_sentence(text):
    """조항이 아닌 문장인지 판단하는 함수"""
    non_article_patterns = [
        r'본 계약의 효력을 증명하기 위하여',
        r'계약 당사자가 서명 또는 날인한다',
        r'\d{4}년 \d{1,2}월 \d{1,2}일',
        r'사용자\(대표자\)',
        r'근로자:',
        r'임대인:',
        r'임차인:',
        r'매도인:',
        r'매수인:',
    ]
    
    for pattern in non_article_patterns:
        if re.search(pattern, text):
            return True
    return False

def is_preamble_sentence(text):
    """서문 문장인지 판단하는 함수"""
    preamble_patterns = [
        r'본 계약은.*간의.*체결한다',
        r'본 계약은.*간의.*다음과 같이',
        r'본 계약서는.*간의.*체결한다',
        r'본 계약서는.*간의.*다음과 같이',
        r'근로계약서',
        r'임대차계약서',
        r'매매계약서',
        r'도급계약서',
        r'용역계약서',
    ]
    
    for pattern in preamble_patterns:
        if re.search(pattern, text):
            return True
    return False

def group_articles_by_clause(articles):
    """조항별로 그룹화하는 함수 - 문장 안에서 '제N조' 패턴 찾기"""
    from app.schemas.contract.types import Article, Sentence
    
    grouped = {}
    current_clause = None
    current_sentences = []
    non_article_sentences = []  # 조항이 아닌 문장들
    preamble_sentences = []  # 서문 문장들
    
    for article in articles:
        for sentence in article.sentences:
            # 서문 문장인지 먼저 확인
            if is_preamble_sentence(sentence.text):
                preamble_sentences.append(sentence)
                continue
            
            # 조항이 아닌 문장인지 확인
            if is_non_article_sentence(sentence.text):
                # 조항이 아닌 문장은 별도로 저장 (숫자 제거하지 않음)
                non_article_sentences.append(sentence)
                continue
            
            # 문장 안에서 "제n조" 패턴 찾기 (괄호 있음/없음 모두 처리)
            clause_match = re.search(r'제\s*(\d+)\s*조(?:\s*\([^)]+\))?', sentence.text)
            
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
                
                # 제목 생성 (괄호 내용이 있으면 포함)
                full_match = clause_match.group(0)  # 전체 매칭된 문자열
                title = f'제{clause_num}조'
                
                # 괄호 내용이 있으면 제목에 포함
                if '(' in full_match and ')' in full_match:
                    # 괄호 내용 추출
                    paren_match = re.search(r'\(([^)]+)\)', full_match)
                    if paren_match:
                        title = f'제{clause_num}조 ({paren_match.group(1)})'
                
                current_clause = clause_num
                current_sentences = []
                
                # 제목을 저장 (나중에 사용하기 위해)
                grouped[clause_num] = {
                    'title': title,
                    'sentences': []
                }
                
                # 문장에서 "제n조" 부분을 제거하고 실제 내용만 추출
                clean_text = re.sub(r'제\s*\d+\s*조(?:\s*\([^)]+\))?\s*', '', sentence.text).strip()
                
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
                    # 현재 조항에 속하는 문장
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
                else:
                    # 조항 매칭에 실패한 문장들은 기타사항으로 분류
                    non_article_sentences.append(sentence)
    
    # 마지막 조항 저장
    if current_clause and current_sentences:
        grouped[current_clause] = {
            'title': grouped[current_clause]['title'],
            'sentences': current_sentences.copy()
        }
    
    # Article 객체로 변환
    result = []
    
    # 서문이 있으면 맨 앞에 추가
    if preamble_sentences:
        result.append(Article(
            id="preamble",
            title="서문",
            sentences=preamble_sentences
        ))
    
    # 조항들을 순서대로 추가
    for clause_num, data in grouped.items():
        result.append(Article(
            id=int(clause_num),
            title=data['title'],
            sentences=data['sentences']
        ))
    
    # 조항이 아닌 문장들을 별도 Article로 추가
    if non_article_sentences:
        result.append(Article(
            id="non_article",
            title="기타 사항",
            sentences=non_article_sentences
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

        # AI가 문서 내용에서 제목 추출
        document_title = extract_document_title(payload.articles)
        print(f"AI가 추출한 문서 제목: {document_title}")
        
        # 파일명이 있으면 로그에 출력 (디버깅용)
        if file_name:
            print(f"원본 파일명: {file_name}")
            clean_filename = os.path.splitext(file_name)[0]
            print(f"파일명 기반 제목: {clean_filename}")
        print(f"최종 사용할 제목: {document_title}")
        
        # 4) 응답 (AI 추출 제목 포함)
        response = AnalyzeResponse(
            articles=articles,
            counts=counts,
            safety_percent=sp,
            title=document_title,  # AI가 추출한 제목 포함
        )
        
        return response
    except HTTPException:
        # FastAPI용 예외는 그대로 전달
        raise
    except Exception as e:
        # 예기치 못한 에러는 500으로 래핑 (로그는 서버 콘솔에서 확인)
        print(f"에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analyze failed: {type(e).__name__}")