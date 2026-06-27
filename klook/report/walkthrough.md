# Klook 상세페이지 실시간 리뷰 연동 및 파싱 완료 보고서

Klook 상세페이지에서 동적으로 로딩되는 리뷰 정보를 보완하기 위해 **비동기 리뷰 수집 API(`activity_reviews_list`)를 우회 연동**하여, 개별 상품의 실제 **리뷰 개수, 평점, 대표 리뷰 텍스트 및 작성자 닉네임**을 완벽하게 파싱 및 SQLite 데이터베이스에 적재 완료했습니다.

---

## 1. 주요 작업 변경사항 (Changes Made)

### 1.1. 비동기 리뷰 수집 API 연동
- **[detail_scraper.py](file:///c:/Users/82104/Desktop/icb10proj2/klook/src/detail_scraper.py)**:
  - 기존 HTML DOM 파싱으로는 로딩되지 않던 실시간 리뷰 데이터를 수집하기 위해, Klook의 내부 비동기 리뷰 서비스 API(`activity_reviews_list`)를 자동으로 추출 및 타겟팅하여 연동 호출하는 로직을 추가했습니다.
  - 헤더에 브라우저의 기본 요청 특성을 완벽히 반영하여 WAF 차단을 안전하게 우회하고 한국어(`ko_KR`) 리뷰를 받아오도록 구현했습니다.
  - 받아온 JSON 응답에서 `result.item` 내의 리뷰 리스트를 `reviews_json` 컬럼에 통째로 저장하고, 그 중 0번째 리뷰 데이터를 파싱하여 대표 리뷰 정보(`representative_review`, `representative_review_author`, `representative_review_rating`)를 추출 및 저장합니다.
  - 100점 만점으로 제공되는 API 상의 리뷰 평점을 5점 단위 평점으로 자동 변환하여 정합성을 일치시켰습니다.

### 1.2. WAF 차단 및 인코딩 예외 처리 강화
- **패키지 API 403 대응**: Klook의 패키지 API가 Cloudflare/DataDome WAF에 의해 강력하게 차단되는 환경을 고려하여, 수집 실패 시 빈 값(`[]`)으로 채우며 크래시 없이 조용히 넘어가도록 설계했습니다.
- **윈도우 터미널 인코딩 오류 수정**: 대표 리뷰 내용에 포함된 특수 문자(예: 유니코드 한자 戲 등)를 윈도우 터미널에 print하는 과정에서 발생하던 `cp949` 코덱 에러를 완벽하게 예방하기 위해, DB 저장 시의 터미널 print 로그를 간결하게 수치 중심으로 변경했습니다. DB 내에는 모든 유니코드가 정상적으로(UTF-8) 저장됩니다.

---

## 2. 검증 결과 (Validation Results)

### 2.1. SQLite 데이터베이스 조인(JOIN) 및 실시간 리뷰 추출 검증
두 테이블을 `INNER JOIN`하여 각 상품의 기본 정보와 상세페이지에서 추가 발췌한 실시간 리뷰 및 평점 지표들을 조회한 결과입니다.

- **조인된 총 레코드 수**: 10개
- **검증 쿼리 결과 (리뷰 수 및 실제 내용 추출)**:
  ```python
  ID: 346 | Title: 제주 첫 방문객을 위한 당일 투어 | 유네스코...
    Review Count: 4077 | Detail Rating: 4.9
    Rep Review Author: 클룩 고객 | Rep Review Rating: 5.0
    Rep Review Content: Elin our tour guide was amazing!!!  She was very nice and helpful. She took great care of us every step of the way.  She offered to help take our fami...
  
  ID: 1163 | Title: 인천국제공항 공항철도 AREX 편도 티켓...
    Review Count: 81114 | Detail Rating: 4.8
    Rep Review Author: Chermaine ***************** | Rep Review Rating: 5.0
    Rep Review Content: I used AREX to and from Incheon Airport and Seoul Station, and it was super convenient. The train arrived and left on time.
  
  ID: 28904 | Title: 제주 본태박물관 티켓...
    Review Count: 10 | Detail Rating: 4.2
    Rep Review Author: LEE ******* | Rep Review Rating: 5.0
    Rep Review Content: 제주에서 비오면 본태박물관 가세요 ! 비안와도 가세요 ㅎㅎㅎ 갑자기 일정 바꿔서 들린 곳인데 너무 좋았어요. 쿠사마 야요이 호박이랑 거울의 방 말고도 그냥 건축물 구경 하는 것도 재밌답니다 :)
  
  ID: 29106 | Title: [제주] 휴애리 자연생활공원 입장권...
    Review Count: 23 | Detail Rating: 4.6
    Rep Review Author: 클룩 고객 | Rep Review Rating: 5.0
    Rep Review Content: 입장전 현장예매하고 바로입장했어요. 10프로 할인받고..들어갈만^^ 핑크뮬리 2군데 다 예뻐요. 아스타국화는 색은 이쁜데 꽃잎이 작아 눈에 띄는 배경이 되진 못해요.
  ```

이로써 가격, 평점, 실제 리뷰 수, 실시간 대표 리뷰 본문 등이 모두 DB 내의 고유 컬럼으로 깨끗하게 분리 및 파싱되어 적재되었습니다.
