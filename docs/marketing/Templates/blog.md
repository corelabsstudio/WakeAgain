# WakeAgain 풀 SEO 블로그 템플릿 (구조 스펙)

> 실제 파일: `public/blog/<slug>.html`  
> 참고: `mvp-sell-before-delete.html`, `side-project-second-chance.html`  
> 스타일: `public/blog/blog.css` + `/styles.css`

---

## 메타

- `lang` 기본 ko (영문 글이면 en)
- `title`: `{키워드 포함 제목} | WakeAgain`
- `description`: 150자 내 · 수익 보장 금지
- `canonical`: `https://wakeagain.com/blog/<slug>.html`
- `og:image`: `https://wakeagain.com/assets/og-image.jpg`
- JSON-LD `BlogPosting` · author CoreLabs
- keywords 메타: 롱테일 중 주제 맞는 것

## 본문 필수 섹션 순서

1. **Kicker** — 예) Indie maker · Side project exit
2. **H1** — 키워드 + 공감 (보장·과장 금지)
3. **이슈 요약** — 3줄 + 출처 링크 (해당 시)
4. **인사이트** — 묵히기/삭제 vs 넘기기·현금화
5. **실무 팁** — 매물 올릴 때 준비물, 데모, 가격 감각 (허위 시세 금지)
6. **해결책 + CTA**
   - 취지: 키워드 검색·안전거래 흐름으로 프로토타입에 두 번째 기회, 무료 매물 등록
   - 링크: https://wakeagain.com · https://wakeagain.com/sell.html
7. **면책** — 수익·성사 보장 아님, 개별 거래 판단

## 키워드

- 사이드 프로젝트 수익화 / 방치된 앱 처분 / MVP 프로토타입 판매 / 인디해커 수익
- 자연 배치 · 스터핑 금지

## 배포 전 Writer가 같이 손댈 파일

- `public/blog/index.html` — 카드 상단
- `public/sitemap.xml` — URL 추가
