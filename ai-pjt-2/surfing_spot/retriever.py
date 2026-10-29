"""검색: 선택한 항목의 메타 청크 + 위키 문서 청크를 합쳐 근거 목록을 만든다. (F2006, F2014)

근거 구성
    1. 선택한 항목의 메타 청크 1건 (항상 포함)
    2. surf_docs 에서 질문과 가까운 청크 TOP_K_DOCS 건
       - 검색 범위는 '선택한 항목 id' 와 'common' 둘뿐이다. 다른 해변의 문서는 섞이지 않는다.
       - USE_MMR=True 이면 MMR 로 비슷한 청크가 몰리는 것을 줄인다. (심화 F2014)
    같은 청크가 두 번 들어오면 한 번만 남기고, 앞에서부터 근거 번호 1, 2, 3... 을 붙인다.

실행:
    python retriever.py 죽도 "이안류에 휘말리면 어떻게 해?"
"""
import logging
import sys

from dotenv import load_dotenv

from config import (
    COMMON_ITEM_ID,
    DOCS_COLLECTION,
    META_COLLECTION,
    MMR_FETCH_K,
    TOP_K_DOCS,
    USE_MMR,
)
from items import build_item_text, item_label
from vectorstore import get_store
logger = logging.getLogger(__name__)


def _meta_evidence(item: dict) -> dict:
    """선택한 항목의 메타 청크. 색인에 있으면 그 텍스트를, 없으면 항목 데이터로 바로 만든다."""
    text = ""
    try:
        found = get_store(META_COLLECTION, with_embeddings=False).get(ids=[item["id"]])
        if found["documents"]:
            text = found["documents"][0]
    except Exception:
        pass  # 색인을 못 읽어도 답변은 항목 데이터로 이어 간다
    return {
        "type": "meta",
        "scope": item["id"],
        "title": f"{item_label(item)} 항목 정보",
        "url": "",
        "source": item.get("source", ""),
        "text": text or build_item_text(item),
    }


def _doc_evidence(document) -> dict:
    meta = document.metadata
    return {
        "type": "doc",
        "scope": meta.get("scope", ""),
        "title": meta.get("title", ""),
        "url": meta.get("url", ""),
        "source": meta.get("source_type", "위키백과"),
        "text": document.page_content,
        "key": f"{meta.get('doc_key', '')}:{meta.get('chunk_index', '')}",
    }


def search_docs(item: dict, question: str, top_k: int = TOP_K_DOCS, use_mmr: bool = USE_MMR) -> list:
    """surf_docs 에서 '선택 항목 + common' 범위만 검색한다."""
    store = get_store(DOCS_COLLECTION)
    scope_filter = {"scope": {"$in": [item["id"], COMMON_ITEM_ID]}}
    if use_mmr:
        return store.max_marginal_relevance_search(
            question, k=top_k, fetch_k=max(MMR_FETCH_K, top_k), filter=scope_filter
        )
    return store.similarity_search(question, k=top_k, filter=scope_filter)


def retrieve(item: dict, question: str, top_k: int = TOP_K_DOCS, use_mmr: bool = USE_MMR) -> list[dict]:
    """근거 목록을 돌려준다. 각 근거에는 'number'(근거 번호)가 붙는다.

    문서 색인이 비어 있거나 검색이 실패해도 메타 근거 1건은 돌려준다. (오류가 화면에 새지 않게 하려는 것)
    """
    evidence = [_meta_evidence(item)]
    try:
        documents = search_docs(item, question, top_k, use_mmr)
    except Exception:
        logger.exception("문서 검색에 실패했습니다")  # 화면에는 내보내지 않고 터미널 로그에만 남긴다 (NF2004)
        documents = []

    seen = set()
    for document in documents:
        found = _doc_evidence(document)
        if found["key"] in seen:
            continue
        seen.add(found["key"])
        evidence.append(found)

    for number, found in enumerate(evidence, start=1):
        found["number"] = number
    return evidence


def main() -> None:
    load_dotenv()
    if len(sys.argv) < 3:
        print('사용법: python retriever.py 항목이름 "질문"')
        return
    from items import load_items

    name, question = sys.argv[1], sys.argv[2]
    item = next((i for i in load_items() if i["name"] == name or i["id"] == name), None)
    if item is None:
        print(f"[중단] '{name}' 항목을 찾지 못했습니다.")
        return
    print(f"항목: {item_label(item)} / 질문: {question} / MMR: {USE_MMR}\n")
    for found in retrieve(item, question):
        preview = found["text"][:70].replace("\n", " ")
        print(f"[근거 {found['number']}] ({found['type']}, 범위 {found['scope']}) {found['title']}\n      {preview}...")


if __name__ == "__main__":
    main()

def search_items(condition: str, top_k: int = 5) -> list[dict]:
    """조건 문장("강원도 양양 서핑 스팟" 등)과 가까운 항목을 surf_meta 색인에서 찾는다. (F2011)

    실패하면 예외를 그대로 낸다. 호출하는 화면이 '검색에 실패했습니다' 안내를 보여 준다.
    """
    from items import load_items

    by_id = {item["id"]: item for item in load_items()}
    found = get_store(META_COLLECTION).similarity_search(condition, k=top_k)
    return [by_id[d.metadata["item_id"]] for d in found if d.metadata.get("item_id") in by_id]

def keyword_search(condition: str, top_k: int = 10) -> list[dict]:
    """조건에 들어 있는 단어가 항목의 이름·지역·유형에 글자 그대로 들어 있는 항목을, 맞는 단어가 많은 순으로 돌려준다.

    지역이나 이름 같은 조건은 의미 유사도보다 글자 일치가 정확하다. (예: "양양" → 양양군의 모든 항목)
    """
    from items import load_items

    words = [word for word in condition.split() if len(word) >= 2]
    scored = []
    for item in load_items():
        text = f"{item['name']} {item['region']} {item['type']}"
        hits = sum(word in text for word in words)
        if hits:
            scored.append((hits, item))
    scored.sort(key=lambda pair: -pair[0])  # 정렬은 안정적이라 같은 점수는 목록 순서를 유지한다
    return [item for _, item in scored[:top_k]]