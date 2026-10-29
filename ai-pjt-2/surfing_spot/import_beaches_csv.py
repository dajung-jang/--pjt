"""공공데이터포털에서 받은 해수욕장 CSV 를 surf_items.json 에 합친다.

실행 예 (해양수산부_해수욕장정보목록):
    python import_beaches_csv.py data/raw/beaches.csv --name-col 해수욕장명 --region-col 지자체,관리청 \
        --length-col "길이(m)" --width-col "너비(m)" --area-col "백사장면적(m2)" \
        --source "공공데이터포털 해양수산부_해수욕장정보목록 (수정일 2025-07-31)" \
        --license "이용허락범위 제한 없음"

옵션
    --name-col     해수욕장 이름이 들어 있는 열 이름 (CSV 첫 줄에서 확인)
    --region-col   지역 열 이름. 여러 개면 쉼표로 이어 쓴다 (공백으로 붙여서 지역 문자열을 만든다)
    --length-col / --width-col / --area-col   (선택) 규모 열 이름. 있으면 '규모' 속성으로 저장한다.
    --source       출처 이름 또는 URL (NF2007)
    --license      이용 조건 (NF2007)

동작
    - 항목은 (이름, 지역) 한 쌍으로 구분한다. 이름만 같고 지역이 다른 해변(예: 송정)은 따로 저장된다.
    - 이미 있는 항목은 새로 만들지 않고, 비어 있는 규모 · 출처 · 이용 조건만 채운다.
      (직접 정리한 서핑 속성을 덮어쓰지 않는다. 몇 번 다시 실행해도 항목이 늘지 않는다.)
    - 새 항목은 id 를 beach_001, beach_002 ... 로 붙인다. 한 번 정한 id 는 바꾸지 마세요. (F2002 덮어쓰기)
    - 서핑 속성(level, features, cautions)은 비워 둔다. 출처로 확인된 내용만 직접 채우세요.
"""
import argparse
import csv
import json

from items import DATA_PATH, load_items


def read_csv_rows(path: str) -> list[dict]:
    """공공데이터 CSV 는 cp949 인 경우가 많아 두 가지 인코딩을 차례로 시도한다."""
    for encoding in ("utf-8-sig", "cp949"):
        try:
            with open(path, encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit("CSV 인코딩을 읽지 못했습니다. 파일을 UTF-8 로 저장해서 다시 시도하세요.")


def format_number(text: str) -> str:
    """'16200' → '16,200'. 숫자가 아니면 그대로 돌려준다."""
    text = (text or "").strip()
    try:
        return f"{int(float(text)):,}"
    except ValueError:
        return text


def build_size(row: dict, args) -> str:
    """길이 · 너비 · 백사장면적 열이 지정된 경우에만 '규모' 문장을 만든다."""
    parts = []
    if args.length_col and (row.get(args.length_col) or "").strip():
        parts.append(f"길이 {format_number(row[args.length_col])}m")
    if args.width_col and (row.get(args.width_col) or "").strip():
        parts.append(f"너비 {format_number(row[args.width_col])}m")
    if args.area_col and (row.get(args.area_col) or "").strip():
        parts.append(f"백사장면적 {format_number(row[args.area_col])}㎡")
    return " · ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--name-col", required=True)
    parser.add_argument("--region-col", required=True)
    parser.add_argument("--length-col")
    parser.add_argument("--width-col")
    parser.add_argument("--area-col")
    parser.add_argument("--source", required=True)
    parser.add_argument("--license", required=True)
    args = parser.parse_args()

    rows = read_csv_rows(args.csv_path)
    if not rows:
        raise SystemExit("CSV 에 데이터가 없습니다.")

    columns = list(rows[0].keys())
    region_cols = [c.strip() for c in args.region_col.split(",")]
    optional = [c for c in (args.length_col, args.width_col, args.area_col) if c]
    for col in [args.name_col, *region_cols, *optional]:
        if col not in columns:
            raise SystemExit(f"열 '{col}' 이 없습니다. CSV 의 열 이름: {columns}")

    items = load_items() if DATA_PATH.exists() else []
    by_key = {(item["name"], item["region"]): item for item in items}
    next_number = sum(1 for item in items if item["id"].startswith("beach_")) + 1
    added = 0
    updated = 0

    for row in rows:
        name = (row.get(args.name_col) or "").strip()
        if not name:
            continue
        region = " ".join((row.get(c) or "").strip() for c in region_cols).strip()
        size = build_size(row, args)
        key = (name, region)

        if key in by_key:
            item = by_key[key]
            changed = False
            for field, value in (("size", size), ("source", args.source), ("license", args.license)):
                if value and not str(item.get(field, "")).strip():
                    item[field] = value
                    changed = True
            updated += 1 if changed else 0
            continue

        item = {
            "id": f"beach_{next_number:03d}",
            "name": name,
            "region": region,
            "type": "해수욕장",
            "size": size,
            "level": "",
            "features": "",
            "cautions": "",
            "source": args.source,
            "license": args.license,
        }
        items.append(item)
        by_key[key] = item
        next_number += 1
        added += 1

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"CSV {len(rows)}행 → 새로 추가 {added}건, 기존 항목 보완 {updated}건, 전체 {len(items)}건 ({DATA_PATH.name})")


if __name__ == "__main__":
    main()
