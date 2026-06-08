# 네이버 데이터랩 - 통합 검색어 트렌드 API 명세

네이버 통합검색 내에서 특정 주제어로 묶인 검색어들에 대한 검색 추이 데이터를 조회하는 API 사양입니다.

## 1. 기본 정보

- **요청 URL**: `https://openapi.naver.com/v1/datalab/search`
- **프로토콜**: HTTPS
- **HTTP 메서드**: POST
- **콘텐츠 타입**: `application/json`
- **일일 호출 제한**: 1,000회 (비로그인 방식)

---

## 2. 요청 헤더 (Request Headers)

```http
POST /v1/datalab/search HTTP/1.1
Host: openapi.naver.com
Content-Type: application/json
X-Naver-Client-Id: {발급받은_클라이언트_아이디}
X-Naver-Client-Secret: {발급받은_클라이언트_시크릿}
```

---

## 3. 요청 바디 파라미터 (JSON)

| 파라미터명 | 타입 | 필수 여부 | 설명 |
| :--- | :---: | :---: | :--- |
| `startDate` | string | Y | 조회 기간 시작 날짜 (`yyyy-mm-dd` 형식, 2016-01-01부터 가능) |
| `endDate` | string | Y | 조회 기간 종료 날짜 (`yyyy-mm-dd` 형식) |
| `timeUnit` | string | Y | 구간 단위 (`date`: 일간, `week`: 주간, `month`: 월간) |
| `keywordGroups` | array | Y | 주제어와 하위 검색어 그룹의 배열 (최대 5개 그룹) |
| `keywordGroups[].groupName` | string | Y | 주제어 (검색어 묶음을 대표하는 이름) |
| `keywordGroups[].keywords` | array | Y | 주제어에 속할 세부 검색어 목록 (최대 20개) |
| `device` | string | N | 검색 환경 조건 (설정 안 함: 전체, `pc`: PC 검색, `mo`: 모바일 검색) |
| `gender` | string | N | 검색 사용자 성별 (설정 안 함: 전체, `m`: 남성, `f`: 여성) |
| `ages` | array | N | 검색 사용자 연령대 조건 (`1`: 0~12세, `2`: 13~18세, ..., `11`: 60세 이상) |

### 요청 바디 작성 예시 (JSON)
```json
{
  "startDate": "2023-01-01",
  "endDate": "2023-04-30",
  "timeUnit": "month",
  "keywordGroups": [
    {
      "groupName": "한글",
      "keywords": ["한글", "korean"]
    },
    {
      "groupName": "영어",
      "keywords": ["영어", "english"]
    }
  ],
  "device": "pc",
  "gender": "f",
  "ages": ["1", "2"]
}
```

---

## 4. 응답 데이터 구조 (JSON)

| 필드명 | 타입 | 설명 |
| :--- | :---: | :--- |
| `startDate` | string | 조회 시작 날짜 |
| `endDate` | string | 조회 종료 날짜 |
| `timeUnit` | string | 데이터 시간 단위 |
| `results` | array | 주제어 그룹별 분석 결과 목록 |
| `results[].title` | string | 주제어 명 |
| `results[].keywords` | array | 해당 주제어에 속한 검색어 목록 |
| `results[].data` | array | 구간별 검색 비율 데이터 목록 |
| `results[].data[].period` | string | 구간별 시작 날짜 (`yyyy-mm-dd` 형식) |
| `results[].data[].ratio` | number | 구간별 상대적 검색 비율 (해당 기간 최고점을 100으로 설정한 상댓값) |

### 응답 데이터 반환 예시 (JSON)
```json
{
  "startDate": "2023-01-01",
  "endDate": "2023-04-30",
  "timeUnit": "month",
  "results": [
    {
      "title": "한글",
      "keywords": ["한글", "korean"],
      "data": [
        { "period": "2023-01-01", "ratio": 47.0 },
        { "period": "2023-02-01", "ratio": 100.0 }
      ]
    }
  ]
}
```
