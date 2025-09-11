# app/services/rules.py
import re
DANGER = [
  r"즉시\s*해고", r"예고\s*없", r"서면\s*통지\s*의무\s*없",
  r"연장근로수당\s*지급하지\s*않", r"모든\s*손해.*전적.*부담"
]
WARNING = [
  r"퇴직\s*후\s*\d+\s*년.*취업.*금지", r"경업\s*금지"
]

def apply_rules(text: str, risk: str) -> str:
    t = re.sub(r"\s+", "", text)
    if any(re.search(p, t) for p in DANGER):  return "danger"
    if risk != "danger" and any(re.search(p, t) for p in WARNING): return "warning"
    return risk