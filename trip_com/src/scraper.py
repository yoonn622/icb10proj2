# -*- coding: utf-8 -*-
"""
trip.com 호텔 리뷰 수집기 스크립트.
이 스크립트는 scrapling.Fetcher를 활용하여 실제 브라우저와 동일한 방식으로
Trip.com 호텔 리뷰 API에서 데이터를 요청하고, 이를 SQLite 데이터베이스에 구조화하여 저장합니다.
주요 기능:
- SQLite 데이터베이스 및 테이블 초기화
- 1페이지 테스트 수집 및 응답 구조 검증
- 전체 리뷰 수집 (페이지네이션 순회)
- 중복 방지 저장 및 안전한 랜덤 지연 처리
"""

import os
import sys
import time
import random
import json
import sqlite3
import math
from scrapling import Fetcher

# Windows 터미널에서 인코딩 에러 방지
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DB_DIR, 'reviews.db')

# API 관련 설정
HOTEL_ID = 58635410
API_URL = "https://kr.trip.com/restapi/soa2/34308/getHotelCommentInfo"

HEADERS = {
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
    "referer": f"https://kr.trip.com/hotels/detail/?cityEnName=Seoul&cityId=274&hotelId={HOTEL_ID}",
    "content-type": "application/json"
}

def init_db():
    """SQLite 데이터베이스 및 테이블을 초기화합니다."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
        print(f"[DB] 데이터 디렉토리를 생성했습니다: {DB_DIR}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 리뷰 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            nickname TEXT,
            avatar_url TEXT,
            create_date TEXT,
            checkin_date TEXT,
            rating INTEGER,
            rating_location INTEGER,
            rating_facility INTEGER,
            rating_service INTEGER,
            rating_room INTEGER,
            content TEXT,
            language TEXT,
            translated_content TEXT,
            translated_language TEXT,
            room_name TEXT,
            travel_type TEXT,
            useful_count INTEGER,
            recommend INTEGER,
            image_list TEXT,
            hotel_reply TEXT,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"[DB] 데이터베이스가 정상적으로 초기화되었습니다: {DB_PATH}")

def fetch_page(page_index, retry=3):
    """지정한 페이지의 리뷰 데이터를 Trip.com API로부터 가져옵니다."""
    payload = {
        "hotelId": HOTEL_ID,
        "commentFilterOptions": {
            "pageIndex": page_index,
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

    for attempt in range(1, retry + 1):
        try:
            print(f"[수집] {page_index} 페이지 요청 중... (시도 {attempt}/{retry})")
            response = Fetcher.post(API_URL, json=payload, headers=HEADERS)
            
            if response.status == 200:
                res_json = response.json()
                if res_json and "data" in res_json:
                    return res_json["data"]
                else:
                    print(f"[수집] {page_index} 페이지 응답에 'data' 필드가 없습니다.")
            else:
                print(f"[수집] 비정상 응답 코드: {response.status}")
        except Exception as e:
            print(f"[오류] {page_index} 페이지 수집 중 예외 발생: {e}")
        
        if attempt < retry:
            sleep_time = attempt * 2 + random.uniform(1.0, 3.0)
            print(f"[대기] {sleep_time:.2f}초 후 재시도합니다...")
            time.sleep(sleep_time)
            
    return None

def parse_and_save_reviews(data):
    """API 응답 데이터에서 리뷰 목록을 파싱하고 DB에 저장합니다."""
    if not data:
        return 0

    group_list = data.get("groupList", [])
    comments = []
    for group in group_list:
        if "commentList" in group:
            comments.extend(group["commentList"])

    if not comments:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved_count = 0

    for comment in comments:
        # 주요 데이터 파싱
        comment_id = comment.get("id")
        if not comment_id:
            continue

        user_info = comment.get("userInfo", {})
        nickname = user_info.get("nickName")
        avatar_url = user_info.get("avatarUrl")
        create_date = comment.get("createDate")
        checkin_date = comment.get("checkinDate")
        
        rating = comment.get("rating")
        rating_info = comment.get("ratingInfo", {})
        rating_location = rating_info.get("ratingLocation")
        rating_facility = rating_info.get("ratingFacility")
        rating_service = rating_info.get("ratingService")
        rating_room = rating_info.get("ratingRoom")

        content = comment.get("content")
        language = comment.get("language")
        translated_content = comment.get("translatedContent")
        translated_language = comment.get("translatedLanguage")

        room_name = comment.get("roomName")
        travel_type = comment.get("travelTypeText")
        useful_count = comment.get("usefulCount", 0)
        recommend = 1 if comment.get("recommend") else 0

        # 이미지 리스트 직렬화
        image_list = json.dumps(comment.get("imageList", []))

        # 호텔 답글 파싱 (feedbackList에 호텔 답변이 들어있음)
        hotel_reply = None
        feedback_list = comment.get("feedbackList", [])
        if feedback_list:
            # 호텔 답변 타입(일반적으로 3번)이나 내용을 모아서 하나의 텍스트로 저장
            replies = [f.get("content") for f in feedback_list if f.get("content")]
            if replies:
                hotel_reply = "\n".join(replies)

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO reviews (
                    id, nickname, avatar_url, create_date, checkin_date,
                    rating, rating_location, rating_facility, rating_service, rating_room,
                    content, language, translated_content, translated_language,
                    room_name, travel_type, useful_count, recommend, image_list, hotel_reply
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comment_id, nickname, avatar_url, create_date, checkin_date,
                rating, rating_location, rating_facility, rating_service, rating_room,
                content, language, translated_content, translated_language,
                room_name, travel_type, useful_count, recommend, image_list, hotel_reply
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"[오류] 리뷰 저장 실패 (ID: {comment_id}): {e}")

    conn.commit()
    conn.close()
    return saved_count

def main():
    print("[시작] Trip.com 리뷰 데이터 수집기를 가동합니다.")
    init_db()

    # 1. 1페이지 테스트 수집 및 확인
    print("\n--- 1단계: 1페이지 테스트 수집 시작 ---")
    first_page_data = fetch_page(page_index=1)
    
    if not first_page_data:
        print("[실패] 1페이지 수집에 실패했습니다. 수집 프로세스를 중단합니다.")
        return

    # 1페이지 데이터 저장 및 검증
    saved_first_page = parse_and_save_reviews(first_page_data)
    print(f"[성공] 1페이지 저장 완료 (새로 저장된 리뷰: {saved_first_page}개)")

    # 2. 전체 리뷰 수 확인 및 전체 수집 진행
    total_count = first_page_data.get("totalCount", 0)
    page_size = 10
    total_pages = math.ceil(total_count / page_size)
    print(f"\n--- 2단계: 전체 리뷰 수집 시작 ---")
    print(f"전체 리뷰 개수: {total_count}개 | 필요 페이지 수: {total_pages}개")

    # 1페이지는 이미 완료했으므로 2페이지부터 순회
    accumulated_saved = saved_first_page
    
    for page in range(2, total_pages + 1):
        # 차단 방지를 위한 랜덤 딜레이
        delay = random.uniform(1.2, 2.8)
        print(f"[대기] 다음 요청까지 {delay:.2f}초 대기합니다...")
        time.sleep(delay)

        page_data = fetch_page(page_index=page)
        if page_data:
            saved = parse_and_save_reviews(page_data)
            accumulated_saved += saved
            print(f"[저장] {page}/{total_pages} 페이지 수집 완료 (누적 새로 저장: {accumulated_saved}개)")
        else:
            print(f"[경고] {page} 페이지 수집 실패. 계속 진행합니다.")

    # 3. 수집 결과 요약
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reviews")
    db_total = cursor.fetchone()[0]
    conn.close()

    print("\n--- 수집 프로세스 종료 ---")
    print(f"목표 리뷰 개수: {total_count}개")
    print(f"새롭게 수집 및 저장된 리뷰 개수: {accumulated_saved}개")
    print(f"현재 DB에 총 저장된 리뷰 개수: {db_total}개")
    print(f"DB 파일 위치: {DB_PATH}")

if __name__ == "__main__":
    main()
