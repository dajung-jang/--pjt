"""외부 문서 수집 흐름.

    F2003   검색어 추출 (프롬프트 1)
    F2004   위키 검색 → 후보 선별 (프롬프트 2) → 본문과 원문 URL 수집
    NF2002  이미 수집한 검색어는 다시 수집하지 않는다 (data/cache/queries.json)

문서가 저장되는 두 가지 범위(scope)
    "common"   모든 항목이 함께 쓰는 개념 문서 (서핑, 파도, 이안류 …) 와, 질문에서 뽑은 검색어로 선별한 문서
    항목 id    선택한 해변 자체를 다룬 문서 (예: 송정해수욕장 (부산) → spot_003)
검색할 때(6번 단계)는 '선택한 항목 id + common' 두 범위를 함께 본다.

수집한 본문은 data/cache/docs/ 에 파일로 저장한다. 색인(5번 단계)은 이 파일을 읽어서 하므로,
청크 크기를 바꿔 다시 색인해도 위키를 다시 호출하지 않는다.
색인(chroma_db)을 지우고 처음부터 다시 하려면 data/cache/ 도 함께 지워야 한다.

실행:
    python collector.py --common                    공통 개념 문서를 미리 수집한다. (처음 한 번)
    python collector.py "죽도" "이안류에 휘말리면 어떻게 해?"
        첫 번째 인자: 해변 이름 일부 (목록 이름에 들어 있으면 된다)
        두 번째 인자: 질문
        → 검색어, 새로 수집한 문서, 재사용한 문서, 버려진 후보를 보여 준다. (검증 4.2)
"""
import json
import re
import sys
import time
from datetime import date

from dotenv import load_dotenv

from config import (
    COMMON_ITEM_ID,
    DOCS_DIR,
    MAX_ITEM_DOCS,
    MAX_QUERIES,
    MAX_SELECT_DOCS,
    MIN_DOC_CHARS,
    QUERY_CACHE_PATH,
    SEARCH_LIMIT,
    WIKI_DOCS_PATH,
    WIKI_SLEEP_SEC,
)
from items import core_name, item_label, item_search_query, load_items, region_keyword
from llm import get_llm
from prompts import build_query_messages, build_select_messages
from wiki_client import check_user_agent, fetch_page, search


