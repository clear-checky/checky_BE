from fastapi import APIRouter, HTTPException
from app.schemas.contract.types import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import (
    classify_articles,
    compute_counts,
    safety_percent,
)

router = APIRouter(prefix="/contract", tags=["contract"])

@router.post("/analyze", response_model=AnalyzeResponse, summary="계약서 문장 위험도 분석")
async def analyze_contract(payload: AnalyzeRequest) -> AnalyzeResponse:
    """
    프론트에서 보낸 계약서 조항/문장 배열을 분석하여
    각 문장의 risk/why/fix를 채워 반환합니다.
    """
    try:
        # 1) 문장 분석 (OpenAI 연동 또는 mock/fallback)
        articles = await classify_articles(payload.articles)

        # 2) 카운트/안전지수 계산
        counts = compute_counts(articles)
        sp = safety_percent(counts)

        # 3) 응답
        return AnalyzeResponse(
            articles=articles,
            counts=counts,
            safety_percent=sp,
        )
    except HTTPException:
        # FastAPI용 예외는 그대로 전달
        raise
    except Exception as e:
        # 예기치 못한 에러는 500으로 래핑 (로그는 서버 콘솔에서 확인)
        raise HTTPException(status_code=500, detail=f"Analyze failed: {type(e).__name__}")