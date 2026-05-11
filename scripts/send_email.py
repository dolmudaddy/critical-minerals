"""
send_email.py
Critical Minerals Weekly 카드뉴스를 Mailchimp Campaign으로 자동 발송.

워크플로우:
1. data/latest.json 로드
2. HTML 메일 본문 생성 (사이트 디자인과 동일한 자홍색 톤·카드 형태)
3. Mailchimp API 호출: Campaign 생성 → 본문 주입 → 즉시 발송

환경 변수:
- MAILCHIMP_API_KEY (필수): Mailchimp API 키. 끝의 -us13 부분이 서버 prefix.
- MAILCHIMP_AUDIENCE_ID (필수): Audience ID. 기본값은 코드에 박혀있음.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import html as html_lib

import requests

# ───────── 설정 ─────────
LATEST_JSON = Path("data/latest.json")
SITE_URL = "https://dolmudaddy.github.io/critical-minerals/"
ARCHIVE_URL = "https://dolmudaddy.github.io/critical-minerals/archive.html"
FROM_NAME = "조성준 (KIGAM)"
REPLY_TO = "mac@kigam.re.kr"  # 박사님 KIGAM 메일

AUDIENCE_ID_DEFAULT = "0592005ac7"

# 카테고리 한글 라벨
CATEGORY_LABEL = {
    "policy_market": "정책·시장",
    "exploration_tech": "탐사기술",
    "discovery": "발견·매장지",
    "supply_chain": "공급망",
    "research": "연구",
}

# Tier 라벨 (index.html과 동일한 매핑)
TIER_LABEL = {
    5: "Tier 1 · Government",
    4: "Tier 2 · Academic",
    3: "Tier 2 · Industry",
    1: "Tier 3 · News Search",
}
TIER_COLOR = {
    5: "#2d5a3d",
    4: "#1f4e79",
    3: "#1f4e79",
    1: "#6b6b6b",
}

# 사이트 색상·폰트 토큰
ACCENT = "#8b2332"
ACCENT_LIGHT = "#f5e8ea"
BG = "#f7f6f2"
PAPER = "#ffffff"
INK = "#1a1a1a"
MUTED = "#6b6b6b"
BORDER = "#e0ddd5"


def esc(s):
    """HTML 이스케이프. None 안전."""
    if s is None:
        return ""
    return html_lib.escape(str(s), quote=True)


def format_date_ko(iso_str):
    """ISO 날짜를 한국식 짧은 형식으로."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y.%m.%d")
    except Exception:
        return iso_str[:10] if iso_str else ""