# ── LLM 응답 파싱 ───────────────────────────────────────────────────
def _read_json_list(text: str) -> list | None:
    """글 안의 [ ... ] 부분을 JSON 배열로 읽는다. 코드블록이나 설명이 섞여 있어도 된다. 실패하면 None."""
    match = re.search(r"\[.*\]", text or "", re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def parse_query_list(text: str, limit: int) -> list[str]:
    """프롬프트 1의 응답에서 검색어 목록을 꺼낸다. 중복과 빈 문자열은 지우고 limit 개까지만 남긴다."""
    data = _read_json_list(text) or []
    queries: list[str] = []
    for value in data:
        if not isinstance(value, str):
            continue
        query = value.strip()
        if query and query not in queries:
            queries.append(query)
    return queries[:limit]


def parse_index_list(text: str, size: int, limit: int) -> list[int]:
    """프롬프트 2의 응답에서 고른 후보 번호(1 ~ size)를 꺼낸다. 범위 밖 번호와 중복은 버린다."""
    data = _read_json_list(text) or []
    picked: list[int] = []
    for value in data:
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        if 1 <= value <= size and value not in picked:
            picked.append(value)
    return picked[:limit]


# ── 검색어 추출 (F2003) ─────────────────────────────────────────────
def extract_queries(item: dict, question: str, model=None) -> dict:
    """항목과 질문에서 외부 문서 검색어를 만든다.

    - 항목 자체를 다룬 문서의 검색어는 LLM 결과와 상관없이 항상 맨 앞에 넣는다.
    - 프롬프트 1(LLM)이 뽑은 검색어를 그 뒤에 붙인다. LLM 호출이 실패해도 항목 검색어는 남는다.
    돌려주는 값: {"item_query": ..., "llm_queries": [...], "queries": [...]}
    """
    item_query = item_search_query(item)
    llm_queries: list[str] = []

    model = model or get_llm()  # 키가 없으면 여기서 RuntimeError (호출하는 쪽에서 안내 문구로 바꾼다)
    try:
        response = model.invoke(build_query_messages(item_label(item), question, MAX_QUERIES))
        llm_queries = parse_query_list(response.content, MAX_QUERIES)
    except Exception:  # 네트워크 오류 등: 항목 검색어만으로 계속 진행한다. (오류 상세는 내보내지 않는다. NF2004)
        llm_queries = []

    queries = [item_query] + [q for q in llm_queries if q != item_query]
    return {"item_query": item_query, "llm_queries": llm_queries, "queries": queries}


# ── 수집 캐시와 문서 저장 (NF2002) ──────────────────────────────────
# 캐시 모양: { 키: {"date": "2026-10-22", "docs": [{"title": ..., "scope": ...}, ...]} }
#   키는 검색어 그대로, 또는 고정 문서는 "doc:범위:제목". 문서가 없어도 키는 남겨 같은 검색을 되풀이하지 않는다.
def _today() -> str:
    return date.today().isoformat()


def load_cache() -> dict:
    if not QUERY_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(QUERY_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict) -> None:
    QUERY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUERY_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _already_known(cache: dict, scope: str, title: str) -> bool:
    """같은 범위에 같은 제목의 문서를 이미 수집했는가."""
    return any(
        doc["scope"] == scope and doc["title"] == title
        for entry in cache.values()
        for doc in entry["docs"]
    )


def save_document(doc: dict) -> None:
    """본문을 파일로 저장한다. 파일 이름이 (범위, 문서 id) 로 정해져서 다시 저장해도 덮어쓰기만 된다."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / f"{doc['scope']}__{doc['doc_id']}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def load_saved_documents() -> list[dict]:
    """data/cache/docs/ 에 저장해 둔 문서를 모두 읽는다. 색인(5번 단계)이 이 목록을 쓴다."""
    docs = []
    for path in sorted(DOCS_DIR.glob("*.json")):
        try:
            docs.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue  # 깨진 파일 하나 때문에 전체가 멈추지 않게 한다
    return docs


# ── 위키 호출 ───────────────────────────────────────────────────────
def _fetch_document(title: str, scope: str, kind: str, query: str, item_id: str | None) -> dict | None:
    """문서 제목으로 본문과 원문 URL 을 받아 저장할 문서 정보로 만든다. 없는 문서면 None."""
    time.sleep(WIKI_SLEEP_SEC)  # 호출 사이에 쉰다 (NF2006)
    page = fetch_page(title)
    if page is None:
        return None
    return {
        "doc_id": f"wiki_{page['page_id']}",
        "title": page["title"],
        "url": page["url"],
        "text": page["text"],
        "source_type": "위키백과",
        "scope": scope,              # "common" 또는 항목 id
        "kind": kind,                # 공통 / 항목 / 선별
        "query": query,              # 이 문서를 찾게 한 검색어
        "related_item_id": item_id,  # 이 문서를 수집하게 만든 항목
        "collected_at": _today(),
    }


def _add_document(doc: dict, entry: dict, result: dict) -> None:
    save_document(doc)
    entry["docs"].append({"title": doc["title"], "scope": doc["scope"]})
    result["new_documents"].append(doc)


def _reuse(cache: dict, key: str, result: dict) -> None:
    for doc in cache[key]["docs"]:
        result["reused_titles"].append(doc["title"])


def _new_result() -> dict:
    return {
        "queries": [],          # 이번 질문의 최종 검색어
        "new_documents": [],    # 새로 수집해 저장한 문서
        "reused_titles": [],    # 이미 수집해 둬서 다시 받지 않은 문서
        "discarded_titles": [],  # 후보였지만 프롬프트 2가 고르지 않은 문서
        "skipped_short": [],    # 고른 문서 중 너무 짧아 제외한 문서
        "errors": 0,            # 호출 실패 횟수 (상세는 내보내지 않는다)
    }


# ── 고정 문서: 공통 개념 문서 + 항목의 해변 문서 ────────────────────
def load_seed_docs() -> list[dict]:
    """data/wiki_docs.json (위키 후보 문서 목록)."""
    try:
        return json.loads(WIKI_DOCS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def common_entries(seeds: list[dict]) -> list[tuple[str, str, str]]:
    return [(d["title"], COMMON_ITEM_ID, "공통") for d in seeds if d["kind"] == "개념 문서" and not d["item_ids"]]


def item_entries(seeds: list[dict], item_id: str) -> list[tuple[str, str, str]]:
    return [(d["title"], item_id, "항목") for d in seeds if d["kind"] == "해변 문서" and item_id in d["item_ids"]]


def _collect_fixed(entries, item_id, cache, result, say) -> None:
    """고정 문서는 선별도 길이 제한도 없이 항상 수집한다."""
    for title, scope, kind in entries:
        key = f"doc:{scope}:{title}"
        if key in cache:
            _reuse(cache, key, result)
            continue
        say(f"문서 수집 중: {title}")
        try:
            doc = _fetch_document(title, scope, kind, key, item_id)
        except Exception:
            result["errors"] += 1
            continue
        cache[key] = {"date": _today(), "docs": []}  # 없는 문서도 기록해 다시 찾지 않게 한다
        if doc:
            _add_document(doc, cache[key], result)
        save_cache(cache)


# ── 항목 자체를 다룬 문서 ───────────────────────────────────────────
def is_item_doc(item: dict, found: dict) -> bool:
    """검색 결과가 이 해변 자체를 다룬 문서인가. 제목에 해변 이름과 '해수욕장/해변'이 있고, 시군구가 제목이나 요약에 있어야 한다.
    (이름이 짧은 해변이 다른 지역 문서나 '송정동' 같은 동네 문서와 섞이는 것을 막는다)
    """
    title = found["title"]
    return (
        core_name(item["name"]) in title
        and region_keyword(item.get("region", "")) in title + found["snippet"]
        and any(word in title for word in ("해수욕장", "해변"))
    )


def _collect_item_docs(item, item_query, cache, result, say) -> None:
    """항목 검색어로 위키를 검색해, 이 해변 자체를 다룬 문서를 선별 없이 항상 수집한다. (F2004)"""
    if item_query in cache:
        _reuse(cache, item_query, result)
        return
    say(f"위키 검색 중: {item_query}")
    try:
        time.sleep(WIKI_SLEEP_SEC)
        found = search(item_query, limit=SEARCH_LIMIT)
    except Exception:
        result["errors"] += 1
        return

    entry = {"date": _today(), "docs": []}
    failed = False
    for candidate in [f for f in found if is_item_doc(item, f)][:MAX_ITEM_DOCS]:
        if _already_known(cache, item["id"], candidate["title"]):
            result["reused_titles"].append(candidate["title"])
            continue
        try:
            doc = _fetch_document(candidate["title"], item["id"], "항목", item_query, item["id"])
        except Exception:
            result["errors"] += 1
            failed = True
            continue
        if doc:
            _add_document(doc, entry, result)
    if not failed:  # 실패한 검색어는 캐시에 남기지 않아 다음에 다시 시도한다
        cache[item_query] = entry
        save_cache(cache)


# ── 질문에서 뽑은 검색어: 후보 → 선별(프롬프트 2) → 수집 ───────────
def _collect_selected_docs(item, question, llm_queries, model, cache, result, say) -> None:
    fresh = []
    for query in llm_queries:
        if query in cache:
            _reuse(cache, query, result)  # 이미 수집한 검색어는 다시 수집하지 않는다 (NF2002)
        else:
            fresh.append(query)
    if not fresh:
        return

    candidates: dict[str, dict] = {}
    searched: list[str] = []
    for query in fresh:
        say(f"위키 검색 중: {query}")
        try:
            time.sleep(WIKI_SLEEP_SEC)
            found = search(query, limit=SEARCH_LIMIT)
        except Exception:
            result["errors"] += 1
            continue
        searched.append(query)
        for page in found:
            if _already_known(cache, COMMON_ITEM_ID, page["title"]):
                result["reused_titles"].append(page["title"])
            elif page["title"] not in candidates:
                candidates[page["title"]] = {"title": page["title"], "snippet": page["snippet"], "query": query}

    pool = list(candidates.values())
    chosen: list[dict] = []
    if pool:
        say(f"후보 {len(pool)}건 중 색인할 문서를 고르는 중")
        try:
            response = model.invoke(build_select_messages(item_label(item), question, pool, MAX_SELECT_DOCS))
            picked = parse_index_list(response.content, len(pool), MAX_SELECT_DOCS)
        except Exception:
            result["errors"] += 1
            return  # 선별에 실패하면 캐시에 남기지 않아 다음에 다시 시도한다
        chosen = [pool[number - 1] for number in picked]
        result["discarded_titles"] = [c["title"] for c in pool if c not in chosen]

    entries = {query: {"date": _today(), "docs": []} for query in searched}
    failed_queries: set[str] = set()
    for candidate in chosen:
        say(f"문서 수집 중: {candidate['title']}")
        try:
            doc = _fetch_document(candidate["title"], COMMON_ITEM_ID, "선별", candidate["query"], item["id"])
        except Exception:
            result["errors"] += 1
            failed_queries.add(candidate["query"])
            continue
        if doc is None:
            continue
        if len(doc["text"]) < MIN_DOC_CHARS:  # 너무 짧은 문서(토막글 등)는 제외한다
            result["skipped_short"].append(doc["title"])
            continue
        _add_document(doc, entries[candidate["query"]], result)

    cache.update({q: e for q, e in entries.items() if q not in failed_queries})
    save_cache(cache)


# ── 전체 흐름 ───────────────────────────────────────────────────────
def collect_documents(item: dict, question: str, model=None, progress=None) -> dict:
    """질문 하나에 필요한 외부 문서를 수집한다. 이미 수집한 것은 다시 받지 않는다.

    순서: ① 고정 문서(공통 개념 + 이 해변의 해변 문서) → ② 검색어 추출 → ③ 이 해변 자체의 문서
          → ④ 질문에서 뽑은 검색어의 후보를 프롬프트 2로 선별해 수집
    progress 는 진행 상태를 문자열로 받는 함수다. (화면의 st.status 에 연결한다 — F2012)
    """
    say = progress or (lambda message: None)
    model = model or get_llm()
    cache = load_cache()
    result = _new_result()

    seeds = load_seed_docs()
    _collect_fixed(common_entries(seeds) + item_entries(seeds, item["id"]), item["id"], cache, result, say)

    extracted = extract_queries(item, question, model)
    result["queries"] = extracted["queries"]

    _collect_item_docs(item, extracted["item_query"], cache, result, say)
    _collect_selected_docs(item, question, extracted["llm_queries"], model, cache, result, say)

    save_cache(cache)
    return result


def collect_common_docs(progress=None) -> dict:
    """공통 개념 문서만 미리 수집한다. 첫 질문이 느려지지 않게 처음에 한 번 돌려 둔다."""
    say = progress or (lambda message: None)
    cache = load_cache()
    result = _new_result()
    _collect_fixed(common_entries(load_seed_docs()), None, cache, result, say)
    save_cache(cache)
    return result


# ── 터미널 실행 ─────────────────────────────────────────────────────
def _unique(titles: list[str]) -> list[str]:
    return list(dict.fromkeys(titles))


def _print_result(result: dict) -> None:
    print(f"\n[이미 수집되어 재사용] {len(_unique(result['reused_titles']))}건: {_unique(result['reused_titles'])}")
    print(f"[새로 수집] {len(result['new_documents'])}건")
    for doc in result["new_documents"]:
        print(f"  - ({doc['kind']}) {doc['title']}  {len(doc['text']):,}자  {doc['url']}")
    if result["discarded_titles"]:
        print(f"[후보 중 버려진 문서] {result['discarded_titles']}")
    if result["skipped_short"]:
        print(f"[너무 짧아 제외] {result['skipped_short']}")
    if result["errors"]:
        print(f"[확인 필요] 위키 또는 LLM 호출 실패 {result['errors']}건 — 네트워크, 키, WIKI_CONTACT 를 확인하세요.")


def main() -> None:
    load_dotenv()
    check_user_agent()

    if len(sys.argv) == 2 and sys.argv[1] == "--common":
        print("공통 개념 문서를 수집합니다...")
        _print_result(collect_common_docs(progress=print))
        return

    if len(sys.argv) < 3:
        print('사용법: python collector.py "해변 이름 일부" "질문"   또는   python collector.py --common')
        sys.exit(1)

    keyword, question = sys.argv[1], sys.argv[2]
    matches = [item for item in load_items() if keyword in item_label(item)]
    if not matches:
        print(f"'{keyword}' 이(가) 들어간 항목이 없습니다.")
        sys.exit(1)
    if len(matches) > 1:
        print(f"'{keyword}' 이(가) 들어간 항목이 {len(matches)}건입니다. 첫 번째를 사용합니다:")
        for item in matches[:5]:
            print("  -", item_label(item))

    item = matches[0]
    print(f"\n해변: {item_label(item)}")
    print(f"질문: {question}\n")
    try:
        result = collect_documents(item, question, progress=print)
    except RuntimeError as error:  # 키 누락 같은 예상한 오류
        print(f"[중단] {error}")
        sys.exit(1)

    print(f"\n최종 검색어: {result['queries']}")
    _print_result(result)


if __name__ == "__main__":
    main()