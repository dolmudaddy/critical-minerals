"""
generate_markdown.py
Critical Minerals Weekly의 카드 데이터를 Obsidian 마크다운 파일로 변환.

워크플로우:
1. data/latest.json 로드 (이번 주 새 카드)
2. 각 카드를 마크다운으로 변환 후 vault/articles/에 저장
3. vault/README.md를 한 번만 생성 (이미 있으면 건너뜀)

출력 구조:
  vault/
  ├── README.md           (vault 사용 안내)
  └── articles/
      ├── 2026-05-11-폴란드-EU-SAFE-차입협약.md
      ├── 2026-05-11-PINNs-베이지안-역산.md
      └── ...
"""

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

# ───────── 위키링크 사전 ─────────
# 영문 키워드 → 한국어 위키링크 노드명
# 순서 중요: 긴 표현이 먼저 매칭되어야 함

# 광종/소재 (영문 → 한국어)
MINERAL_EN = [
    ("rare earth elements", "희토류"),
    ("rare earth element", "희토류"),
    ("rare earths", "희토류"),
    ("rare earth", "희토류"),
    ("platinum group", "백금족"),
    ("lithium", "리튬"),
    ("cobalt", "코발트"),
    ("nickel", "니켈"),
    ("graphite", "흑연"),
    ("manganese", "망간"),
    ("gallium", "갈륨"),
    ("germanium", "게르마늄"),
    ("indium", "인듐"),
    ("tellurium", "텔루륨"),
    ("tungsten", "텅스텐"),
    ("vanadium", "바나듐"),
    ("antimony", "안티모니"),
    ("fluorite", "형석"),
    ("REE", "희토류"),
]

# 광종 한국어 → 한국어 위키링크 (요약문 처리용)
MINERAL_KO = [
    "희토류", "백금족",
    "리튬", "코발트", "니켈", "흑연", "망간",
    "갈륨", "게르마늄", "인듐", "텔루륨",
    "텅스텐", "바나듐", "안티모니", "형석",
]

# 지역/국가 (영문 → 한국어)
REGION_EN = [
    ("european union", "유럽연합"),
    ("united states", "미국"),
    ("united kingdom", "영국"),
    ("south korea", "한국"),
    ("north america", "북미"),
    ("south america", "남미"),
    ("asia-pacific", "아시아태평양"),
    ("east africa", "동아프리카"),
    ("tanzania", "탄자니아"),
    ("indonesia", "인도네시아"),
    ("argentina", "아르헨티나"),
    ("australia", "호주"),
    ("canada", "캐나다"),
    ("chile", "칠레"),
    ("poland", "폴란드"),
    ("germany", "독일"),
    ("france", "프랑스"),
    ("china", "중국"),
    ("japan", "일본"),
    ("russia", "러시아"),
    ("brazil", "브라질"),
    ("india", "인도"),
    ("congo", "콩고"),
]

# 지역 한국어 → 한국어 위키링크
REGION_KO = [
    "유럽연합", "아시아태평양", "동아프리카",
    "탄자니아", "인도네시아", "아르헨티나",
    "폴란드", "호주", "캐나다", "칠레",
    "미국", "중국", "일본", "한국", "영국",
    "독일", "프랑스", "러시아", "브라질", "인도", "콩고",
    "북미", "남미", "유럽", "아프리카", "퀘벡",
]

# 정책/이슈/제도 (영문 → 한국어)
POLICY_EN = [
    ("inflation reduction act", "IRA"),
    ("critical raw materials act", "CRMA"),
    ("critical raw materials", "CRMA"),
    ("supply chain resilience", "공급망 회복력"),
    ("supply chain", "공급망"),
    ("value chain", "가치사슬"),
    ("export restriction", "수출통제"),
    ("export control", "수출통제"),
    ("price floor", "가격하한제"),
    ("strategic stockpile", "전략비축"),
    ("stockpile", "전략비축"),
    ("trade bloc", "무역블록"),
    ("energy transition", "에너지 전환"),
    ("electric vehicle", "전기차"),
    ("permanent magnet", "영구자석"),
    ("strategic autonomy", "전략적 자립"),
    ("critical minerals", "핵심광물"),
    ("critical mineral", "핵심광물"),
    ("battery materials", "배터리 소재"),
    ("rare earth supply", "희토류 공급"),
    ("SAFE", "SAFE"),
    ("CRMA", "CRMA"),
    ("IRA", "IRA"),
    ("ODA", "ODA"),
]

