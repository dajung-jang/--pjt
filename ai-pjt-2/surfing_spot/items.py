"""서핑 항목 데이터 로드 · 검증 · 색인 텍스트 구성 (F2001)

실행:
    python items.py

확인할 것 (검증 4.1)
  - 항목이 몇 건 로드되는가
  - 필수 항목이 비어 있거나 id가 겹치는 곳은 없는가
  - 항목 1건의 색인 텍스트에 의도한 속성이 모두 들어갔는가
"""
import json
from pathlib import Path

from config import ITEMS_PATH

DATA_PATH = ITEMS_PATH  # 경로는 config.py 에서 한 곳으로 관리한다

# 비어 있으면 안 되는 필드. source / license 는 NF2007(출처와 이용 조건 기록) 때문에 필수다.
REQUIRED_FIELDS = ["id", "name", "region", "source", "license"]

# 색인 텍스트에 넣을 속성과 라벨 (순서대로 이어 붙인다)
TEXT_FIELDS = [
    ("name", "이름"),
    ("region", "지역"),
    ("type", "유형"),
    ("size", "규모"),
    ("level", "난이도"),
    ("features", "특징"),
    ("cautions", "주의사항"),
]


def load_items(path: Path = DATA_PATH) -> list[dict]:
    """JSON 파일에서 항목 목록을 읽는다."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_items(items: list[dict]) -> list[str]:
    """문제가 있는 곳을 문장 목록으로 돌려준다. 문제가 없으면 빈 목록."""
    problems = []
    seen_ids = set()
    for number, item in enumerate(items, start=1):
        label = f"{number}번째 항목({item.get('name', '?')})"
        for key in REQUIRED_FIELDS:
            if not str(item.get(key, "")).strip():
                problems.append(f"{label}: '{key}' 가 비어 있습니다.")
        item_id = item.get("id")
        if item_id in seen_ids:
            problems.append(f"{label}: id '{item_id}' 가 중복입니다.")
        seen_ids.add(item_id)
    return problems


def build_item_text(item: dict) -> str:
    """항목 1건을 검색에 쓸 하나의 텍스트로 만든다. 비어 있는 속성은 넣지 않는다."""
    parts = []
    for key, label in TEXT_FIELDS:
        value = str(item.get(key, "")).strip()
        if value:
            parts.append(f"{label}: {value}")
    return " / ".join(parts)


def item_label(item: dict) -> str:
    """사이드바 selectbox 에 보일 이름. 예) 죽도해변 (강원 양양)"""
    return f"{item['name']} ({item['region']})"


NAME_SUFFIXES = ["해수욕장", "해변", "비치", "포구", "항"]
REGION_SUFFIXES = ["특별자치시", "특별자치도", "광역시", "시", "군", "구"]


def core_name(name: str) -> str:
    """'죽도해변' → '죽도' 처럼 흔한 꼬리말을 떼어 비교용 이름을 만든다."""
    for suffix in NAME_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name


def region_keyword(region: str) -> str:
    """'강원도 양양군' → '양양' 처럼 시군구의 알맹이만 뽑는다. 검색어와 비교용이라 꼬리말을 뗀다."""
    last = region.split()[-1] if region.split() else ""
    for suffix in REGION_SUFFIXES:
        if last.endswith(suffix) and len(last) > len(suffix) + 1:
            return last[: -len(suffix)]
    return last


def item_search_query(item: dict) -> str:
    """항목 자체를 다룬 위키 문서를 찾는 검색어. 이름이 짧은 해변(송정, 인구)이 섞이지 않도록 시군구를 붙인다.
    예) 죽도 (강원도 양양군) → '양양 죽도 해수욕장'
    """
    return f"{region_keyword(item.get('region', ''))} {item['name']} 해수욕장".strip()


if __name__ == "__main__":
    items = load_items()
    print(f"로드한 항목 수: {len(items)}건")

    problems = validate_items(items)
    if problems:
        print(f"\n[확인 필요] {len(problems)}건")
        for line in problems[:15]:
            print(" -", line)
        if len(problems) > 15:
            print(f" ... 외 {len(problems) - 15}건")
    else:
        print("검증 통과: 필수 항목 누락과 id 중복이 없습니다.")

    if items:
        print("\n[색인 텍스트 예시 — 첫 번째 항목]")
        print(build_item_text(items[0]))