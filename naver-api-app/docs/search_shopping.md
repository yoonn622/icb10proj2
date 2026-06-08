# 네이버 검색 - 쇼핑 검색 API 명세

네이버 쇼핑 서비스의 상품 검색 결과를 조회할 수 있는 RESTful API 명세입니다.

## 1. 기본 정보

- **요청 URL**: `https://openapi.naver.com/v1/search/shop.json` (JSON 형식 반환)
  *(XML 형식의 응답을 원하는 경우 `https://openapi.naver.com/v1/search/shop.xml` 호출 가능)*
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
| `sort` | string | N | `sim` | 정렬 방식<br>- `sim`: 정확도순 내림차순<br>- `date`: 등록일순 내림차순<br>- `asc`: 가격 낮은순 오름차순<br>- `dsc`: 가격 높은순 내림차순 |
| `filter` | string | N | - | 상품 유형 필터 (`naverpay`: 네이버페이 연동 상품만 노출) |
| `exclude` | string | N | - | 제외할 상품 유형. `{option}:{option}` 형태로 복수 설정 가능 (`used`: 중고 상품 제외, `rental`: 렌탈 상품 제외, `cbshop`: 해외직구/구매대행 제외) |

---

## 3. 응답 데이터 구조 (JSON)

| 필드명 | 타입 | 설명 |
| :--- | :---: | :--- |
| `lastBuildDate` | string | 검색 결과가 생성된 날짜 및 시간 |
| `total` | integer | 총 검색 결과 개수 |
| `start` | integer | 검색 시작 위치 |
| `display` | integer | 한 번에 표시되는 결과 개수 |
| `items` | array | 개별 상품의 검색 결과 목록 |
| `items[].title` | string | 상품명 (검색 키워드는 `<b>` 태그로 강조 표시됨) |
| `items[].link` | string | 상품 상세 정보 및 구매 페이지 URL |
| `items[].image` | string | 상품의 대표 섬네일 이미지 URL |
| `items[].lprice` | integer | 상품의 최저가 (없으면 0 반환, 단일 상품일 경우 판매가 의미) |
| `items[].hprice` | integer | 상품의 최고가 (없으면 0 반환) |
| `items[].mallName` | string | 상품을 판매하는 쇼핑몰명 (가격비교 대상이 아닌 단독몰인 경우 해당 쇼핑몰명) |
| `items[].productId` | string | 네이버 쇼핑 상품 ID |
| `items[].productType` | integer | 상품군 및 상품 종류 정보에 따른 타입 코드 (하단 참조) |
| `items[].maker` | string | 제조사명 |
| `items[].brand` | string | 브랜드명 |
| `items[].category1` | string | 상품의 대분류 카테고리 |
| `items[].category2` | string | 상품의 중분류 카테고리 |
| `items[].category3` | string | 상품의 소분류 카테고리 |
| `items[].category4` | string | 상품의 세분류 카테고리 |

### 상품 타입 코드 (`productType`)

| 구분 | 가격비교 상품 | 가격비교 비매칭 일반상품 | 가격비교 매칭 일반상품 |
| :--- | :---: | :---: | :---: |
| **일반 상품** | 1 | 2 | 3 |
| **중고 상품** | 4 | 5 | 6 |
| **단종 상품** | 7 | 8 | 9 |
| **판매예정 상품** | 10 | 11 | 12 |

### 응답 반환 예시 (JSON)
```json
{
  "lastBuildDate": "Tue, 04 Oct 2016 13:23:58 +0900",
  "total": 17161390,
  "start": 1,
  "display": 10,
  "items": [
    {
      "title": "허니트립 보스턴백",
      "link": "https://search.shopping.naver.com/...",
      "image": "https://shopping-phinf.pstatic.net/...",
      "lprice": 6700,
      "hprice": 0,
      "mallName": "허니트립",
      "productId": "10315467179",
      "productType": 2,
      "maker": "허니트립",
      "brand": "",
      "category1": "패션잡화",
      "category2": "여행용가방/소품",
      "category3": "보스턴백",
      "category4": ""
    }
  ]
}
```
