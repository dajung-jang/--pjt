"""조건 기반 항목 탐색. (F2011)

    1) 후보를 모은다. 글자 일치(지역·이름·유형)와 의미 유사도(surf_meta 색인)를 함께 쓴다.  (retriever)
    2) 프롬프트 5 로 후보 중 조건에 맞는 항목만 고른다.        (이 파일)
선택 결과가 없으면 빈 목록을 돌려준다. 호출 실패는 예외로 알린다. 화면이 안내 문구를 보여 준다.
"""
from collector import parse_index_list
from config import CONDITION_CANDIDATES, CONDITION_MAX_RESULTS, CONDITION_POOL
from items import build_item_text, item_label
from llm import get_llm
from prompts import build_condition_messages
from retriever import keyword_search, search_items


def find_items(condition: str, llm=None, search=search_items, keyword=keyword_search) -> list[dict]:
    """조건에 맞는 항목 목록. 후보가 없거나 맞는 항목이 없으면 빈 목록."""
    candidates, seen = [], set()
    for item in keyword(condition, CONDITION_CANDIDATES) + search(condition, CONDITION_CANDIDATES):
        if item["id"] not in seen:  # 키워드 후보를 앞에 두고, 중복은 한 번만
            seen.add(item["id"])
            candidates.append(item)
    candidates = candidates[:CONDITION_POOL]
    if not candidates:
        return []
    texts = [f"{item_label(item)} — {build_item_text(item)}" for item in candidates]
    messages = build_condition_messages(condition, texts, CONDITION_MAX_RESULTS)
    reply = (llm or get_llm()).invoke(messages).content
    picked = parse_index_list(reply, len(candidates), CONDITION_MAX_RESULTS)
    return [candidates[number - 1] for number in picked]