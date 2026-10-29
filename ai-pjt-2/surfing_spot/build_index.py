"""항목 메타데이터를 임베딩해 Chroma 컬렉션(surf_meta)에 색인한다. (F2002)

실행:
    python build_index.py                  색인만 한다.
    python build_index.py "부산 송정"       색인한 뒤, 이 질문과 가장 비슷한 항목 3건을 보여 준다.
    python build_index.py --docs           수집해 둔 위키 문서를 청킹해서 surf_docs 컬렉션에 색인한다. (F2005)

확인할 것 (검증 4.1)
  1. 로드한 항목 수와 색인된 청크 수가 같은가
  2. 두 번 실행해도 청크 수가 늘지 않는가   ← 청크 id 를 항목 id 로 고정했기 때문
"""
import sys

from dotenv import load_dotenv

from collector import load_saved_documents
from config import CHUNK_OVERLAP, CHUNK_SIZE, DOCS_COLLECTION, META_COLLECTION
from items import load_items, validate_items
from vectorstore import count_indexed, get_store, index_documents, index_items


def main() -> None:
    load_dotenv()  # GMS_KEY 를 환경변수로 등록한다. 이 줄이 vectorstore 를 쓰기 전에 있어야 한다.

    items = load_items()
    problems = validate_items(items)
    if problems:
        print(f"[중단] 항목 데이터에 문제가 {len(problems)}건 있습니다. python items.py 로 확인하세요.")
        sys.exit(1)

    before = count_indexed(META_COLLECTION)
    print(f"로드한 항목: {len(items)}건 / 색인 전 청크: {before}건")

    try:
        after = index_items(items)
    except RuntimeError as error:  # 키 누락 같은 예상한 오류
        print(f"[중단] {error}")
        sys.exit(1)
    print(f"색인 후 청크: {after}건")

    if after == len(items):
        print("확인: 로드한 항목 수와 색인된 청크 수가 같습니다.")
    else:
        print("[확인 필요] 항목 수와 청크 수가 다릅니다.")

    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(f"\n\"{query}\" 와 가장 비슷한 항목:")
        for rank, doc in enumerate(get_store(META_COLLECTION).similarity_search(query, k=3), start=1):
            print(f"  {rank}. {doc.metadata['name']} ({doc.metadata['region']})")


def main_docs() -> None:
    """수집해 둔 위키 문서(data/cache/docs/)를 청킹해서 색인한다. (F2005)"""
    load_dotenv()

    docs = load_saved_documents()
    if not docs:
        print("저장된 문서가 없습니다. 먼저 python collector.py --common 으로 문서를 수집하세요.")
        sys.exit(1)

    before = count_indexed(DOCS_COLLECTION)
    print(f"저장된 문서: {len(docs)}건 / 청크 설정: {CHUNK_SIZE}자, 겹침 {CHUNK_OVERLAP}자 / 색인 전 청크: {before}건")

    try:
        summary = index_documents(docs)
    except RuntimeError as error:  # 키 누락 같은 예상한 오류
        print(f"[중단] {error}")
        sys.exit(1)

    for title, chunk_count in summary:
        print(f"  - {title}: {chunk_count}청크")
    print(f"색인 후 청크: {count_indexed(DOCS_COLLECTION)}건 (이번에 만든 청크 합계 {sum(n for _, n in summary)}건)")


if __name__ == "__main__":
    if "--docs" in sys.argv:
        main_docs()
    else:
        main()