"""
Scrapling의 StealthyFetcher에서 page_setup과 page_action을 활용하여
트립닷컴 호텔 상세 페이지의 스크롤을 내리고 리뷰 API(soa2)를 가로채는 테스트 스크립트입니다.
"""
import json
import time
from playwright.sync_api import Page
from scrapling.fetchers import StealthyFetcher

# 인터셉트된 요청을 저장할 리스트
intercepted_apis = []

def setup_page(page: Page) -> Page:
    """
    페이지가 로드되기 전에 네트워크 요청을 모니터링하여
    soa2 관련 API 요청을 가로채고 기록합니다.
    """
    def handle_request(request):
        # soa2 또는 comment/review 관련 패턴 감지
        if "soa2" in request.url or "comment" in request.url.lower():
            # 유용한 요청 정보 추출
            req_info = {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
            }
            try:
                if request.post_data:
                    req_info["payload"] = request.post_data
            except Exception:
                pass
                
            intercepted_apis.append(req_info)
            print(f"\n[Captured API] {request.url}")
            
    page.on("request", handle_request)
    return page

def action_page(page: Page) -> Page:
    """
    페이지가 로드된 후 스크롤을 아래로 천천히 내려서
    리뷰 섹션을 동적으로 로드하도록 유도합니다.
    """
    print("Executing scroll action down the page...")
    # 총 8회에 걸쳐 1000픽셀씩 아래로 스크롤하면서 동적 요소를 로드
    for i in range(10):
        # scrollBy를 통해 현재 스크롤 위치 대비 상대적으로 이동
        page.evaluate("window.scrollBy(0, 1000)")
        print(f"Scrolled down {i+1}/10")
        page.wait_for_timeout(1500) # 1.5초 대기
        
    # 최종 스크롤 후 추가 동적 렌더링을 위해 대기
    page.wait_for_timeout(5000)
    return page

def run_test():
    target_url = (
        "https://kr.trip.com/hotels/detail/?cityEnName=Seoul&cityId=274&hotelId=58635410"
        "&checkIn=2026-06-22&checkOut=2026-06-23&adult=2&children=0&crn=1&ages=&curr=KRW&barcurr=KRW"
        "&hoteluniquekey=H4sIAAAAAAAA_-M6wcTFJMEkdZCJo3XuntdsQoxGBiv5La5mOR7-qhHTX1Tg4Nn6OnCHnGSRQwBPIQMYuDjMYJz08pf0RkbNmP5DXzOsHHYwMp1gbGtmWcD050OzwykWZo6XepdYDjFGVytlp1YqWZnoKJVkluSkKlkpvd7W8GoDCL3ZOeNNyw4lHaWU1OJkoASQlZibX5pXAmSbWloa6xkYAIVKEis8U8AGJCfmJJfmJJakhlQWAA0y01HKLHYuKcosCErNzSwpSQWqSkvMKU4FiQelFgNlksGCSn5AY4qgApn5eRDtBihiYYk5pakQNwAtdEuF2mFYG_uIhSk69hMLwy-gn1a5NrEydLEyTGJl4QB6dhcrR4iRc6CHka7hBdYNJ1ikFA0NDAyMTE2NzHUNEi0Tk40NknRNLE0NjE11DY1NDQ0szDR65y7_8c7YSPYUo5ShuamJpYWpubG5oaWhnqWFuXmeYXBOkkdOiQdjEJuloYWbi1uUDRezd1C4YMam-nlsPEX2UiCeIoynBeIZwniBsjtV9sYFuNpHwkSSWLPzdb2DMlaKFjA2MDJ1MXILMHowRjBWAHmMqxgZNjAy7mD8DwOMrxhB5gEA1rgozBECAAA"
        "&masterhotelid_tracelogid=100025527-0a9ac30b-495035-1351086"
        "&detailFilters=17%7C1%7E17%7E1*80%7C2%7C1%7E80%7E2*29%7C1%7E29%7E1%7C2&hotelType=normal&display=incavg&subStamp=714&isCT=true&isFlexible=F&locale=ko-KR"
    )
    
    print("Launching StealthyFetcher with page_setup and page_action...")
    try:
        page = StealthyFetcher.fetch(
            target_url, 
            headless=True, 
            page_setup=setup_page, 
            page_action=action_page,
            timeout=120000 # 타임아웃을 넉넉히 2분으로 설정
        )
        
        print("\n--- StealthyFetcher Execution Completed ---")
        print(f"Response Status: {page.status}")
        print(f"Captured {len(intercepted_apis)} soa2/comment APIs during execution.")
        
        # 캡처된 API 중 'getComment' 혹은 'comment' 관련 내용 검색 및 저장
        comment_apis = [api for api in intercepted_apis if "getComment" in api["url"] or "comment" in api["url"].lower()]
        print(f"Found {len(comment_apis)} specific comment/review APIs.")
        
        for idx, api in enumerate(comment_apis):
            print(f"\n[Comment API #{idx+1}]")
            print(f"URL: {api['url']}")
            if "payload" in api:
                print(f"Payload Preview: {api['payload'][:300]}...")
                
        # 모든 가로채진 API 요청을 저장
        with open("trip_com/src/action_intercepted.json", "w", encoding="utf-8") as f:
            json.dump(intercepted_apis, f, indent=4, ensure_ascii=False)
        print("\nSaved all intercepted requests to trip_com/src/action_intercepted.json")
        
        # 수집 후 HTML 소스 저장
        with open("trip_com/src/action_page_source.html", "w", encoding="utf-8") as f:
            f.write(page.html_content)
        print("Saved page HTML content to trip_com/src/action_page_source.html")
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    run_test()
