# Critical Minerals Weekly

조성준 박사님 (KIGAM 책임연구원, 한국자원공학회장) 전용 중요광물 주간 동향 카드뉴스 시스템.

## 무엇을 하나

매주 월요일 아침 (KST 08:00), 다음을 자동으로 수행합니다:

1. **20여 개 RSS 소스**에서 지난 7일간의 critical mineral 관련 기사 수집
   - Tier 1: USGS, IEA, EU Commission, Geoscience Australia
   - Tier 2: Mining.com, S&P Global, Reuters, arXiv geo-physics
   - Tier 3: Google News 검색 (광범위 모니터링)
2. 키워드·소스 신뢰도·최신성 기반 **점수화 및 상위 12개 선별**
3. 제목 유사도 기반 **중복 제거**
4. **Claude API로 한국어 요약 + 영어 학습 표현 3개 자동 추출**
5. `chodolmu.github.io/critical-minerals/`에 자동 배포

## 초기 설정 (1회만)

### 1. 저장소 생성

```bash
# GitHub에서 'critical-minerals' 저장소 생성 후
git clone https://github.com/chodolmu/critical-minerals.git
cd critical-minerals
# 이 폴더 내용을 모두 복사
```

### 2. Anthropic API 키 등록

1. https://console.anthropic.com 에서 API 키 발급
2. GitHub 저장소 Settings → Secrets and variables → Actions
3. `New repository secret` 클릭
4. Name: `ANTHROPIC_API_KEY`, Value: 발급받은 키

### 3. GitHub Pages 활성화

저장소 Settings → Pages → Source: `Deploy from a branch`, Branch: `main` / `(root)`

### 4. 첫 실행 (테스트)

Actions 탭 → `Weekly Critical Minerals Digest` → `Run workflow` 버튼

3-5분 후 `https://dolmudaddy.github.io/critical-minerals/` 에서 확인 가능합니다.

## 일상 운영

박사님께서 직접 하실 일은 거의 없습니다. 다음 정도만:

- **소스 추가/제거**: `sources.yaml` 편집 후 commit
- **점수화 가중치 조정**: `sources.yaml`의 `keywords` 섹션 수정
- **수동 갱신**: Actions 탭에서 `Run workflow` 버튼
- **과거 기록 조회**: `data/week-YYYY-MM-DD.json` 파일

## 비용

- GitHub Actions: 무료 (월 2,000분 무료, 이 작업은 회당 5분 미만)
- GitHub Pages: 무료
- Claude API (Haiku 4.5): **주당 약 $0.3-1** (12개 카드 × 약 1,500 토큰)
- **연간 예상 비용: $20-50**

## 폴더 구조

```
critical-minerals/
├── index.html              # 카드뉴스 페이지
├── sources.yaml            # 소스 및 키워드 설정
├── scripts/
│   ├── collect.py          # RSS 수집 + 점수화
│   └── summarize.py        # Claude API 요약
├── data/
│   ├── latest.json         # 이번 주 (프론트엔드가 읽음)
│   ├── week-2026-05-06.json
│   └── raw-2026-05-06.json # 요약 전 원본
└── .github/workflows/
    └── weekly.yml          # 매주 자동 실행
```

## 학회·국제회의 활용 팁

각 카드 하단의 "표현 보기" 버튼을 누르면, Claude가 추출한 3개의 핵심 영어 표현이
나타납니다. 이 표현들은 박사님께서 한국자원공학회 발표나 Tanzania ODA 회의에서
직접 사용 가능한 수준으로 가공되어 있습니다.

또한 각 주의 `data/week-*.json` 파일은 그대로 인용 가능한 형식이므로,
연구·발표용 자료 백업으로도 활용 가능합니다.