def build_card_html(article):
    """카드 1개의 HTML을 생성. 인라인 CSS 사용 (네이버 메일, 다음 메일 호환)."""
    tier = article.get("tier_weight", 1)
    tier_label = TIER_LABEL.get(tier, "Source")
    tier_color = TIER_COLOR.get(tier, MUTED)

    category = article.get("category", "")
    category_label = CATEGORY_LABEL.get(category, "")

    title = esc(article.get("title", "(제목 없음)"))
    source = esc(article.get("source", ""))
    url = article.get("url", "#")
    korean_summary = esc(article.get("korean_summary", ""))
    date_str = format_date_ko(article.get("published", ""))

    # 영어 표현 (최대 3개만 보여서 메일 길이 적정 유지)
    phrases = article.get("english_phrases", []) or []
    phrases_html = ""
    if phrases:
        items = []
        for p in phrases[:3]:
            phrase = esc(p.get("phrase", ""))
            meaning = esc(p.get("meaning", ""))
            items.append(
                f'<div style="margin-bottom:6px;font-size:13px;line-height:1.5;">'
                f'<span style="font-weight:500;color:{INK};">"{phrase}"</span>'
                f'<span style="color:{MUTED};margin-left:6px;">— {meaning}</span>'
                f"</div>"
            )
        phrases_html = (
            f'<div style="background:{ACCENT_LIGHT};border-radius:4px;'
            f'padding:12px 14px;margin:14px 0;">'
            f'<div style="font-size:11px;font-weight:600;color:{ACCENT};'
            f'letter-spacing:0.05em;text-transform:uppercase;margin-bottom:8px;">'
            f"📚 영어 표현</div>"
            f"{''.join(items)}"
            f"</div>"
        )

    # 태그
    tags = article.get("tags", []) or []
    tags_html = ""
    if tags:
        tag_spans = "".join(
            f'<span style="display:inline-block;font-size:11px;'
            f'background:#f0ede4;color:#555;padding:2px 8px;'
            f'border-radius:3px;margin-right:6px;margin-bottom:4px;">'
            f"#{esc(t)}</span>"
            for t in tags
        )
        tags_html = f'<div style="margin:10px 0 14px;">{tag_spans}</div>'

    # 카테고리 배지 (오른쪽 상단)
    category_badge = ""
    if category_label:
        category_badge = (
            f'<span style="font-size:11px;color:{MUTED};">{esc(category_label)}</span>'
        )

    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="background:{PAPER};border:1px solid {BORDER};border-radius:6px;
              margin-bottom:20px;border-collapse:separate;">
  <tr>
    <td style="padding:12px 18px;border-bottom:1px solid {BORDER};">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr>
          <td align="left" style="font-size:12px;font-weight:600;
                                   color:{tier_color};letter-spacing:0.05em;
                                   text-transform:uppercase;">
            {esc(tier_label)}
          </td>
          <td align="right" style="font-size:12px;color:{MUTED};">
            {category_badge}{' · ' if category_badge else ''}{esc(date_str)}
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td style="padding:18px 20px;">
      <div style="font-size:11px;color:{MUTED};letter-spacing:0.03em;
                  text-transform:uppercase;margin-bottom:6px;">{source}</div>
      <h2 style="font-family:Arial,sans-serif;font-size:17px;font-weight:600;
                 line-height:1.35;margin:0 0 12px;color:{INK};">{title}</h2>
      <div style="font-size:14px;color:#333;line-height:1.7;margin-bottom:14px;">
        {korean_summary}
      </div>
      {phrases_html}
      {tags_html}
      <div style="padding-top:12px;border-top:1px solid {BORDER};">
        <a href="{esc(url)}" target="_blank"
           style="display:inline-block;background:{ACCENT};color:#ffffff;
                  font-size:13px;font-weight:600;padding:8px 16px;
                  text-decoration:none;border-radius:4px;">원문 보기 →</a>
      </div>
    </td>
  </tr>
