#!/usr/bin/env python3
"""
Critical Minerals News Collector
주간 RSS 피드 수집 및 점수화 파이프라인

조성준 박사님 (KIGAM) - critical mineral exploration weekly digest
"""

import os
import json
import yaml
import hashlib
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

import feedparser
import requests

# ========== 설정 로드 ==========
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "sources.yaml"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


def fetch_feed(source: dict) -> list[dict]:
    """단일 RSS 피드를 파싱하여 기사 리스트 반환"""
    print(f"  → Fetching {source['name']}...")
    try:
        # User-Agent 설정 (일부 서버가 봇 차단)
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CriticalMineralsBot/1.0; "
                          "Academic research aggregator)"
        }
        # feedparser는 자체 fetch 사용. 필요 시 requests로 우회.
        parsed = feedparser.parse(source["url"], request_headers=headers)

        if parsed.bozo and not parsed.entries:
            print(f"    ⚠️  Parse failed: {parsed.bozo_exception}")
            return []

        articles = []
        for entry in parsed.entries[:30]:  # 소스당 최대 30개
            # 발행일 파싱 (여러 형식 대응)
            published = None
            for date_field in ["published_parsed", "updated_parsed"]:
                if hasattr(entry, date_field) and getattr(entry, date_field):
                    published = datetime(*getattr(entry, date_field)[:6],
                                         tzinfo=timezone.utc)
                    break
            if not published:
                published = datetime.now(timezone.utc)

            # 7일 이내만 수집
            if (datetime.now(timezone.utc) - published).days > 7:
                continue

            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary
            elif hasattr(entry, "description"):
                summary = entry.description

            # HTML 태그 제거 (간단)
            import re
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = summary[:500]  # 너무 길면 자르기

            articles.append({
                "title": entry.title.strip(),
                "url": entry.link,
                "source": source["name"],
                "tier_weight": source["tier_weight"],
                "summary_raw": summary,
                "published": published.isoformat(),
                "published_dt": published,  # 정렬용 (JSON 저장 전 제거)
            })
        print(f"    ✓ {len(articles)} articles within 7 days")
        return articles

    except Exception as e:
        print(f"    ✗ Error: {e}")
        return []


def score_article(article: dict) -> int:
    """기사 점수 계산"""
    text = (article["title"] + " " + article["summary_raw"]).lower()
    kw = CONFIG["keywords"]

    # 1. 핵심 광종 필터 (없으면 탈락)
    if not any(m.lower() in text for m in kw["critical_minerals"]):
        return 0

    score = article["tier_weight"]  # Tier 가중치 기본 점수

    # 2. 탐사 기술 키워드
    for keyword, weight in kw["exploration_tech"].items():
        if keyword.lower() in text:
            score += weight

    # 3. 정책·시장 키워드
    for keyword, weight in kw["policy_market"].items():
        if keyword.lower() in text:
            score += weight

    # 4. 최신성 보너스 (3일 이내 +2)
    age_days = (datetime.now(timezone.utc) - article["published_dt"]).days
    if age_days <= 3:
        score += 2

    return score


def deduplicate(articles: list[dict], threshold: float = 0.7) -> list[dict]:
    """제목 유사도 기반 중복 제거 (점수 높은 것 유지)"""
    articles = sorted(articles, key=lambda a: a["score"], reverse=True)
    unique = []
    for article in articles:
        is_dup = False
        for kept in unique:
            ratio = SequenceMatcher(
                None,
                article["title"].lower(),
                kept["title"].lower()
            ).ratio()
            if ratio > threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(article)
    return unique


def main():
    all_articles = []

    print("=" * 60)
    print("Critical Minerals News Collector")
    print(f"Run time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # 모든 tier 순회
    for tier_key in ["tier1_government", "tier2_industry", "tier3_search"]:
        print(f"\n[{tier_key}]")
        for source in CONFIG.get(tier_key, []):
            articles = fetch_feed(source)
            all_articles.extend(articles)

    print(f"\n총 수집: {len(all_articles)}개")

    # 점수 계산
    for a in all_articles:
        a["score"] = score_article(a)

    # 점수 임계값 필터
    threshold = CONFIG["publication"]["min_score_threshold"]
    filtered = [a for a in all_articles if a["score"] >= threshold]
    print(f"점수 ≥ {threshold} 통과: {len(filtered)}개")

    # 중복 제거
    deduped = deduplicate(
        filtered,
        threshold=CONFIG["publication"]["dedup_similarity_threshold"]
    )
    print(f"중복 제거 후: {len(deduped)}개")

    # 상위 N개만 선택
    max_cards = CONFIG["publication"]["max_cards_per_week"]
    top = deduped[:max_cards]
    print(f"최종 카드: {len(top)}개\n")

    # 정렬용 datetime 객체 제거 (JSON 직렬화 안됨)
    for a in top:
        a.pop("published_dt", None)
        # 고유 ID 부여
        a["id"] = hashlib.md5(a["url"].encode()).hexdigest()[:10]

    # 저장 (이번 주 raw 데이터)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw_path = DATA_DIR / f"raw-{today}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "week_of": today,
            "articles": top,
        }, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved: {raw_path}")
    print(f"  → 다음 단계: summarize.py 실행")


if __name__ == "__main__":
    main()
