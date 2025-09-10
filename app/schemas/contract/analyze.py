from fastapi import APIRouter
from app.schemas.contract.types import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/contract", tags=["contract"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_contract(payload: AnalyzeRequest):
    # 1단계: 임시 응답 — 모든 문장을 safe로 본다
    articles = payload.articles
    total = sum(len(a.sentences) for a in articles)
    counts = {"danger": 0, "warning": 0, "safe": total, "total": total}
    return AnalyzeResponse(articles=articles, counts=counts, safety_percent=100.0)