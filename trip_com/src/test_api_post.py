"""
인터셉트한 헤더와 페이로드를 사용하여 트립닷컴 호텔 리뷰 API(getHotelCommentInfo)로
직접 POST 요청을 전송하고, 리뷰 데이터를 JSON으로 수집할 수 있는지 테스트하는 스크립트입니다.
"""
import json
import requests

def test_direct_post():
    url = "https://kr.trip.com/restapi/soa2/34308/getHotelCommentInfo"
    
    # test_stealth_action.py에서 획득한 헤더 정보 그대로 복사
    # (x-ctx-wclient-req 등의 토큰이 일시적인지 테스트하기 위함)
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "cookie": "GUID=09034092419999315550; nfes_isSupportWebP=1; ibulanguage=KR; ibulocale=ko_kr; cookiePricesDisplayed=KRW; ibu_country=KR; ibu_cookie_strict=0; ibusite=KR; ibugroup=trip; Union=AllianceID=1078328&SID=2036522&OUID=ctag.hash.p0fpTrxOj2Jv&Expires=1784722508803&createtime=1782130508; UBT_VID=1782130508820.284982VOoo8P; IBU_showtotalamt=2; _bfa=1.1782130508820.284982VOoo8P.1.1782130510532.1782130510532.1.1.10320668147; intl_ht1=h4%3D274_58635410",
        "origin": "https://kr.trip.com",
        "referer": "https://kr.trip.com/hotels/detail/?cityEnName=Seoul&cityId=274&hotelId=58635410&checkIn=2026-06-22&checkOut=2026-06-23&adult=2&children=0&crn=1&ages=&curr=KRW&barcurr=KRW&hoteluniquekey=H4sIAAAAAAAA_-M6wcTFJMEkdZCJo3XuntdsQoxGBiv5La5mOR7-qhHTX1Tg4Nn6OnCHnGSRQwBPIQMYuDjMYJz08pf0RkbNmP5DXzOsHHYwMp1gbGtmWcD050OzwykWZo6XepdYDjFGVytlp1YqWZnoKJVkluSkKlkpvd7W8GoDCL3ZOeNNyw4lHaWU1OJkoASQlZibX5pXAmSbWloa6xkYAIVKEis8U8AGJCfmJJfmJJakhlQWAA0y01HKLHYuKcosCErNzSwpSQWqSkvMKU4FiQelFgNlksGCSn5AY4qgApn5eRDtBihiYYk5pakQNwAtdEuF2mFYG_uIhSk69hMLwy-gn1a5NrEydLEyTGJl4QB6dhcrR4iRc6CHka7hBdYNJ1ikFA0NDAyMTE2NzHUNEi0Tk40NknRNLE0NjE11DY1NDQ0szDR65y7_8c7YSPYUo5ShuamJpYWpubG5oaWhnqWFuXmeYXBOkkdOiQdjEJuloYWbi1uUDRezd1C4YMam-nlsPEX2UiCeIoynBeIZwniBsjtV9sYFuNpHwkSSWLPzdb2DMlaKFjA2MDJ1MXILMHowRjBWAHmMqxgZNjAy7mD8DwOMrxhB5gEA1rgozBECAAA&masterhotelid_tracelogid=100025527-0a9ac30b-495035-1351086&detailFilters=17%7C1%7E17%7E1*80%7C2%7C1%7E80%7E2*29%7C1%7E29%7E1%7C2&hotelType=normal&display=incavg&subStamp=714&isCT=true&isFlexible=F&locale=ko-KR",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "cookieorigin": "https://kr.trip.com",
        "currency": "KRW",
        "locale": "ko-KR",
        "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Chromium\";v=\"148\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "x-ctx-country": "KR",
        "x-ctx-currency": "KRW",
        "x-ctx-locale": "ko-KR",
        "x-ctx-ubt-pageid": "10320668147",
        "x-ctx-ubt-pvid": "1",
        "x-ctx-ubt-sid": "1",
        "x-ctx-ubt-vid": "1782130508820.284982VOoo8P",
        "x-ctx-wclient-req": "d08b0c06db3c15bf22c1d19ec3f60a16"
    }

    # test_stealth_action.py에서 획득한 Payload 그대로 사용
    payload = {
        "hotelId": 58635410,
        "commentFilterOptions": {
            "pageIndex": 1,
            "pageSize": 10,
            "repeatComment": 1
        },
        "sceneTypes": ["CommentList"],
        "head": {
            "platform": "PC",
            "cver": "0",
            "cid": "1782130508820.284982VOoo8P",
            "bu": "IBU",
            "group": "trip",
            "aid": "1078328",
            "sid": "2036522",
            "ouid": "ctag.hash.p0fpTrxOj2Jv",
            "locale": "ko-KR",
            "region": "KR",
            "timezone": "9",
            "currency": "KRW",
            "pageId": "10320668147",
            "vid": "1782130508820.284982VOoo8P",
            "guid": "",
            "isSSR": False,
            "extension": [
                {"name": "cityId", "value": ""},
                {"name": "checkIn", "value": "2026-06-22"},
                {"name": "checkOut", "value": "2026-06-23"}
            ]
        }
    }

    print("Sending POST request to Trip.com comment API...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            res_json = response.json()
            print("Successfully received JSON response!")
            
            # 응답 구조 요약 출력
            print(f"Keys in response: {list(res_json.keys())}")
            
            # 'commentInfo'나 'commentList'가 있는지 확인
            # 트립닷컴의 실제 API 키 명칭을 알아보기 위함
            for key in ["commentInfo", "comments", "commentList", "result"]:
                if key in res_json:
                    print(f"Found key '{key}' in response.")
            
            # 응답 JSON 전문 저장
            with open("trip_com/src/post_response.json", "w", encoding="utf-8") as f:
                json.dump(res_json, f, indent=4, ensure_ascii=False)
            print("Saved response JSON to trip_com/src/post_response.json")
            
            # 구조 파악을 위한 데이터 샘플 출력
            comment_items = res_json.get("commentItems", [])
            print(f"Found {len(comment_items)} reviews in commentItems.")
            
            if comment_items:
                first_review = comment_items[0]
                print("\n[First Review Sample]")
                print(f"Title / Header: {first_review.get('title') or first_review.get('recommendText')}")
                print(f"Score / Rating: {first_review.get('rating') or first_review.get('ratingScore')}")
                print(f"Content: {first_review.get('content')[:150] if first_review.get('content') else 'No content'}...")
            else:
                # 혹시 다른 키에 들어있는지 확인하기 위해 상위 500자 텍스트 출력
                print(f"Raw Response snippet: {response.text[:500]}")
        else:
            print(f"Failed to fetch data. Body: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_post = test_direct_post()