# 정책 한국어 → 한국어 위키링크
POLICY_KO = [
    "공급망 다변화", "공급망 회복력", "공급망",
    "가치사슬", "수출통제", "가격하한제", "전략비축",
    "무역블록", "에너지 전환", "전기차", "영구자석",
    "전략적 자립", "핵심광물", "배터리 소재", "희토류 공급",
    "지정학적 위험", "자급화", "공급망 독립성",
]

# 탐사기술 (영문 → 한국어)
TECH_EN = [
    ("physics-informed neural networks", "PINNs"),
    ("PINNs", "PINNs"),
    ("magnetotelluric", "MT 탐사"),
    ("MT survey", "MT 탐사"),
    ("hyperspectral", "초분광 탐사"),
    ("remote sensing", "원격탐사"),
    ("machine learning", "기계학습"),
    ("AI exploration", "AI 탐사"),
    ("geophysical", "지구물리탐사"),
    ("geochemical", "지화학 탐사"),
    ("geochemistry", "지화학"),
    ("Bayesian inversion", "베이지안 역산"),
    ("Bayesian", "베이지안"),
    ("seismic", "탄성파 탐사"),
    ("drilling", "시추"),
    ("exploration drilling", "탐사 시추"),
    ("infill drilling", "충진 시추"),
]

# 탐사기술 한국어 → 한국어 위키링크
TECH_KO = [
    "지구물리탐사", "지구물리 역산", "지화학 탐사",
    "MT 탐사", "초분광 탐사", "원격탐사",
    "기계학습", "인공지능", "AI 탐사",
    "베이지안 역산", "베이지안",
    "탄성파 탐사", "시추", "탐사 시추", "충진 시추",
    "광물탐사", "광물탐사기술", "자원량 추정", "광물화 잠재력",
]


def slugify_ko(text, max_len=60):
    """한국어/영문 혼합 텍스트를 파일명용 slug로 변환.
    - 특수문자·구두점 제거
    - 공백 → 하이픈
    - 한글·영문·숫자만 허용
    """
    # 유니코드 정규화
    text = unicodedata.normalize("NFC", text)
    # 따옴표·특수기호 제거
    text = re.sub(r"['\"`'`""·]", "", text)
    # 영문·숫자·한글·공백·하이픈 외 모두 공백으로
    text = re.sub(r"[^\w\s가-힣\-]", " ", text)
    # 공백 정리
    text = re.sub(r"\s+", "-", text.strip())
    # 연속 하이픈 정리
    text = re.sub(r"-+", "-", text).strip("-")
    # 길이 제한 (한글 기준)
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text or "untitled"


def build_filename(article):
    """파일명 생성: YYYY-MM-DD-한국어slug.md
    한국어 제목이 있으면 영문 원제에서 핵심 명사 추출하여 결합."""
    # 발행일에서 날짜 추출
    pub = article.get("published", "")
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")
    except Exception:
        date_str = article.get("week_of", "0000-00-00")[:10]

    # 한국어 제목 후보: tags 첫 1-2개를 결합 + 영문 원제 핵심
    tags = article.get("tags", []) or []
    title_en = article.get("title", "untitled")

    # 영문 원제에서 핵심 키워드 추출 (불용어 제거)
    stopwords = {
        "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
        "with", "by", "from", "as", "is", "was", "are", "were", "be", "been",
        "this", "that", "these", "those", "new", "via",
    }
    words = re.findall(r"[A-Za-z가-힣]+", title_en)
    keywords = [w for w in words if w.lower() not in stopwords][:5]
    title_part = " ".join(keywords)

    # 한국어 태그 1-2개를 앞에 붙임
    if tags:
        tag_part = "-".join(tags[:2])
        slug = slugify_ko(f"{tag_part}-{title_part}")
    else:
        slug = slugify_ko(title_part)

    return f"{date_str}-{slug}.md"


