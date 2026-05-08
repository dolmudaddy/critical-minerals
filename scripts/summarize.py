#!/usr/bin/env python3
"""
Claude API를 사용한 기사 요약 스크립트

각 기사에 대해 다음을 생성:
1. 한국어 3줄 요약 (발표용 문체)
2. 핵심 영어 표현 3개 (학회·국제회의 활용)
3. 자동 태그
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

# Claude Haiku 4.5 — 비용 효율적 (요약 작업에 충분)
MODEL = "claude-haiku-4-5-20251001"

PROMPT_TEMPLATE = """당신은 핵심광물(critical minerals) 분야의 전문 큐레이터입니다.
다음 영문 기사를 한국 자원공학 연구자(KIGAM 책임연구원, 한국자원공학회장)를 위한
주간 카드뉴스용으로 가공해 주십시오.

[번역 지침]
- "critical minerals" 또는 "critical raw materials"는 반드시 "핵심광물"로 번역
- "중요광물"이라는 표현은 사용하지 말 것
- "전략광물"도 가급적 "핵심광물"로 통일 (단, 원문이 strategic mineral인 경우는 전략광물 유지)
[기사 정보]
제목: {title}
출처: {source}
원문 요약: {summary}
URL: {url}

[작업]
정확히 다음 JSON 형식으로만 응답하십시오 (다른 텍스트 일절 금지):

{{
  "korean_summary": "발표용 문체로 작성한 한국어 3줄 요약. 핵심 사실·수치·함의를 포함. 각 줄은 마침표로 끝낼 것.",
  "english_phrases": [
    {{"phrase": "원문에서 추출한 학술·실무 영어 표현", "meaning": "한국어 의미"}},
    {{"phrase": "두 번째 표현", "meaning": "한국어 의미"}},
    {{"phrase": "세 번째 표현", "meaning": "한국어 의미"}}
  ],
  "tags": ["광종명", "기술/정책키워드", "지역/국가"],
  "category": "exploration_tech | policy_market | discovery | supply_chain | research 중 하나"
}}

[제약]
- korean_summary는 정중한 발표체로 ("~로 확인되었음", "~할 전망임" 등)
- english_phrases는 박사님이 국제 학회·회의에서 직접 사용 가능한 수준의 표현
- tags는 한국어로 3개 (예: ["리튬", "지구물리탐사", "칠레"])
"""


def summarize_article(client, article: dict) -> dict:
    """단일 기사 요약"""
    prompt = PROMPT_TEMPLATE.format(
        title=article["title"],
        source=article["source"],
        summary=article["summary_raw"][:1500],
        url=article["url"],
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # JSON만 추출 (혹시 코드블록 감싸여 있으면 제거)
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)
        return {
            **article,
            "korean_summary": result.get("korean_summary", ""),
            "english_phrases": result.get("english_phrases", []),
            "tags": result.get("tags", []),
            "category": result.get("category", "research"),
            "ai_processed": True,
        }
    except Exception as e:
        print(f"    ✗ Failed to summarize: {e}")
        return {
            **article,
            "korean_summary": "(요약 생성 실패 — 원문 참조)",
            "english_phrases": [],
            "tags": [],
            "category": "research",
            "ai_processed": False,
        }


def main():
    # 가장 최근 raw-*.json 파일 찾기
    raw_files = sorted(DATA_DIR.glob("raw-*.json"), reverse=True)
    if not raw_files:
        print("✗ No raw data file found. Run collect.py first.")
        return

    latest_raw = raw_files[0]
    print(f"Loading: {latest_raw}")

    with open(latest_raw, "r", encoding="utf-8") as f:
        data = json.load(f)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("✗ ANTHROPIC_API_KEY environment variable not set.")
        return

    client = anthropic.Anthropic(api_key=api_key)

    print(f"\nSummarizing {len(data['articles'])} articles with {MODEL}...")
    print("=" * 60)

    summarized = []
    for i, article in enumerate(data["articles"], 1):
        print(f"[{i}/{len(data['articles'])}] {article['title'][:60]}...")
        result = summarize_article(client, article)
        summarized.append(result)

    # 카테고리별 정렬 (정책 → 탐사기술 → 발견 → 공급망 → 연구)
    category_order = {
        "policy_market": 1,
        "exploration_tech": 2,
        "discovery": 3,
        "supply_chain": 4,
        "research": 5,
    }
    summarized.sort(
        key=lambda a: (category_order.get(a["category"], 9), -a["score"])
    )

    # 최종 결과 저장
    week_of = data["week_of"]
    output = {
        "week_of": week_of,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cards": len(summarized),
        "articles": summarized,
    }

    final_path = DATA_DIR / f"week-{week_of}.json"
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # latest.json도 갱신 (프론트엔드가 읽음)
    latest_path = DATA_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Saved: {final_path}")
    print(f"✓ Updated: {latest_path}")
    print(f"\n총 {len(summarized)}개 카드 생성 완료")


if __name__ == "__main__":
    main()
