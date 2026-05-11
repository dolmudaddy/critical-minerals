#!/usr/bin/env python3
"""
아카이브 인덱스 생성 스크립트

data/week-*.json 파일들을 스캔하여 archive-index.json을 생성합니다.
이 인덱스는 메인 페이지의 드롭다운과 archive.html의 목록에서 사용됩니다.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"


def main():
    if not DATA_DIR.exists():
        print("✗ data/ directory not found")
        return

    # week-YYYY-MM-DD.json 파일들 수집
    week_files = sorted(DATA_DIR.glob("week-*.json"), reverse=True)
    
    if not week_files:
        print("⚠️  No week-*.json files found")
        # 빈 인덱스 생성
        index = {"total_weeks": 0, "weeks": []}
        with open(DATA_DIR / "archive-index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        return

    weeks = []
    for week_file in week_files:
        # 파일명에서 날짜 추출: week-2026-05-10.json → 2026-05-10
        match = re.match(r"week-(\d{4}-\d{2}-\d{2})\.json", week_file.name)
        if not match:
            continue
        week_of = match.group(1)
        
        try:
            with open(week_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            articles = data.get("articles", [])
            
            # 카테고리별 카운트
            category_counts = {}
            for article in articles:
                cat = article.get("category", "research")
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # 주차의 대표 키워드 (상위 5개 태그)
            tag_counts = {}
            for article in articles:
                for tag in article.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
            
            weeks.append({
                "week_of": week_of,
                "filename": week_file.name,
                "total_cards": len(articles),
                "category_counts": category_counts,
                "top_tags": [tag for tag, _ in top_tags],
                "generated_at": data.get("generated_at", ""),
            })
            
        except Exception as e:
            print(f"  ⚠️  Failed to parse {week_file.name}: {e}")
            continue
    
    # 최신 호가 가장 위에 오도록 정렬 (이미 reverse=True지만 명시적으로)
    weeks.sort(key=lambda w: w["week_of"], reverse=True)
    
    index = {
        "total_weeks": len(weeks),
        "latest_week": weeks[0]["week_of"] if weeks else None,
        "weeks": weeks,
    }
    
    output_path = DATA_DIR / "archive-index.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Generated: {output_path}")
    print(f"  → {len(weeks)} weeks indexed")
    for w in weeks[:5]:
        print(f"    - {w['week_of']}: {w['total_cards']} cards")
    if len(weeks) > 5:
        print(f"    ... and {len(weeks) - 5} more")


if __name__ == "__main__":
    main()