def make_pattern(keyword):
    """키워드에 안전한 정규식 패턴 생성.
    - 영문: 단어 경계
    - 한글 포함: 단순 매칭 (한글은 단어 경계 개념이 약해서)
    """
    escaped = re.escape(keyword)
    # 영문만으로 구성되었는지 확인
    if re.fullmatch(r"[A-Za-z0-9 \-]+", keyword):
        return re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    else:
        return re.compile(escaped)


# 사전 컴파일
_PATTERNS_EN = []
for kw_list in [MINERAL_EN, REGION_EN, POLICY_EN, TECH_EN]:
    for kw, target in kw_list:
        _PATTERNS_EN.append((make_pattern(kw), target))

_PATTERNS_KO = []
for kw in MINERAL_KO + REGION_KO + POLICY_KO + TECH_KO:
    _PATTERNS_KO.append((make_pattern(kw), kw))


def linkify(text):
    """텍스트에 자동 위키링크 삽입.
    이미 [[…]] 안에 있는 표현은 다시 변환하지 않도록 처리.
    """
    if not text:
        return ""

    # 1단계: 이미 변환된 부분 보호 (placeholder로 치환)
    placeholders = {}

    def protect(m):
        key = f"\x00PROTECTED{len(placeholders)}\x00"
        placeholders[key] = m.group(0)
        return key

    protected = re.sub(r"\[\[[^\]]+\]\]", protect, text)

    # 2단계: 영문 키워드 → 한국어 위키링크
    # 매칭된 부분도 보호 처리하여 중복 변환 방지
    matched = []

    def replace_with_link(match, target):
        result = f"[[{target}]]"
        matched.append((match.start(), match.end(), result))
        return result

    # 모든 매칭을 한 번에 수집 (좌→우, 길이 긴 것 우선은 패턴 순서로 보장)
    for pattern, target in _PATTERNS_EN + _PATTERNS_KO:
        spans_to_replace = []
        for m in pattern.finditer(protected):
            # 이미 다른 매칭이 이 구간을 차지했는지 확인
            overlap = False
            for s, e, _ in matched:
                if not (m.end() <= s or m.start() >= e):
                    overlap = True
                    break
            if not overlap:
                spans_to_replace.append((m.start(), m.end()))
                matched.append((m.start(), m.end(), f"[[{target}]]"))

    # 뒤에서부터 치환 (인덱스 보존)
    matched.sort(key=lambda x: x[0], reverse=True)
    result = protected
    for s, e, replacement in matched:
        result = result[:s] + replacement + result[e:]

    # 3단계: placeholder 복원
    for key, original in placeholders.items():
        result = result.replace(key, original)

    return result


def extract_related_concepts(article):
    """카드에서 등장한 위키링크 노드들을 카테고리별로 추출.
    Frontmatter `related`와 본문 하단 "관련 개념" 섹션 용도.
    """
    # 검색 대상 텍스트
    haystack = " ".join([
        article.get("title", ""),
        article.get("korean_summary", ""),
        article.get("summary_raw", "") or "",
        " ".join(article.get("tags", []) or []),
    ])

    found = {
        "광종": set(),
        "지역": set(),
        "정책": set(),
        "기술": set(),
    }

    # 영문 매칭
    for kw, target in MINERAL_EN:
        if make_pattern(kw).search(haystack):
            found["광종"].add(target)
    for kw, target in REGION_EN:
        if make_pattern(kw).search(haystack):
            found["지역"].add(target)
    for kw, target in POLICY_EN:
        if make_pattern(kw).search(haystack):
            found["정책"].add(target)
    for kw, target in TECH_EN:
        if make_pattern(kw).search(haystack):
            found["기술"].add(target)

    # 한국어 매칭
    for kw in MINERAL_KO:
        if make_pattern(kw).search(haystack):
            found["광종"].add(kw)
    for kw in REGION_KO:
        if make_pattern(kw).search(haystack):
            found["지역"].add(kw)
    for kw in POLICY_KO:
        if make_pattern(kw).search(haystack):
            found["정책"].add(kw)
    for kw in TECH_KO:
        if make_pattern(kw).search(haystack):
            found["기술"].add(kw)

    # 정렬된 리스트로 반환
    return {k: sorted(v) for k, v in found.items()}


