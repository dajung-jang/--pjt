"""수집해 둔 위키 문서(data/cache/docs/)를 청킹해서 surf_docs 컬렉션에 색인한다. (F2005)

실행:
    python build_docs_index.py                 저장된 문서를 전부 다시 색인한다.
    python build_docs_index.py "이안류 대처"     색인한 뒤, 이 질문과 가장 비슷한 청크 3건을 보여 준다.
"""
import sys

from dotenv import load_dotenv

from config import CHUNK_OVERLAP, CHUNK_SIZE, DOCS_COLLECTION
from vectorstore import count_indexed, get_store, load_saved_documents, rebuild_docs_index


def main() -> None:
    load_dotenv()

    documents = load_saved_documents()
    if not documents:
        print("[중단] 수집해 둔 문서가 없습니다. 먼저 python collector.py --common 을 실행하세요.")
        sys.exit(1)

    print(f"저장된 문서: {len(documents)}건")
    print(f"설정: 청크 {CHUNK_SIZE}자, 중복 {CHUNK_OVERLAP}자")
    print(f"색인 전 청크: {count_indexed(DOCS_COLLECTION)}건")

    try:
        summary = rebuild_docs_index()
    except RuntimeError as error:  # 키 누락 같은 예상한 오류
        print(f"[중단] {error}")
        sys.exit(1)

    print(f"색인 후 청크: {count_indexed(DOCS_COLLECTION)}건\n")
    for doc, (title, chunks) in zip(documents, summary):
        print(f"  - [{doc['scope']}] {title}: 본문 {len(doc['text']):,}자 → 청크 {chunks}건")

    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(f"\n\"{query}\" 와 가장 비슷한 청크:")
        for rank, found in enumerate(get_store(DOCS_COLLECTION).similarity_search(query, k=3), start=1):
            meta = found.metadata
            preview = found.page_content[:60].replace("\n", " ")
            print(f"  {rank}. {meta['title']} (범위 {meta['scope']}, 청크 {meta['chunk_index']}) {preview}...")


if __name__ == "__main__":
    main()