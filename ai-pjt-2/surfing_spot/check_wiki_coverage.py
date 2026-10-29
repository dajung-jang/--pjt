"""항목마다 한국어 위키백과 문서가 잡히는지 확인한다.

준비:
    .env 에  WIKI_CONTACT=your-email@example.com
    (없으면 분당 10회로 제한되어 277건 확인에 30분 가까이 걸립니다)

실행:
    python check_wiki_coverage.py

결과:
    wiki_coverage.csv  — 항목별 검색 결과(검색어, 맨 위 문서, 조건에 맞는 문서)
    터미널에는 문서가 잡힌 항목 수 요약

판정 규칙: 검색 결과 중 '제목에 해변 이름이 들어 있고, 제목이나 요약에 시군구 이름이 들어 있는' 문서만 센다.
          이름이 짧은 해변(죽도, 송정 등)이 다른 지역 문서와 섞이는 것을 줄이기 위한 규칙이다.
          그래도 틀릴 수 있으니 csv 를 열어 눈으로 한 번 더 확인하세요.

참고: 이 스크립트는 '해변 자체를 다룬 문서'만 찾는다. 서핑 · 파도 · 이안류 같은 개념 문서는
      모든 항목에 공통으로 쓰므로 wiki_docs.json 에 따로 정리해 두었다.

wiki_client.py 의 search(), 호출 간격, User-Agent 규칙을 그대로 가져다 씁니다. (NF2006)
"""
import csv
import time

from config import DATA_DIR
from items import core_name, item_search_query, load_items, region_keyword
from wiki_client import check_user_agent, search

OUTPUT_PATH = DATA_DIR / "wiki_coverage.csv"


def main() -> None:
    check_user_agent()
    items = load_items()
    rows = []

    for number, item in enumerate(items, start=1):
        keyword = region_keyword(item.get("region", ""))
        query = item_search_query(item)  # collector.py 와 같은 검색어를 쓴다
        error = ""
        try:
            results = search(query, limit=5)
        except Exception as exc:  # 한 건 실패로 전체가 멈추지 않게 한다
            results = []
            error = type(exc).__name__

        core = core_name(item["name"])
        matched = [
            r for r in results
            if core in r["title"] and keyword in (r["title"] + r["snippet"])
        ]
        rows.append({
            "id": item["id"],
            "name": item["name"],
            "region": item.get("region", ""),
            "query": query,
            "top_title": results[0]["title"] if results else "",
            "matched_count": len(matched),
            "matched_titles": " | ".join(r["title"] for r in matched),
            "error": error,
        })
        print(f"[{number}/{len(items)}] {query} → 조건에 맞는 문서 {len(matched)}건")
        time.sleep(0.5)  # 호출 사이에 쉰다

    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    covered = sum(1 for r in rows if r["matched_count"] > 0)
    print(f"\n문서가 잡힌 항목: {covered}/{len(rows)}건  → 자세한 내용은 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()