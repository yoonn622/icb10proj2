# 네이버 검색 - 카페글 검색 API 명세

네이버 전체 공개 카페 게시글 중에서 특정 검색어가 포함된 게시글의 검색 결과를 조회할 수 있는 RESTful API 명세입니다.

## 1. 기본 정보

- **요청 URL**: `https://openapi.naver.com/v1/search/cafearticle.json` (JSON 형식 반환)
  *(XML 형식의 응답을 원하는 경우 `https://openapi.naver.com/v1/search/cafearticle.xml` 호출 가능)*
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
| `items` | array | 개별 카페 게시글의 검색 결과 목록 |
| `items[].title` | string | 카페 게시글의 제목 (검색 키워드는 `<b>` 태그로 강조 표시됨) |
| `items[].link` | string | 카페 게시글의 실제 URL 주소 |
| `items[].description` | string | 카페 게시글의 본문 요약문 (검색 키워드는 `<b>` 태그로 강조 표시됨) |
| `items[].cafename` | string | 게시글이 작성된 네이버 카페의 이름 |
| `items[].cafeurl` | string | 게시글이 작성된 네이버 카페의 주소 URL |

### 응답 반환 예시 (JSON)
```json
{
  "lastBuildDate": "Mon, 26 Sep 2016 10:42:03 +0900",
  "total": 1777224,
  "start": 1,
  "display": 10,
  "items": [
    {
      "title": "<b>주식</b>과 비지니스 : 뇌동매매 방지 마인드",
      "link": "https://cafe.naver.com/darkpak/...",
      "description": "제가 <b>주식</b> 강의에서 이 말씀을 왜 드리는가?...",
      "cafename": "기술적분석 주식공부 모임",
      "cafeurl": "https://cafe.naver.com/darkpak"
    }
  ]
}
```
