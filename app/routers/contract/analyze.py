from fastapi import APIRouter
from app.schemas.contract.types import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import classify_articles, compute_counts, safety_percent

router = APIRouter(prefix="/contract", tags=["contract"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_contract(payload: AnalyzeRequest):
    articles = await classify_articles(payload.articles)  # 현재는 mock
    counts = compute_counts(articles)
    sp = safety_percent(counts)
    return AnalyzeResponse(articles=articles, counts=counts, safety_percent=sp)