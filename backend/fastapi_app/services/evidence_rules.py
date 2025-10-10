# backend/fastapi_app/services/evidence_rules.py
from typing import Dict, List

# Facet별 키워드 사전 (초기 버전)
LEX = {
    "aggression":  ["knife", "gun", "chase", "attack", "hit", "stab", "fight", "blood"],
    "conflict":    ["argue", "shout", "quarrel", "dispute", "pursue", "threaten"],
    "friendliness":["help", "comfort", "hug", "support", "reassure", "encourage"],
    "success":     ["escape", "solve", "found", "rescued", "safe", "relief", "overcome"],
    "misfortune":  ["lost", "fail", "broken", "injured", "fell", "stuck", "accident"],
    "sexuality":   ["kiss", "sex", "nude", "intimate", "touch"]
}

def extract_evidence_candidates(text: str, facets: Dict[str, float]) -> Dict[str, List[Dict]]:
    """
    간단한 규칙 기반 evidence 추출:
    - 확률이 높은 facet만 검사
    - 해당 facet 관련 키워드가 있는 문장을 evidence로 반환
    """
    # 아주 단순한 문장 분리 (나중에 nltk, spacy 등 교체 가능)
    sents = [s.strip() for s in text.replace("!"," .").replace("?"," .").split(".") if s.strip()]
    out: Dict[str, List[Dict]] = {}
    low = text.lower()

    for label, vocab in LEX.items():
        if facets.get(label, 0.0) < 0.3:
            continue
        hits: List[Dict] = []
        for s in sents:
            sl = s.lower()
            if any(w in sl for w in vocab):
                start = low.find(sl)
                hits.append({
                    "sentence": s + ".",
                    "start": start,
                    "end": start + len(s) + 1
                })
        if hits:
            out[label] = hits[:2]  # 문장 2개까지만
    return out
