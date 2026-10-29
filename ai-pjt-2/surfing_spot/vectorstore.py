"""Chroma 컬렉션 열기와 색인. (F2002, 이후 F2005 문서 색인도 여기에 추가한다)

이 파일은 '저장소' 일만 한다.
    - 어떤 텍스트를 색인할지  → items.py
    - 어떻게 검색·병합할지    → retriever.py (6번 단계)
이렇게 나눠 두면 수집 · 색인 · 검색 · 생성 · UI 의 책임이 섞이지 않는다. (NF2005)
"""

import json
import os
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCS_COLLECTION,
    DOCS_DIR,
    EMBEDDING_MODEL,
    GMS_BASE_URL,
    META_COLLECTION,
    MIN_CHUNK_CHARS,
)
from items import build_item_text, load_items

BATCH_SIZE = 100  # 임베딩 요청을 한 번에 너무 많이 보내지 않도록 나눠서 색인한다.


def get_embeddings() -> OpenAIEmbeddings:
    """GMS 임베딩 클라이언트. 키가 없으면 안내 문구와 함께 RuntimeError 를 낸다."""
    key = os.environ.get("GMS_KEY")
    if not key:
        raise RuntimeError("GMS_KEY가 없습니다. .env를 확인하세요.")
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=key, base_url=GMS_BASE_URL)


def get_store(collection_name: str, with_embeddings: bool = True) -> Chroma:
    """컬렉션을 연다. 없으면 만든다. 건수만 셀 때는 임베딩(키)이 필요 없어 with_embeddings=False 로 연다."""
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings() if with_embeddings else None,
        persist_directory=str(CHROMA_DIR),
    )


def count_indexed(collection_name: str) -> int:
    """컬렉션에 저장된 청크 수. 컬렉션을 열지 못하면 0 을 돌려준다. (화면에 오류 추적 정보를 내보내지 않기 위함)"""
    try:
        return get_store(collection_name, with_embeddings=False)._collection.count()
    except Exception:
        return 0


def index_items(items: list[dict]) -> int:
    """항목 메타데이터를 surf_meta 컬렉션에 색인한다. 항목당 1청크.

    청크 id 를 항목 id 로 고정해서, 다시 실행해도 같은 항목은 덮어쓰기만 일어난다. (F2002)
    돌려주는 값은 색인이 끝난 뒤 컬렉션에 들어 있는 청크 수.
    """
    store = get_store(META_COLLECTION)
    for start in range(0, len(items), BATCH_SIZE):
        batch = items[start:start + BATCH_SIZE]
        documents = [
            Document(
                page_content=build_item_text(item),
                metadata={
                    "item_id": item["id"],
                    "name": item["name"],
                    "region": item["region"],
                    "type": item["type"],
                },
            )
            for item in batch
        ]
        store.add_documents(documents, ids=[item["id"] for item in batch])
    return count_indexed(META_COLLECTION)


# ── 위키 문서 청크 (F2005) ──────────────────────────────────────────
def load_saved_documents() -> list[dict]:
    """collector.py 가 data/cache/docs/ 에 저장해 둔 문서 본문을 모두 읽는다."""
    documents = []
    for path in sorted(DOCS_DIR.glob("*.json")):
        try:
            documents.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue  # 깨진 파일 하나 때문에 전체가 멈추지 않게 한다
    return documents

HEADING = re.compile(r"=+[^=\n]*=+")  # 위키 소제목: == 제목 ==, === 제목 ===

# 이 소제목이 나오면 그 뒤는 근거가 아니라 목록(참고문헌, 외부 링크 등)이다. 문서 끝에 모여 있으므로 거기서부터 잘라 낸다.
TAIL_SECTIONS = re.compile(r"\n={2,}\s*(참고\s*문헌|외부\s*링크|각주|주석|같이\s*보기|바깥\s*고리)\s*={2,}")


def strip_tail_sections(text: str) -> str:
    """문서 끝의 참고문헌·외부 링크 같은 목록 구역을 잘라 낸다. 그런 구역이 없으면 그대로 돌려준다."""
    found = TAIL_SECTIONS.search(text)
    return text[:found.start()] if found else text

def has_body(piece: str) -> bool:
    """소제목을 빼고 남은 본문이 MIN_CHUNK_CHARS 이상인 청크만 근거로 쓸 만하다고 본다.
    제목만 있는 청크("== 풍파와 물결 ==")나 참고문헌·외부 링크 목록은 근거 자리만 차지해서 색인하지 않는다.
    """
    return len(re.sub(r"\s", "", HEADING.sub("", piece))) >= MIN_CHUNK_CHARS

