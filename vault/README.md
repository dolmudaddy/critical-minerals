# Critical Minerals Vault

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