# ───────── 카테고리 라벨 ─────────
CATEGORY_LABEL = {
    "policy_market": "정책·시장",
    "exploration_tech": "탐사기술",
    "discovery": "발견·매장지",
    "supply_chain": "공급망",
    "research": "연구",
}

TIER_LABEL = {
    5: "Government",
    4: "Academic",
    3: "Industry",
    1: "News Search",
}


def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return iso_str[:10] if iso_str else ""


def build_markdown(article, week_of):
    """카드 1개의 마크다운 문서 생성."""
    title = article.get("title", "(제목 없음)")
    url = article.get("url", "")
    source = article.get("source", "")
    tier = article.get("tier_weight", 1)
    category = article.get("category", "")
    score = article.get("score", 0)
    pub_date = format_date(article.get("published", ""))
    korean_summary = article.get("korean_summary", "")
    phrases = article.get("english_phrases", []) or []
    tags = article.get("tags", []) or []

    # 위키링크 변환된 본문
    summary_linked = linkify(korean_summary)

    # 관련 개념 추출
    related = extract_related_concepts(article)

    # 모든 위키링크 노드를 frontmatter related에도 기록
    all_links = sorted(set(
        related["광종"] + related["지역"] +
        related["정책"] + related["기술"]
    ))

    # YAML frontmatter
    # 따옴표 escape
    safe_title = title.replace('"', '\\"')
    safe_source = source.replace('"', '\\"')
    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    related_yaml = "\n".join(f"  - \"[[{r}]]\"" for r in all_links)

    frontmatter = f"""---
title: "{safe_title}"
date: {pub_date}
week_of: {week_of}
source: "{safe_source}"
source_url: {url}
tier: {tier}
tier_label: {TIER_LABEL.get(tier, "Source")}
category: {category}
category_label: {CATEGORY_LABEL.get(category, "")}
score: {score}
tags:
{tags_yaml}
related:
{related_yaml}
---
"""

    # 본문 제목: 한국어 태그 첫 번째 + 영문 원제
    display_title = f"{tags[0] if tags else '카드'} — {title}"

    # 영어 표현 섹션
    phrases_md = ""
    if phrases:
        items = []
        for p in phrases:
            phrase = p.get("phrase", "").replace('"', "'")
            meaning = p.get("meaning", "")
            items.append(f"- **\"{phrase}\"** — {meaning}")
        phrases_md = "\n".join(items)

    # 관련 개념 섹션
    related_sections = []
    for label, items in related.items():
        if items:
            links = " · ".join(f"[[{x}]]" for x in items)
            related_sections.append(f"- **{label}**: {links}")
    related_md = "\n".join(related_sections) if related_sections else "_(자동 추출된 관련 개념 없음)_"

    body = f"""
# {display_title}

> **출처**: [{source}]({url})
> **발표일**: {pub_date} · **Tier**: {TIER_LABEL.get(tier, "Source")} · **점수**: {score}

## 한국어 요약

{summary_linked}

## 영어 표현 (학회·국제회의 활용)

{phrases_md if phrases_md else "_(영어 표현 없음)_"}

## 관련 개념

{related_md}

---

**원문 보기**: <{url}>

*이 노트는 [Critical Minerals Weekly](https://dolmudaddy.github.io/critical-minerals/) 시스템이 {week_of} 주차에 자동 생성하였습니다.*
"""

    return frontmatter + body


