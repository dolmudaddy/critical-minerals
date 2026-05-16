# KCMO Vault

KCMO Weekly (Korea Critical Minerals ODA Weekly)가 매주 일요일 08:00 KST에
자동 생성하는 노트 모음입니다.

## 폴더 구조

- `articles/{연도}/` — 카드 1건당 마크다운 노트 1개
- `weekly/{연도}/KCMO Weekly {YYYY-Www}.md` — 주간 인덱스

## 옵시디언 활용

### Graph View
좌측 Graph 아이콘 → 카드와 협력 노드(국가·광종·기관) 사이 연결망 시각화.
1년 누적 시 핵심광물 ODA 도메인 지형도가 만들어집니다.

### Wikilink로 협력 관점 탐색
- `[[탄자니아]]` — 탄자니아 관련 모든 카드
- `[[KIAT]]` — KIAT가 등장한 모든 카드
- `[[탄자니아 흑연]]` — 탄자니아 × 흑연 협력 노드 (자동 생성)
- 좌측 Backlinks 패널에 해당 노드를 인용한 모든 카드가 표시됨

### Dataview 쿼리 예시
```dataview
TABLE date, source, score
FROM "KCMO/articles"
WHERE contains(tags, "흑연") AND country = "탄자니아"
SORT date DESC
LIMIT 20
```

## 자동 생성 정책

- **카드 노트는 기계 출력 영역**입니다. 같은 id로 매주 덮어쓰기됨.
- 박사님 수기 메모는 카드가 아니라 **협력 노드 페이지**에 작성하세요.
  예: `[[탄자니아]]`, `[[KIAT]]`, `[[탄자니아 흑연]]`
- 노드 페이지는 옵시디언이 빈 wikilink 클릭 시 자동 생성합니다.

## 출처

- **운영자**: 조성준 박사 (KIGAM 책임연구원)
- **소스 저장소**: https://github.com/dolmudaddy/korea-oda-minerals
- **사이트**: https://dolmudaddy.github.io/korea-oda-minerals/
