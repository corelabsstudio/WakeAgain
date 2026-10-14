# 가성비 상품 데이터 운영

현재 공식 API·제휴 계정은 미연결입니다. 네이버는 발급 상품 링크 및 사용 허용 자료의 운영자 승인 JSON 가져오기에 한정합니다. 일반 쇼핑 검색 API를 제휴 상품·판매량 근거로 사용하지 않습니다. 쿠팡 인증 API 어댑터는 공식 스키마 및 최종 승인 확인 전 등록하지 않았습니다. 토스는 제외합니다. 외부 요청·검색·유료 호출·자격증명 설정은 이 코드에 없습니다.

파이프라인은 승인 JSON → 정규화·검증 → 검토 대기/적격 후보 → 중복 제거 → 선택적 게시 → 재검증·만료입니다. 판매량이나 최저가를 추정하지 않습니다. 판매/공식 인기 근거와 리뷰 수를 구분합니다. 공개 제휴 링크는 발급 원문을 href에 직접 넣으며 중간 이동 경로를 만들지 않습니다.

## 설정과 실행

데이터는 기존 matching DB와 별도로 `/data/matching/curation`에 저장합니다. 설정 파일이 없으면 수집/게시 모두 꺼짐입니다. 승인된 자료만 이 디렉터리의 `imports/*.json`에 넣습니다. 경로 이탈·심볼릭 링크 이탈·5MB 초과·500행 초과를 거부합니다. 설정은 로컬 운영자가 관리하며 공개 쓰기 API는 없습니다. 아래 내용을 `settings.json`으로 검토 후 생성합니다. 실제 계정 승인과 데이터 사용권 확인 전 true로 바꾸지 마세요.

```json
{"enabled":false,"autoPublish":false,"intervalSeconds":3600,"sources":[],"programs":[]}
```

각 소스는 id, enabled, approved, channelApproved, approvalReference, redistributionAllowed, priceComparisonAllowed, termsUrl, adapter=`operator_import`, file=`승인된파일.json`, maxCacheSeconds가 필요합니다. 승인·채널·재게시·가격 비교 허용값은 실제 증거가 있어야 true입니다. 출처 허용 캐시는 1~86400초로 지정하고 더 짧은 상품 expiresAt을 우선합니다. 원본 imports 파일은 운영자가 권한·캐시 정책에 따라 관리해야 하며 이 프로그램은 원본 보관 허가를 부여하지 않습니다.

programs는 id, approved, allowedHosts 및 requiredTrackingParams 또는 trackingMode=`path`와 trackingPathPattern을 공식 발급 방식에 맞춰 설정합니다. API 키·비밀값을 넣지 않습니다. 공개 응답은 이 허용된 필드만 보냅니다.

```sh
python value_catalog.py --data /data/matching/curation --dry-run
python value_catalog.py --data /data/matching/curation
```

dry-run은 설정의 승인 소스만 읽고 상태·상품 파일을 수정하지 않습니다. enabled=false인 일반 실행은 수집하지 않습니다. enabled=true 후 서버 재시작하면 최소 1시간 간격 작업이 시작됩니다. autoPublish=false는 적격 후보만 준비하고 기존의 아직 유효한 공개 자료를 보존합니다. true는 적격 결과를 원자적으로 교체합니다. 원격 연동 어댑터 추가와 지속 접근 활성화는 별도 승인·공식 범위 확인이 필요합니다.

## JSON 상품 필드

배열의 각 상품에 sku, option, unit, quantity, currency=`KRW`, name, category, merchant, sourceUrl, sourceName, selectionReason, price, shipping, shippingVerified, infoCheckedAt, expiresAt, stock를 넣습니다. 금액/배송비/판매 근거가 미확인이라면 null로 두고 해당 후보는 공개하지 않습니다. 옵션·수량 단위는 임의 환산하지 않습니다. 가격대 필터는 배송비 포함 총액입니다. 단가는 `(price+shipping)/quantity`입니다.

comparisons는 동일 sku/option/unit/quantity를 갖는 최소 두 개의 서로 다른 확인된 외부 출처이며 price, shipping, sourceUrl, checkedAt, verified가 필요합니다. 해당 상품의 총액이 각 비교값보다 높으면 선정하지 않습니다. 이것은 확인한 출처 사이의 비교이며 전체 시장 최저가를 의미하지 않습니다.

popularity는 kind=`sales_count`/`sales_rank`/`official_popularity_rank`, value, verified, sourceUrl, period, checkedAt입니다. review_count는 제외됩니다. quality는 verified, sourceUrl, checkedAt, returnSummary, riskSummary이며 품질·반품 조건 확인 기록입니다. 모든 기준일은 시간대가 명시된 ISO 8601이고 미래나 유효기한 경과 데이터를 게시하지 않습니다.

affiliateApproved, programId, affiliateUrl, linkVerified, disclosure 및 imagePath, imageUsageAllowed, imagePermissionSource가 필요합니다. 이미지는 사용권을 확인한 실제 상품 이미지를 `/curation/assets/` 아래 로컬 PNG/JPEG/WebP로 준비해야 합니다. 브랜드 사진을 상품 실물로 등록하지 마세요. 현재 자동 원격 이미지 다운로드는 제공하지 않습니다.

## 상태·실패·권한 취소

catalog.json은 공개 결과, candidates.json은 적격 검토 후보, review.json은 미확인 항목의 원본 행 번호와 사유입니다. 원시 가격이 없는 status.json 및 최대 100회의 runs.json은 운영 점검용입니다. 공개 GET `/api/curation/catalog`는 상품·출처별 승인 프로그램의 공개 필드·가동 상태만 반환합니다. 새 공개 쓰기 경로는 없습니다.

성공한 소스에서 품절/삭제된 상품은 공개 목록에서 제거됩니다. 실패한 소스는 이전 정상 자료 중 확인 기한이 남은 것만 유지하며 만료 시 삭제합니다. 만료 가격·재고를 공개하지 않습니다. 출처 권한을 취소하면 공개 대상에서 즉시 빠집니다. 로그는 상품 원문/비밀값을 저장하지 않습니다. 테스트 픽스처는 임시 디렉터리에만 존재합니다.

## 공식 확인 자료

- Naver 일반 쇼핑 검색 API: https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md (Shopping Connect 제휴 적격 상품 목록 API와 다름)
- Naver 링크 변형 제한: https://help.naver.com/service/30027/contents/22312?lang=ko
- Coupang 승인/API 가이드: https://partners.coupangcdn.com/partners-guide/partners-guide-20251028182159.pdf (17·20쪽)
- Toss API 신청 제한: https://sharelink-docs.toss.im/developers/open-api/auth.md