# ── 위키 문서 색인 (F2005) ──────────────────────────────────────────
def split_document(doc: dict, item_names: dict[str, str]) -> list[Document]:
    """문서 본문을 config 의 청크 크기·겹침으로 나누고, 청크마다 출처 정보를 함께 담는다.

    scope 는 검색 범위다. "common"(모든 항목이 공유) 또는 항목 id.
    (영화 예시의 '영화 ID' 필터에 해당한다. 6번 단계에서 '선택한 항목 id + common' 으로 검색한다)
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    related_id = doc.get("related_item_id") or ""  # Chroma 메타데이터에는 None 을 넣을 수 없다
    return [
        Document(
            page_content=piece,
            metadata={
                "scope": doc["scope"],
                "doc_id": doc["doc_id"],
                "doc_key": f"{doc['scope']}:{doc['doc_id']}",
                "title": doc["title"],
                "url": doc["url"],
                "source_type": doc.get("source_type", "위키백과"),
                "kind": doc.get("kind", ""),
                "query": doc.get("query", ""),
                "related_item_id": related_id,
                "related_item_name": item_names.get(related_id, ""),
                "collected_at": doc.get("collected_at", ""),
                "chunk_index": number,
            },
        )
        for number, piece in enumerate(splitter.split_text(strip_tail_sections(doc["text"])))
        if has_body(piece)  # chunk_index 는 자르기 전 순번 그대로 둔다 (청크 id 가 바뀌지 않게)
    ]


def index_documents(docs: list[dict]) -> list[tuple[str, int]]:
    """수집해 둔 문서를 청킹해서 surf_docs 컬렉션에 색인한다. 돌려주는 값: [(문서 제목, 청크 수), ...]

    청크 id 는 "범위:문서ID:순번" (예: common:wiki_123:0, spot_003:wiki_456:2).
    같은 문서를 다시 색인하면 그 문서의 기존 청크를 먼저 지운 뒤 넣는다.
    (청크 크기를 키워 청크 수가 줄었을 때 남는 옛 청크가 섞이지 않게 하려는 것)
    """
    store = get_store(DOCS_COLLECTION)
    item_names = {item["id"]: item["name"] for item in load_items()}
    summary = []
    for doc in docs:
        chunks = split_document(doc, item_names)
        old_ids = store.get(where={"doc_key": f"{doc['scope']}:{doc['doc_id']}"})["ids"]
        if old_ids:
            store.delete(ids=old_ids)
        ids = [f"{doc['scope']}:{doc['doc_id']}:{chunk.metadata['chunk_index']}" for chunk in chunks]
        for start in range(0, len(chunks), BATCH_SIZE):
            store.add_documents(chunks[start:start + BATCH_SIZE], ids=ids[start:start + BATCH_SIZE])
        summary.append((doc["title"], len(chunks)))
    return summary


def rebuild_docs_index() -> list[tuple[str, int]]:
    """surf_docs 를 비우고 저장된 문서 전체를 다시 색인한다. 청크 설정을 바꿔 비교할 때 쓴다."""
    docs = load_saved_documents()
    get_store(DOCS_COLLECTION, with_embeddings=False).delete_collection()
    return index_documents(docs)

def sync_docs_index() -> int:
    """저장된 문서 중 색인에 없는 것만 색인한다. 돌려주는 값은 새로 색인한 문서 수.

    chroma_db 를 지웠거나 색인이 어긋났을 때, 수집 캐시(data/cache/docs)가 남아 있으면 위키를 다시 부르지 않고 복구한다.
    """
    store = get_store(DOCS_COLLECTION, with_embeddings=False)
    indexed = {meta.get("doc_key") for meta in store.get(include=["metadatas"])["metadatas"]}
    missing = [d for d in load_saved_documents() if f"{d['scope']}:{d['doc_id']}" not in indexed]
    if missing:
        index_documents(missing)
    return len(missing)

def sync_meta_index(items: list[dict]) -> int:
    """항목 메타데이터 색인이 비었거나 모자라면 다시 채운다. 돌려주는 값은 색인한 항목 수. (같은 id 는 덮어쓰기)"""
    if count_indexed(META_COLLECTION) >= len(items):
        return 0
    index_items(items)
    return len(items)