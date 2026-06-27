"""
트립닷컴 호텔 상세 페이지에서 백엔드 API 요청(soa2 등)을 가로채고(Intercept),
페이지 HTML 구조를 저장하여 DOM 선택자 분석을 지원하는 테스트 스크립트입니다.
"""
import json
import time
from playwright.sync_api import sync_playwright

from scrapling.fetchers import StealthyFetcher

def intercept_api():
    print("Starting Playwright to intercept Trip.com API requests...")
    
    target_url = (
        "https://kr.trip.com/hotels/detail/?cityEnName=Seoul&cityId=274&hotelId=58635410"
        "&checkIn=2026-06-22&checkOut=2026-06-23&adult=2&children=0&crn=1&ages=&curr=KRW&barcurr=KRW"
        "&hoteluniquekey=H4sIAAAAAAAA_-M6wcTFJMEkdZCJo3XuntdsQoxGBiv5La5mOR7-qhHTX1Tg4Nn6OnCHnGSRQwBPIQMYuDjMYJz08pf0RkbNmP5DXzOsHHYwMp1gbGtmWcD050OzwykWZo6XepdYDjFGVytlp1YqWZnoKJVkluSkKlkpvd7W8GoDCL3ZOeNNyw4lHaWU1OJkoASQlZibX5pXAmSbWloa6xkYAIVKEis8U8AGJCfmJJfmJJakhlQWAA0y01HKLHYuKcosCErNzSwpSQWqSkvMKU4FiQelFgNlksGCSn5AY4qgApn5eRDtBihiYYk5pakQNwAtdEuF2mFYG_uIhSk69hMLwy-gn1a5NrEydLEyTGJl4QB6dhcrR4iRc6CHka7hBdYNJ1ikFA0NDAyMTE2NzHUNEi0Tk40NknRNLE0NjE11DY1NDQ0szDR65y7_8c7YSPYUo5ShuamJpYWpubG5oaWhnqWFuXmeYXBOkkdOiQdjEJuloYWbi1uUDRezd1C4YMam-nlsPEX2UiCeIoynBeIZwniBsjtV9sYFuNpHwkSSWLPzdb2DMlaKFjA2MDJ1MXILMHowRjBWAHmMqxgZNjAy7mD8DwOMrxhB5gEA1rgozBECAAA"
        "&masterhotelid_tracelogid=100025527-0a9ac30b-495035-1351086"
        "&detailFilters=17%7C1%7E17%7E1*80%7C2%7C1%7E80%7E2*29%7C1%7E29%7E1%7C2&hotelType=normal&display=incavg&subStamp=714&isCT=true&isFlexible=F&locale=ko-KR"
    )

    intercepted_requests = []

    with sync_playwright() as p:
        # User-Agent 설정 및 브라우저 시작
        browser = p.chromium.launch(headless=True)
        # 일반적인 브라우저처럼 보이기 위해 context 옵션 지정
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()

        # 네트워크 요청 인터셉트 설정
        def handle_request(request):
            if "soa2" in request.url or "getComment" in request.url:
                try:
                    payload = request.post_data
                    headers = request.headers
                    intercepted_requests.append({
                        "url": request.url,
                        "method": request.method,
                        "headers": headers,
                        "payload": payload
                    })
                    print(f"\n[Intercepted Request] URL: {request.url}")
                except Exception as e:
                    pass

        page.on("request", handle_request)

        print("Navigating to Trip.com hotel page...")
        page.goto(target_url, wait_until="networkidle", timeout=60000)
        
        # 리뷰 섹션이 로드되도록 아래로 스크롤
        print("Scrolling down to load review section...")
        for _ in range(5):
            page.mouse.wheel(0, 1000)
            time.sleep(1)

        # 리뷰 탭이 있다면 강제로 클릭 시도하거나 기다림
        # HTML DOM에서 리뷰 요소를 찾아 출력해보기
        time.sleep(5) # 추가 로딩 대기
        
        print("\nChecking for page elements...")
        # 페이지 소스 일부 저장 및 리뷰 목록 파싱 시도
        # trip.com의 현재 리뷰 구조를 알아내기 위해 리뷰 텍스트를 포함하고 있는 class나 tag 검사
        reviews = page.locator(".review-item, .comment-item, [class*='comment'], [class*='review']").all()
        print(f"Found {len(reviews)} potential review/comment elements via basic locators.")
        
        # 만약 리뷰 아이템이 안 나온다면, 전체 html을 검사하여 리뷰 본문 키워드로 클래스 역추적
        html_content = page.content()
        with open("trip_com/src/page_source.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Saved page source to trip_com/src/page_source.html")

        # 인터셉트 결과 저장
        with open("trip_com/src/intercepted.json", "w", encoding="utf-8") as f:
            json.dump(intercepted_requests, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(intercepted_requests)} intercepted requests to trip_com/src/intercepted.json")
        
        browser.close()

if __name__ == "__main__":
    intercepted = intercept_api()
