#!/usr/bin/env python3
"""
RSS 2.0 피드 생성 스크립트

data/latest.json을 읽어서 rss.xml을 생성합니다.
Feedly, Inoreader 등 표준 RSS 리더에서 구독 가능합니다.
"""

import json
import html
from datetime import datetime, timezone
from pathlib import Path
from email.utils import format_datetime

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
SITE_URL = "https://dolmudaddy.github.io/critical-minerals"


def escape_xml(text: str) -> str:
    """XML 특수문자 이스케이프"""
    if not text:
        return ""
    return html.escape(text, quote=False)


def main():
    latest_path = DATA_DIR / "latest.json"
    if not latest_path.exists():
        print("✗ latest.json not found.")
        return

    with open(latest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    week_of = data.get("week_of", "")
    articles = data.get("articles", [])
    now = datetime.now(timezone.utc)

    # RSS 2.0 표준 형식
    items = []
    for article in articles:
        title = escape_xml(article.get("title", ""))
        url = article.get("url", "")
        source = escape_xml(article.get("source", ""))
        korean_summary = escape_xml(article.get("korean_summary", ""))
        tags = article.get("tags", [])
        article_id = article.get("id", "")

        # 발행일 파싱
        try:
            pub_dt = datetime.fromisoformat(
                article.get("published", "").replace("Z", "+00:00")
            )
        except Exception:
            pub_dt = now
        pub_date_rss = format_datetime(pub_dt)

        # 카테고리 태그
        category_tags = "\n      ".join(
            f"<category>{escape_xml(t)}</category>" for t in tags
        )

        # 본문(description) — 한국어 요약 + 영어 표현 + 출처
        desc_parts = [f"<p><strong>출처</strong>: {source}</p>"]
        if korean_summary:
            desc_parts.append(f"<p>{korean_summary}</p>")
        
        phrases = article.get("english_phrases", [])
        if phrases:
            phrase_html = "<p><strong>핵심 영어 표현</strong></p><ul>"
            for p in phrases:
                ph = escape_xml(p.get("phrase", ""))
                mn = escape_xml(p.get("meaning", ""))
                phrase_html += f"<li><em>{ph}</em> — {mn}</li>"
            phrase_html += "</ul>"
            desc_parts.append(phrase_html)

        description = escape_xml("".join(desc_parts))

        items.append(f"""    <item>
      <title>{title}</title>
      <link>{url}</link>
      <guid isPermaLink="false">{article_id}</guid>
      <pubDate>{pub_date_rss}</pubDate>
      <source url="{SITE_URL}">{source}</source>
      {category_tags}
      <description>{description}</description>
    </item>""")

    items_xml = "\n".join(items)
    last_build = format_datetime(now)

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>핵심광물 주간 동향 (Critical Minerals Weekly)</title>
    <link>{SITE_URL}/</link>
    <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>
    <description>조성준 박사 (KIGAM, 한국자원공학회장) 큐레이션. 핵심광물 탐사·정책·시장 주간 동향.</description>
    <language>ko-KR</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <generator>GitHub Actions + Claude API</generator>
    <managingEditor>dolmudaddy@gmail.com (조성준)</managingEditor>
{items_xml}
  </channel>
</rss>
"""

    rss_path = ROOT / "rss.xml"
    with open(rss_path, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"✓ Generated: {rss_path}")
    print(f"  → {len(articles)} items, week of {week_of}")


if __name__ == "__main__":
    main()
