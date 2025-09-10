from typing import List
from app.schemas.contract.types import Article

async def classify_articles(articles: List[Article]) -> List[Article]:
    # TODO: 다음 단계에서 OpenAI 연동
    # 현재는 들어온 그대로 반환
    return articles

def compute_counts(articles: List[Article]):
    d = w = s = t = 0
    for a in articles:
        for x in a.sentences:
            t += 1
            if x.risk == "danger":
                d += 1
            elif x.risk == "warning":
                w += 1
            else:
                s += 1
    return {"danger": d, "warning": w, "safe": s, "total": t}

def safety_percent(counts: dict) -> float:
    return 100.0 if counts["total"] == 0 else round((counts["safe"] / counts["total"]) * 1000) / 10