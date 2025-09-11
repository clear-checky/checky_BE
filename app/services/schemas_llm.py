# app/services/schemas_llm.py
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError

Risk = Literal["danger", "warning", "safe"]

class LLMItem(BaseModel):
    risk: Risk
    why: Optional[str] = Field("", max_length=300)
    fix: Optional[str] = Field("", max_length=300)