# ───────── README ─────────
README_CONTENT = """# Critical Minerals Vault

이 vault는 [Critical Minerals Weekly](https://dolmudaddy.github.io/critical-minerals/) 시스템이 매주 자동으로 생성하는 마크다운 노트들의 모음입니다.

## 구조

```
vault/
├── README.md           ← 이 파일
└── articles/           ← 카드별 마크다운 (파일명: YYYY-MM-DD-키워드.md)
```

## Obsidian에서 활용하는 방법

### 1. Vault 열기
- Obsidian 실행 → **Open folder as vault** → 이 폴더(`vault/`) 선택

### 2. Graph View로 연결망 보기
- 좌측 사이드바에서 Graph View 아이콘 클릭
- 광종(`[[리튬]]`, `[[희토류]]`), 지역(`[[탄자니아]]`, `[[호주]]`), 정책(`[[IRA]]`, `[[CRMA]]`) 노드들이 카드들과 연결되어 표시됨
- 1년간 누적 시 핵심광물 분야 트렌드가 시각적으로 드러남

### 3. 위키링크 클릭으로 관련 카드 탐색
- 본문에서 `[[리튬]]` 클릭 → 해당 노트가 없으면 자동 생성됨 (그대로 두면 됨)
- 좌측 패널의 **Backlinks**에 "리튬을 언급한 모든 카드들"이 자동 표시됨
- 이것이 MOC를 대체하는 Obsidian 고유의 강력한 기능

### 4. Frontmatter 활용
각 카드의 YAML frontmatter에는 다음 정보가 포함됩니다:
- `tier`, `category`, `score`: 분류·중요도
- `tags`: 한국어 태그
- `related`: 자동 추출된 위키링크 목록

**Dataview 플러그인**을 설치하면 frontmatter를 쿼리할 수 있습니다:
```dataview
TABLE date, source, score
FROM "articles"
WHERE contains(tags, "리튬")
SORT date DESC
LIMIT 20
```

### 5. 동기화 (Obsidian Git 플러그인)
- Obsidian → Settings → Community plugins → "Obsidian Git" 설치
- 매일 또는 시간마다 자동 `git pull`로 GitHub의 새 카드를 받아옴

## 자동 생성 일정

- 매주 일요일 23:00 UTC (= 월요일 08:00 KST)
- GitHub Actions가 새 카드를 수집·요약하고 이 vault에도 마크다운으로 저장

## 위키링크 사전

자동 위키링크 변환은 `scripts/generate_markdown.py`의 사전을 기준으로 합니다:
- **광종**: 리튬, 코발트, 니켈, 흑연, 망간, 희토류, 갈륨, 게르마늄, 인듐, 텔루륨, 텅스텐, 바나듐, 안티모니, 형석, 백금족
- **지역**: 미국, 중국, 일본, 한국, 호주, 캐나다, 칠레, 폴란드, 탄자니아, 인도네시아, 아르헨티나, 콩고 등
- **정책**: IRA, CRMA, SAFE, ODA, 공급망, 수출통제, 전략비축, 에너지 전환, 핵심광물 등
- **기술**: PINNs, MT 탐사, 초분광 탐사, 원격탐사, 기계학습, 베이지안 역산, 지구물리탐사 등

새 키워드 추가가 필요하면 `scripts/generate_markdown.py`의 사전을 편집하세요.

---

*이 vault는 한국지질자원연구원(KIGAM) 조성준 박사의 핵심광물 큐레이션 시스템에서 자동 생성됩니다.*
"""


def main():
    latest_path = Path("data/latest.json")
    if not latest_path.exists():
        print(f"[알림] {latest_path} 없음. 건너뜁니다.")
        return

    with open(latest_path, encoding="utf-8") as f:
        data = json.load(f)

    week_of = data.get("week_of", "unknown")
    articles = data.get("articles", []) or []

    if not articles:
        print("[알림] 변환할 카드가 없습니다.")
        return

    # 출력 디렉토리
    vault_dir = Path("vault")
    articles_dir = vault_dir / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)

    # README (없을 때만 생성)
    readme_path = vault_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(README_CONTENT, encoding="utf-8")
        print(f"✓ Created: {readme_path}")

    # 각 카드를 마크다운으로 변환
    print(f"=== Markdown 생성 시작 (week: {week_of}, {len(articles)}건) ===")
    created = 0
    skipped = 0
    for article in articles:
        filename = build_filename(article)
        out_path = articles_dir / filename
        if out_path.exists():
            print(f"  · 이미 존재 (skip): {filename}")
            skipped += 1
            continue
        md = build_markdown(article, week_of)
        out_path.write_text(md, encoding="utf-8")
        print(f"  ✓ {filename}")
        created += 1

    print(f"\n=== 완료: 신규 {created}건, 건너뜀 {skipped}건 ===")


if __name__ == "__main__":
    main()
