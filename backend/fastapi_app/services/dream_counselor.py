# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List
import os

# (선택) OpenAI가 있으면 더 자연스럽게 다듬기
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))

def _rule_based_summary(text: str, valence: Dict[str, float], facets: Dict[str, float]) -> str:
    pos, neg = valence.get("positive", 0.0), valence.get("negative", 0.0)
    hi = {k: v for k, v in facets.items() if v >= 0.6}
    lo = {k: v for k, v in facets.items() if v < 0.6}

    lines: List[str] = []

    # 1) 공감/정서 반영
    if pos - neg >= 0.2:
        lines.append("당신의 꿈에서는 전반적으로 안정감과 긍정성이 느껴져요.")
    elif neg - pos >= 0.2:
        lines.append("이 꿈은 긴장감이나 부담이 배경에 깔려 있는 듯해요. 혼자서 버텨 온 시간이 있었을까요?")
    else:
        lines.append("감정의 균형이 비교적 중립적이에요. 상황을 관찰하는 태도가 인상적이에요.")

    # 2) 주제 단서 해석
    if "friendliness" in hi:
        lines.append("타인과의 연결·협력 욕구가 또렷하게 드러납니다. 관계에서 얻는 힘이 크네요.")
    if "aggression" in hi or "conflict" in hi:
        lines.append("마음 한켠에 갈등/마찰 이슈가 남아 있을 수 있어요. 경계선을 정리하는 연습이 도움이 됩니다.")
    if "sexuality" in hi:
        lines.append("사적 영역과 친밀감에 대한 관심이 올라와 있어요. 내 속도와 안전감을 최우선으로 두세요.")
    if "success" in hi:
        lines.append("성취/진전에 대한 기대가 큽니다. 최근 목표나 역할 변화가 있었나요?")
    if "misfortune" in hi:
        lines.append("작은 불운/변수에 과민해질 수 있어요. ‘내가 통제할 수 있는 것’만 붙잡아 보자는 제안을 드려요.")

    # 3) 자기돌봄 제안(짧게)
    tips: List[str] = []
    if "conflict" in hi or "aggression" in hi:
        tips.append("오늘 5분만 ‘나의 경계선 문장(예: 지금은 어려워요, 내일 이야기해요)’을 적어 보세요.")
    if "friendliness" in hi:
        tips.append("고마웠던 사람 한 명에게 짧은 메시지를 보내 보세요. 연결감이 회복에 큰 힘이 돼요.")
    if "misfortune" in hi or neg > pos:
        tips.append("잠들기 전, 호흡 4-4 리듬으로 1분. 몸의 긴장을 내려놓는 데 효과적입니다.")
    if not tips:
        tips.append("오늘 꿈에서 느꼈던 핵심 장면을 한 줄로 기록해 보세요. 내일의 나에게 작게 신호가 됩니다.")

    lines.append("")
    lines.append("<<작은 실천 제안>>")
    for t in tips:
        lines.append(f"• {t}")

    # 4) 마무리
    lines.append("")
    lines.append("마지막으로, 꿈은 ‘나의 현재 마음상태’를 비유적으로 보여주는 거울이에요. "
                 "해석이 정답은 아니고, 당신에게 의미가 되는 느낌이 가장 중요합니다.")

    return "\n".join(lines)

def counseling_note(text: str, valence: Dict[str, float], facets: Dict[str, float]) -> str:
    base = _rule_based_summary(text, valence, facets)

    if not USE_OPENAI:
        return base

    # OpenAI가 있으면 문장을 더 따뜻하고 부드럽게 다듬기 (선택)
    try:
        from openai import OpenAI
        client = OpenAI()
        prompt = (
            "다음 한국어 상담 요약을 친절하고 부드럽게 다듬어 주세요. 과장/명령을 피하고, 유효성 검증과 선택지를 주는 어조로.\n\n"
            f"<<원문>>\n{base}\n\n"
            "출력은 한국어 순수 텍스트만 주세요."
        )
        resp = client.responses.create(model="gpt-4o-mini", input=prompt)
        return resp.output_text.strip() or base
    except Exception:
        return base
