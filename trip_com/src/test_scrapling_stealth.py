"""
Scrapling의 StealthyFetcher를 사용하여 트립닷컴 호텔 상세 페이지의
로그인 리다이렉션을 우회할 수 있는지 테스트하는 스크립트입니다.
"""
import sys
from scrapling.fetchers import StealthyFetcher

def test_stealth_fetch():
    target_url = (
        "https://kr.trip.com/hotels/detail/?cityEnName=Seoul&cityId=274&hotelId=58635410"
        "&checkIn=2026-06-22&checkOut=2026-06-23&adult=2&children=0&crn=1&ages=&curr=KRW&barcurr=KRW"
        "&hoteluniquekey=H4sIAAAAAAAA_-M6wcTFJMEkdZCJo3XuntdsQoxGBiv5La5mOR7-qhHTX1Tg4Nn6OnCHnGSRQwBPIQMYuDjMYJz08pf0RkbNmP5DXzOsHHYwMp1gbGtmWcD050OzwykWZo6XepdYDjFGVytlp1YqWZnoKJVkluSkKlkpvd7W8GoDCL3ZOeNNyw4lHaWU1OJkoASQlZibX5pXAmSbWloa6xkYAIVKEis8U8AGJCfmJJfmJJakhlQWAA0y01HKLHYuKcosCErNzSwpSQWqSkvMKU4FiQelFgNlksGCSn5AY4qgApn5eRDtBihiYYk5pakQNwAtdEuF2mFYG_uIhSk69hMLwy-gn1a5NrEydLEyTGJl4QB6dhcrR4iRc6CHka7hBdYNJ1ikFA0NDAyMTE2NzHUNEi0Tk40NknRNLE0NjE11DY1NDQ0szDR65y7_8c7YSPYUo5ShuamJpYWpubG5oaWhnqWFuXmeYXBOkkdOiQdjEJuloYWbi1uUDRezd1C4YMam-nlsPEX2UiCeIoynBeIZwniBsjtV9sYFuNpHwkSSWLPzdb2DMlaKFjA2MDJ1MXILMHowRjBWAHmMqxgZNjAy7mD8DwOMrxhB5gEA1rgozBECAAA"
        "&masterhotelid_tracelogid=100025527-0a9ac30b-495035-1351086"
        "&detailFilters=17%7C1%7E17%7E1*80%7C2%7C1%7E80%7E2*29%7C1%7E29%7E1%7C2&hotelType=normal&display=incavg&subStamp=714&isCT=true&isFlexible=F&locale=ko-KR"
    )

    print("Fetching page using Scrapling StealthyFetcher (headless=True)...")
    try:
        # network_idle=True 옵션으로 리소스가 완전히 로드될 때까지 대기
        page = StealthyFetcher.fetch(target_url, headless=True, timeout=60000)
        
        print(f"Page Object Type: {type(page)}")
        print(f"Status Code: {page.status}")
        
        body_len = len(page.body) if page.body else 0
        text_len = len(page.text) if page.text else 0
        html_content_len = len(page.html_content) if page.html_content else 0
        
        print(f"Body Length: {body_len} bytes")
        print(f"Text Length: {text_len} bytes")
        print(f"HTML Content Length: {html_content_len} bytes")
        
        # HTML 내용 미리보기
        if page.html_content:
            print(f"HTML Preview (first 300 chars):\n{page.html_content[:300]}")
            # HTML 저장
            with open("trip_com/src/stealth_page_source.html", "w", encoding="utf-8") as f:
                f.write(page.html_content)
            print("Saved source to trip_com/src/stealth_page_source.html")
        else:
            print("No HTML Content found!")
            
        # title 요소 추출해보기
        title_nodes = page.css("title")
        if title_nodes:
            print(f"Title: {[node.text for node in title_nodes]}")
        else:
            print("Title element not found via CSS Selector")

        # captured_xhr 확인
        if hasattr(page, "captured_xhr") and page.captured_xhr:
            print(f"\n[Success] Captured {len(page.captured_xhr)} XHR requests!")
            for idx, request in enumerate(page.captured_xhr):
                print(f"[{idx}] URL: {request.get('url') or request}")
                # 혹시 리뷰 API가 있다면 페이로드 정보도 같이 출력해보기 위해
                if "getComment" in str(request) or "soa2" in str(request):
                    print(f"    -> Found matching API: {request}")
        else:
            print("\nNo XHR requests captured.")



        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_stealth_fetch()
