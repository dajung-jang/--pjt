"""서핑 특화 기능: 오늘 조건으로 보는 입수 판단 가이드. (F2010)

사용자가 오늘의 조건(파도 높이, 바람 방향, 숙련도)을 직접 입력하면, 색인된 문서에서 관련 근거를 찾아
'입수 전에 고려할 점'을 정리해 준다. 실시간 날씨·파고 API 는 쓰지 않는다. 조건은 전부 사용자가 입력한 값이다.

안전 원칙
    - 수치 기준(몇 m 이상 위험 등)을 코드에 넣지 않는다. 근거 문서에 있는 내용만 쓴다.
    - '입수 통제·경보가 있다'고 표시되면 LLM 을 부르지 않고 입수하지 말라는 안내만 돌려준다.
"""
from typing import Callable

from citations import strip_empty_citations
from items import item_label
from llm import get_llm
from prompts import build_guide_messages
from retriever import retrieve

WIND_OPTIONS = [
    "바다에서 육지 쪽으로 분다 (온쇼어)",
    "육지에서 바다 쪽으로 분다 (오프쇼어)",
    "해안선과 나란히 분다 (사이드)",
    "모르겠다",
]
LEVELS = ["입문 (보드 위에 서는 연습 단계)", "중급 (혼자 파도를 잡고 탈 수 있음)", "상급 (다양한 조건에서 탈 수 있음)"]

BLOCKED_MESSAGE = (
    "입수 통제나 경보가 있다면 입수하지 마세요. 안전요원과 현장 안내를 따르는 것이 최우선입니다. "
    "이 경우에는 조건을 분석하지 않습니다."
)
FAILED_MESSAGE = ""  # 빈 문자열이면 화면이 '가이드를 만들지 못했습니다' 안내를 보여 준다


def describe_conditions(conditions: dict) -> str:
    """입력된 조건을 프롬프트에 넣을 문장으로 만든다."""
    return (
        f"- 파도 높이: 약 {conditions['wave']:.1f}m (사용자가 직접 입력)\n"
        f"- 바람: {conditions['wind']}\n"
        f"- 숙련도: {conditions['level']}"
    )


def guide_question(conditions: dict) -> str:
    """위키 수집(프롬프트 1)과 근거 검색에 쓸 질문 문장. 조건을 문장으로 풀어 쓴다."""
    return (
        f"파도 높이 {conditions['wave']:.1f}m, 바람 {conditions['wind']}, 숙련도 {conditions['level']}인 서퍼가 "
        "입수하기 전에 고려할 점과 위험 요소(이안류, 파도, 바람)는?"
    )


def run_guide(item: dict, conditions: dict, llm=None, retrieve_fn: Callable = retrieve) -> dict:
    """가이드를 만든다. 돌려주는 값: {"answer": str, "evidence": list}. 실패하면 answer 가 빈 문자열이다."""
    if conditions.get("blocked"):
        return {"answer": BLOCKED_MESSAGE, "evidence": []}
    evidence = retrieve_fn(item, guide_question(conditions))
    messages = build_guide_messages(item_label(item), describe_conditions(conditions), evidence)
    try:
        answer = strip_empty_citations((llm or get_llm()).invoke(messages).content)
    except Exception:  # 키 누락, 네트워크 오류 등. 추적 정보는 화면에 내보내지 않는다. (NF2004)
        answer = FAILED_MESSAGE
    return {"answer": answer, "evidence": evidence}