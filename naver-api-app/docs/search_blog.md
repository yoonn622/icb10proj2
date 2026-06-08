# 네이버 검색 - 블로그 검색 API 명세

네이버 검색 엔진의 블로그 섹션 검색 결과를 조회할 수 있는 RESTful API 명세입니다.

## 1. 기본 정보

- **요청 URL**: `https://openapi.naver.com/v1/search/blog.json` (JSON 형식 반환)
  *(XML 형식의 응답을 원하는 경우 `https://openapi.naver.com/v1/search/blog.xml` 호출 가능)*
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
| `items` | array | 개별 블로그 포스트의 검색 결과 목록 |
| `items[].title` | string | 블로그 포스트의 제목 (검색 키워드는 `<b>` 태그로 강조 표시됨) |
| `items[].link` | string | 블로그 포스트의 실제 URL 주소 |
| `items[].description` | string | 포스트 본문 요약문 (검색 키워드는 `<b>` 태그로 강조 표시됨) |
| `items[].bloggername` | string | 해당 블로그의 이름 |
| `items[].bloggerlink` | string | 해당 블로그의 메인 주소 URL |
| `items[].postdate` | string | 포스트가 등록된 날짜 (`yyyymmdd` 형식) |

### 응답 반환 예시 (JSON)
```json
{
  "lastBuildDate": "Mon, 26 Sep 2016 10:39:37 +0900",
  "total": 8714891,
  "start": 1,
  "display": 10,
  "items": [
    {
      "title": "명예훼손 없이 <b>리뷰</b>쓰기",
      "link": "https://blog.naver.com/yoonbitgaram/...",
      "description": "명예훼손 없이 <b>리뷰</b>쓰기 우리 블로그하시는 분들께는...",
      "bloggername": "건짱의 Best Drawing World2",
      "bloggerlink": "https://blog.naver.com/yoonbitgaram",
      "postdate": "20161208"
    }
  ]
}
```