</table>
"""


def build_email_html(data):
    """전체 메일 HTML 구성."""
    week_of = data.get("week_of", "")
    total = data.get("total_cards", 0)
    articles = data.get("articles", []) or []

    cards_html = "\n".join(build_card_html(a) for a in articles)

    # 발송일 표시 (한국식)
    try:
        dt = datetime.fromisoformat(week_of) if week_of else datetime.utcnow()
        week_display = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        week_display = week_of

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Critical Minerals Weekly</title>
</head>
<body style="margin:0;padding:0;background:{BG};
             font-family:Arial,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
             color:{INK};line-height:1.6;">

<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
       style="background:{BG};">
  <tr>
    <td align="center" style="padding:0;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"
             width="640" style="max-width:640px;width:100%;">

        <!-- 헤더 -->
        <tr>
          <td style="background:{PAPER};border:1px solid {BORDER};
                     border-radius:6px 6px 0 0;padding:32px 24px 28px;
                     text-align:center;">
            <h1 style="font-size:28px;font-weight:700;letter-spacing:-0.02em;
                       margin:0 0 6px;color:{ACCENT};">Critical Minerals Weekly</h1>
            <div style="font-size:13px;color:{MUTED};letter-spacing:0.05em;
                        text-transform:uppercase;">
              핵심광물 탐사·정책 주간 동향
            </div>
            <div style="margin-top:14px;font-size:14px;color:{MUTED};">
              <strong style="color:{INK};font-weight:600;">{esc(week_display)}</strong>
              · <strong style="color:{INK};font-weight:600;">{total}건</strong>
              · Curated by 조성준 (KIGAM)
            </div>
          </td>
        </tr>

        <!-- 인사말 -->
        <tr>
          <td style="background:{PAPER};border-left:1px solid {BORDER};
                     border-right:1px solid {BORDER};padding:20px 24px;
                     font-size:14px;color:#333;line-height:1.7;">
            안녕하세요. 이번 주 핵심광물 분야에서 주목할 만한 동향
            <strong>{total}건</strong>을 정리해 드립니다.
            정부·국제기구 발표, 학술 연구, 산업 뉴스를 종합 분석한 결과이며,
            각 카드에는 한국어 요약과 함께 학회·국제회의에서 활용 가능한
            영어 표현을 포함하였습니다.
          </td>
        </tr>

        <!-- 카드 영역 -->
        <tr>
          <td style="background:{BG};padding:20px 16px;
                     border-left:1px solid {BORDER};border-right:1px solid {BORDER};">
            {cards_html}
          </td>
        </tr>

        <!-- 사이트 안내 -->
        <tr>
          <td style="background:{PAPER};border-left:1px solid {BORDER};
                     border-right:1px solid {BORDER};padding:24px;text-align:center;">
            <a href="{SITE_URL}" target="_blank"
               style="display:inline-block;background:{ACCENT};color:#ffffff;
                      font-size:14px;font-weight:600;padding:10px 24px;
                      text-decoration:none;border-radius:4px;margin:4px;">
              📰 사이트에서 전체 보기
            </a>
            <a href="{ARCHIVE_URL}" target="_blank"
               style="display:inline-block;background:{PAPER};color:{ACCENT};
                      font-size:14px;font-weight:600;padding:10px 24px;
                      text-decoration:none;border:1px solid {ACCENT};
                      border-radius:4px;margin:4px;">
              📚 지난 호 아카이브
            </a>
          </td>
        </tr>

        <!-- 푸터 -->
        <tr>
          <td style="background:{PAPER};border:1px solid {BORDER};
                     border-top:none;border-radius:0 0 6px 6px;
                     padding:20px 24px;text-align:center;
                     font-size:11px;color:{MUTED};line-height:1.6;">
            본 뉴스레터는 한국지질자원연구원(KIGAM) 조성준 박사가
            큐레이션하는 비공식 학술 정보 서비스입니다.<br>
            문의: <a href="mailto:{REPLY_TO}"
                    style="color:{ACCENT};text-decoration:none;">{REPLY_TO}</a>
            · <a href="{SITE_URL}" target="_blank"
                 style="color:{ACCENT};text-decoration:none;">{SITE_URL}</a>
            <br><br>
            <span style="color:{MUTED};">
              수신을 원치 않으시면 <a href="*|UNSUB|*"
              style="color:{MUTED};text-decoration:underline;">여기를 클릭</a>해 주십시오.
            </span><br>
            <span style="color:{MUTED};font-size:10px;">*|LIST:ADDRESSLINE|*</span>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>

</body>
</html>
"""


def build_plain_text(data):
    """텍스트 버전 (HTML 표시 안 되는 메일 클라이언트용)."""
    week_of = data.get("week_of", "")
    total = data.get("total_cards", 0)
    articles = data.get("articles", []) or []

    lines = [
        "Critical Minerals Weekly",
        "핵심광물 탐사·정책 주간 동향",
        f"{week_of} | {total}건 | Curated by 조성준 (KIGAM)",
        "",
        "═" * 50,
        "",
    ]
    for i, a in enumerate(articles, 1):
        lines.append(f"[{i}] {a.get('title', '')}")
        lines.append(f"    출처: {a.get('source', '')} | {format_date_ko(a.get('published', ''))}")
        lines.append("")
        lines.append(f"    {a.get('korean_summary', '')}")
        lines.append("")
        lines.append(f"    원문: {a.get('url', '')}")
        lines.append("")
        lines.append("─" * 50)
        lines.append("")
    lines.append(f"사이트: {SITE_URL}")
    lines.append(f"아카이브: {ARCHIVE_URL}")
    lines.append(f"문의: {REPLY_TO}")
    lines.append("")
    lines.append("수신을 원치 않으시면 다음 링크를 클릭해 주십시오: *|UNSUB|*")
    return "\n".join(lines)


