import os, json
from typing import List
from app.schemas.contract.types import Article
from .openai_client import chat_completion

PROMPT = """당신은 계약서 분석 전문가입니다. 모든 답변은 한국어로만 하며,
요청된 JSON 형식과 길이를 반드시 지킵니다. 설명 문구나 마크다운을 출력하지 않습니다.

다음 '문장들' 배열(길이 {n})의 각 항목을 아래 기준으로 분류하세요.
반드시 길이가 {n}인 JSON "배열"만 반환합니다. 다른 텍스트/설명/마크다운 금지.

[분류 키]
- risk: "danger" | "warning" | "safe"
- why:  한 줄(최대 120자), 한국 법/관행/판례 흐름에 맞춘 간결 근거
- fix:  한 줄(최대 120자), 실무적으로 적용 가능한 개선 문구

[판단 기준]
- "danger" (즉시 위험)
  • 해고: 즉시 해고/예고 없이 해고/서면통지 없음/정당사유 불명
  • 임금·수당: 연장·야간·휴일근로 수당 미지급/포괄임금으로 수당 전면 배제
  • 손해배상: 사업상 위험·모든 손해의 전적 부담 등 포괄 전가
  • 업무조건: 일방적 근로조건 변경/근로시간 중 대기·지시로 휴게 침해
- "warning" (주의·조정 필요)
  • 경업금지: 과도한 범위/지역/기간(일반적으로 1년 초과, 직무 불특정, 전 업종 등)
  • 비밀유지: 비밀 범위 불명확/과도한 포괄성
  • 기타: 불명확 표현으로 근로자 권리 침해 우려
- "safe"
  • 법정 기준 충족 또는 통상적·명확한 조항

[타이브레이커]
- 애매하면 근로자 보호 관점에서 더 보수적으로("warning" → "danger" 우선).

[출력 형식(배열, 길이 {n}) — 예시]
[
  {"risk":"danger","why":"해고예고·서면통지 의무 위반 소지","fix":"해고는 정당사유·서면통지·예고수당 원칙 준수"},
  {"risk":"warning","why":"경업금지 기간·범위 과도","fix":"기간 1년 내, 직무·지역 한정 및 비밀보호 범위 특정"},
  {"risk":"safe","why":"법정 기준에 부합","fix":""}
]

문장들:
{texts_json}
"""

def _fallback(n: int):
    return [{"risk": "safe", "why": "-", "fix": "-"} for _ in range(n)]

async def classify_articles(articles: List[Article]) -> List[Article]:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")

    for art in articles:
        if not art.sentences:
            continue

        # 각 조항의 문장들을 AI에게 분석 요청
        texts = [s.text for s in art.sentences]
        
        if not api_key:
            parsed = _fallback(len(texts))
        else:
            # 조항별 분석을 위한 프롬프트 생성
            article_prompt = f"""다음은 계약서의 '{art.title}' 조항에 속한 문장들입니다.
각 문장의 위험도를 분석해주세요.

문장들:
{json.dumps(texts, ensure_ascii=False)}

위험도는 다음 중 하나로 분류해주세요:
- danger: 위험한 조항 (법적 문제 가능성 높음)
- warning: 주의가 필요한 조항 (개선 권장)
- safe: 안전한 조항 (문제없음)

각 문장에 대해 다음을 제공해주세요:
1. 위험도 (danger/warning/safe)
2. 위험한 이유 (why)
3. 개선 방안 (fix)

반드시 길이가 {len(texts)}인 JSON 배열만 반환하세요:
[
  {{"risk":"danger","why":"해고예고·서면통지 의무 위반 소지","fix":"해고는 정당사유·서면통지·예고수당 원칙 준수"}},
  {{"risk":"warning","why":"경업금지 기간·범위 과도","fix":"기간 1년 내, 직무·지역 한정 및 비밀보호 범위 특정"}},
  {{"risk":"safe","why":"법정 기준에 부합","fix":""}}
]"""
            
            try:
                res = await chat_completion([
                    {"role": "system", "content": "당신은 계약서 분석 전문가입니다. 한국어로 간결하게 답하세요. 반드시 JSON 배열만 반환하세요."},
                    {"role": "user", "content": article_prompt},
                ])
                content = res["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if not isinstance(parsed, list):
                    parsed = _fallback(len(texts))
                if len(parsed) != len(texts):
                    parsed = (parsed + _fallback(len(texts)))[:len(texts)]
            except Exception as e:
                print(f"AI 분석 실패: {str(e)}")
                parsed = _fallback(len(texts))

        # 결과를 문장에 업데이트
        for s, p in zip(art.sentences, parsed):
            s.risk = p.get("risk", s.risk)
            s.why  = p.get("why", s.why)
            s.fix  = p.get("fix", s.fix)

    return articles

def compute_counts(articles):
    danger = warning = safe = total = 0
    for art in articles:
        for s in art.sentences:
            total += 1
            if s.risk == "danger":
                danger += 1
            elif s.risk == "warning":
                warning += 1
            else:
                safe += 1
    return {"danger": danger, "warning": warning, "safe": safe, "total": total}


def safety_percent(counts: dict) -> float:
    if counts["total"] == 0:
        return 100.0
    return round((counts["safe"] / counts["total"]) * 1000) / 10