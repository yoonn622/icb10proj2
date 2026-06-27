# -*- coding: utf-8 -*-
"""
trip.com 수집된 리뷰 데이터베이스 검증 스크립트.
이 스크립트는 trip_com/data/reviews.db에 저장된 리뷰 데이터들의 무결성을 확인하고,
총 레코드 수, 평점 통계, 그리고 데이터 샘플 일부를 출력하여 정상 수집 여부를 검증합니다.
"""

import os
import sys
import sqlite3
import json

# Windows 터미널에서 인코딩 에러 방지
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'reviews.db')

def verify_data():
    if not os.path.exists(DB_PATH):
        print(f"[오류] DB 파일이 존재하지 않습니다: {DB_PATH}")
        return

    print(f"[검증] DB 파일 로드 중: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 총 리뷰 개수 확인
    cursor.execute("SELECT COUNT(*) FROM reviews")
    total_count = cursor.fetchone()[0]
    print(f"1. 총 수집된 리뷰 개수: {total_count}개")

    if total_count == 0:
        print("[경고] 데이터베이스가 비어 있습니다.")
        conn.close()
        return

    # 2. 평점 관련 기초 통계
    cursor.execute("""
        SELECT 
            AVG(rating), MIN(rating), MAX(rating),
            AVG(rating_location), AVG(rating_facility), AVG(rating_service), AVG(rating_room)
        FROM reviews
    """)
    stats = cursor.fetchone()
    print("\n2. 평점 통계 정보:")
    print(f"   - 전체 평점 평균: {stats[0]:.2f} (최소: {stats[1]}, 최대: {stats[2]})")
    print(f"   - 위치 평점 평균: {stats[3]:.2f}" if stats[3] else "   - 위치 평점 평균: 데이터 없음")
    print(f"   - 시설 평점 평균: {stats[4]:.2f}" if stats[4] else "   - 시설 평점 평균: 데이터 없음")
    print(f"   - 서비스 평점 평균: {stats[5]:.2f}" if stats[5] else "   - 서비스 평점 평균: 데이터 없음")
    print(f"   - 객실 평점 평균: {stats[6]:.2f}" if stats[6] else "   - 객실 평점 평균: 데이터 없음")

    # 3. 예약 룸 정보 종류 통계
    cursor.execute("SELECT room_name, COUNT(*) FROM reviews GROUP BY room_name ORDER BY COUNT(*) DESC")
    rooms = cursor.fetchall()
    print("\n3. 예약 객실 타입 분포:")
    for room, count in rooms[:5]:
        room_name = room if room else "미지정"
        print(f"   - {room_name}: {count}개")
    if len(rooms) > 5:
        print(f"   - 외 {len(rooms) - 5}개 타입 더 있음")

    # 4. 샘플 리뷰 출력 (최신 작성일 기준 3개)
    cursor.execute("""
        SELECT id, nickname, create_date, rating, content, translated_content, language
        FROM reviews 
        ORDER BY create_date DESC 
        LIMIT 3
    """)
    samples = cursor.fetchall()
    print("\n4. 최신 리뷰 샘플 (최대 3개):")
    for idx, row in enumerate(samples, 1):
        r_id, nick, c_date, rate, content, trans_content, lang = row
        print(f"   [{idx}] ID: {r_id} | 닉네임: {nick} | 작성일: {c_date} | 평점: {rate}")
        print(f"       언어: {lang}")
        
        # 본문 출력 (안전하게 인코딩 처리)
        safe_content = content.encode('utf-8', errors='replace').decode('utf-8')
        print(f"       본문: {safe_content[:150]}...")
        
        if trans_content:
            safe_trans = trans_content.encode('utf-8', errors='replace').decode('utf-8')
            print(f"       번역: {safe_trans[:150]}...")
        print("-" * 50)

    # 5. 다국어 리뷰 통계
    cursor.execute("SELECT language, COUNT(*) FROM reviews GROUP BY language ORDER BY COUNT(*) DESC")
    languages = cursor.fetchall()
    print("\n5. 작성 언어별 통계:")
    for lang, count in languages:
        lang_name = lang if lang else "미지정"
        print(f"   - {lang_name}: {count}개")

    conn.close()

if __name__ == "__main__":
    verify_data()