def get_server_prefix(api_key):
    """API 키 끝의 -us13 같은 부분을 추출."""
    if "-" not in api_key:
        raise ValueError(
            "MAILCHIMP_API_KEY에 서버 prefix(-us13 등)가 없습니다. "
            "전체 키를 정확히 등록했는지 확인하십시오."
        )
    return api_key.rsplit("-", 1)[1]


def mailchimp_request(method, path, api_key, server, json_body=None):
    """Mailchimp API 호출 헬퍼."""
    url = f"https://{server}.api.mailchimp.com/3.0{path}"
    resp = requests.request(
        method,
        url,
        auth=("anystring", api_key),
        json=json_body,
        timeout=30,
    )
    if resp.status_code >= 400:
        sys.stderr.write(
            f"[Mailchimp API 오류] {method} {path}: "
            f"{resp.status_code}\n{resp.text}\n"
        )
        resp.raise_for_status()
    return resp.json() if resp.text else {}


def send_campaign(data, api_key, audience_id):
    """Mailchimp Campaign을 생성하고 즉시 발송."""
    server = get_server_prefix(api_key)
    week_of = data.get("week_of", "")
    total = data.get("total_cards", 0)

    subject = f"핵심광물 주간 동향 | {week_of} ({total}개 동향)"
    preview = f"{week_of} 주의 정책·탐사·시장 동향 {total}건 — KIGAM 조성준"

    # 1) Campaign 생성
    print(f"[1/3] Campaign 생성 중... (subject: {subject})")
    campaign = mailchimp_request(
        "POST",
        "/campaigns",
        api_key,
        server,
        json_body={
            "type": "regular",
            "recipients": {"list_id": audience_id},
            "settings": {
                "subject_line": subject,
                "preview_text": preview,
                "title": f"CMW {week_of}",  # 내부 관리용 제목
                "from_name": FROM_NAME,
                "reply_to": REPLY_TO,
                "to_name": "*|FNAME|*",
                "auto_footer": False,
                "inline_css": True,
            },
        },
    )
    campaign_id = campaign["id"]
    print(f"      → Campaign ID: {campaign_id}")

    # 2) HTML 본문 주입
    print("[2/3] HTML 본문 주입 중...")
    html_body = build_email_html(data)
    text_body = build_plain_text(data)
    mailchimp_request(
        "PUT",
        f"/campaigns/{campaign_id}/content",
        api_key,
        server,
        json_body={
            "html": html_body,
            "plain_text": text_body,
        },
    )
    print(f"      → 본문 크기: {len(html_body):,} bytes")

    # 3) 즉시 발송
    print("[3/3] 발송 요청 중...")
    mailchimp_request(
        "POST",
        f"/campaigns/{campaign_id}/actions/send",
        api_key,
        server,
    )
    print(f"      ✅ 발송 완료! Campaign ID: {campaign_id}")
    return campaign_id


def main():
    # 환경 변수 확인
    api_key = os.environ.get("MAILCHIMP_API_KEY")
    if not api_key:
        sys.stderr.write("[오류] MAILCHIMP_API_KEY 환경 변수가 설정되지 않았습니다.\n")
        sys.exit(1)

    audience_id = os.environ.get("MAILCHIMP_AUDIENCE_ID", AUDIENCE_ID_DEFAULT)

    # 데이터 로드
    if not LATEST_JSON.exists():
        sys.stderr.write(f"[오류] {LATEST_JSON} 파일을 찾을 수 없습니다.\n")
        sys.exit(1)

    with open(LATEST_JSON, encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("articles"):
        print("[알림] 발송할 카드가 없습니다. 건너뜁니다.")
        return

    print(f"=== Mailchimp 발송 시작 ===")
    print(f"주차: {data.get('week_of')}")
    print(f"카드 수: {data.get('total_cards')}")
    print(f"Audience ID: {audience_id}")
    print()

    try:
        send_campaign(data, api_key, audience_id)
    except Exception as e:
        sys.stderr.write(f"\n[발송 실패] {type(e).__name__}: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
