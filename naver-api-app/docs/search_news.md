# 네이버 검색 - 뉴스 검색 API 명세

네이버 검색 엔진의 뉴스 섹션 검색 결과를 조회할 수 있는 RESTful API 명세입니다.

## 1. 기본 정보

- **요청 URL**: `https://openapi.naver.com/v1/search/news.json` (JSON 형식 반환)
  *(XML 형식의 응답을 원하는 경우 `https://openapi.naver.com/v1/search/news.xml` 호출 가능)*
- **프로토콜**: HTTPS
- **HTTP 메서드**: GET
- **일일 호출 제한**: 25,000회 (비로그인 방식)

---

## 2. 요청 파라미터 (Query String)

| 파라미터명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `query` | string | Y | - | 검색어. 반드시 UTF-8 형식으로 URL 인코딩하여 전송해야 합니다. |
| `display` | integer | N | 10 | 한 번에 표시할 검색 결과 개수 (허용 범위: 1 ~ 100) |
| `start` | integer | N | 1 | 검색 시작 위치 (허용 범위: 1 ~ 1000) |
| `sort` | string | N | `sim` | 정렬 방식<br>- `sim`: 정확도순 내림차순<br>- `date`: 작성일순 내림차순 |

---

## 3. 응답 데이터 구조 (JSON)

| 필드명 | 타입 | 설명 |
| :--- | :---: | :--- |
| `lastBuildDate` | string | 검색 결과가 생성된 날짜 및 시간 |
| `total` | integer | 총 검색 결과 개수 |
| `start` | integer | 검색 시작 위치 |
| `display` | integer | 한 번에 표시되는 결과 개수 |
| `items` | array | 개별 뉴스 기사의 검색 결과 목록 |
| `items[].title` | string | 뉴스 기사의 제목 (검색 키워드는 `<b>` 태그로 강조 표시됨) |
| `items[].originallink` | string | 뉴스 언론사 원문의 URL 주소 |
| `items[].link` | string | 해당 기사의 네이버 뉴스 URL (네이버 비제공 기사인 경우 originallink와 동일) |
| `items[].description` | string | 뉴스 기사의 요약문 (검색 키워드는 `<b>` 태그로 강조 표시됨) |
| `items[].pubDate` | string | 기사가 등록되었거나 네이버에 제공된 발행 일시 |

### 응답 반환 예시 (JSON)
```json
{
  "lastBuildDate": "Mon, 26 Sep 2016 11:01:35 +0900",
  "total": 2566589,
  "start": 1,
  "display": 10,
  "items": [
    {
      "title": "국내 <b>주식</b>형펀드서 사흘째 자금 순유출",
      "originallink": "http://app.yonhapnews.co.kr/...",
      "link": "https://n.news.naver.com/...",
      "description": "국내 <b>주식</b>형 펀드에서 사흘째 자금이 빠져나갔다. 26일...",
      "pubDate": "Mon, 26 Sep 2016 07:50:00 +0900"
    }
  ]
}
```
