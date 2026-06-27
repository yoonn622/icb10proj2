# -*- coding: utf-8 -*-
"""
trip.com 호텔 리뷰 API 수집 테스트 스크립트.
이 스크립트는 scrapling Fetcher를 활용하여 지정된 API로부터 첫 페이지 리뷰 데이터를 가져오고 구조를 분석합니다.
"""
import json
from scrapling import Fetcher

def test_api():
    url = "https://kr.trip.com/restapi/soa2/34308/getHotelCommentInfo"
    
    headers = {
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "w-payload-source": "1.0.9@102!Nudtz1KLhCAbOX4SO6An9PKnG2KLOSqZOlbn+6FaG6OaKSbpKET2OSVbOrK2+ET5+rApbbbpOSknKr42+rG2KlqIbEVbKtb5+rbSOEb2KE4p+rKpOr4nKrq/K5bpOSqL+rk/OSKZKrVpQlVROShDKFO3GVd3hbb=",
        "x-ctx-country": "KR",
        "x-ctx-currency": "KRW",
        "x-ctx-locale": "ko-KR",
        "x-ctx-ubt-pageid": "10320668147",
        "x-ctx-ubt-pvid": "7",
        "x-ctx-ubt-sid": "9",
        "x-ctx-ubt-vid": "1754985737191.9877n1SlbHlt",
        "x-ctx-user-recognize": "NON_EU",
        "x-ctx-wclient-req": "0af33fe7acb74bcfe9f82cf404544b46",
        "referer": "https://kr.trip.com/hotels/detail/?cityEnName=Seoul&cityId=274&hotelId=58635410",
        "content-type": "application/json"
    }

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
            "cid": "1754985737191.9877n1SlbHlt",
            "bu": "IBU",
            "group": "trip",
            "aid": "",
            "sid": "",
            "ouid": "",
            "locale": "ko-KR",
            "timezone": "9",
            "currency": "KRW",
            "pageId": "10320668147",
            "vid": "1754985737191.9877n1SlbHlt",
            "guid": "",
            "isSSR": False
        }
    }

    print("Fetching reviews...")
    response = Fetcher.post(url, json=payload, headers=headers)
    print("Status code:", response.status)
    
    try:
        res_json = response.json()
        print("Successfully parsed JSON!")
        inner_data = res_json.get("data", {})
        group_list = inner_data.get("groupList", [])
        
        comments = []
        for group in group_list:
            if "commentList" in group:
                comments.extend(group["commentList"])
        
        import sys
        # Windows 터미널에서 인코딩 오류 방지
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            
        print(f"Total extracted comments in this page: {len(comments)}")
        if len(comments) > 0:
            print("--- First Comment Keys and Snippets ---")
            first = comments[0]
            for k, v in first.items():
                val_str = str(v)
                if len(val_str) > 100:
                    val_str = val_str[:100] + "..."
                # 터미널 출력이 안 깨지도록 안전하게 인코딩 처리
                safe_val = val_str.encode('utf-8', errors='replace').decode('utf-8')
                print(f"  {k} ({type(v).__name__}): {safe_val}")
            print("----------------------------")
        else:
            print("No comments found.")
    except Exception as e:
        print("Failed to process. Error:", e)

if __name__ == "__main__":
    test_api()
