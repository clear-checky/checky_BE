from pydantic import BaseModel
from typing import List, Optional, Literal, Union

RiskLevel = Literal["danger", "warning", "safe"]

class Sentence(BaseModel):
    id: str
    text: str
    risk: RiskLevel
    why: Optional[str] = None
    fix: Optional[str] = None

class Article(BaseModel):
    id: Union[int, str]
    title: str
    sentences: List[Sentence] = []

class AnalyzeRequest(BaseModel):
    articles: List[Article]

class AnalyzeResponse(BaseModel):
    articles: List[Article]
    counts: dict                  # {"danger":..,"warning":..,"safe":..,"total":..}
    safety_percent: float         # 예: 87.5 (0.1% 단위 반올림)