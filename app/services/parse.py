# app/services/parse.py
import json
from typing import List
from .schemas_llm import LLMItem, ValidationError

def parse_llm_array(raw: str, expected_len: int) -> List[LLMItem]:
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("not a list")
    except Exception:
        return [LLMItem(risk="safe", why="-", fix="-") for _ in range(expected_len)]

    items: List[LLMItem] = []
    for i in range(expected_len):
        try:
            items.append(LLMItem(**(data[i] if i < len(data) else {})))
        except ValidationError:
            items.append(LLMItem(risk="safe", why="-", fix="-"))
    return items[:expected_len]