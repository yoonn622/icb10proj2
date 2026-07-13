"""
서울시 생활인구 Parquet 데이터와 엑셀 매핑 정보 데이터를 미리 결합·집계하여
SQLite 데이터베이스 파일(seoul_pops.db)을 빌드하는 일회성 전처리 파이프라인 스크립트입니다.
"""

import os
import sqlite3
import pandas as pd
import numpy as np

# 경로 정의
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, "data", "LOCAL_PEOPLE_DONG_202606_tidy.parquet")
EXCEL_PATH = os.path.join(BASE_DIR, "data", "행정동코드_매핑정보_20241218.xlsx")
DB_PATH = os.path.join(BASE_DIR, "data", "seoul_pops.db")

def build_database():
    print("=== SQLite 데이터베이스 빌드 프로세스 시작 ===")
    
    # 1. 엑셀 매핑 정보 로드
    print("1. 행정동코드 매핑 정보 엑셀 파일 로딩 중...")
    df_map = pd.read_excel(EXCEL_PATH)
    if df_map.iloc[0]['시도명'] == 'DO_NM':
        df_map = df_map.iloc[1:].reset_index(drop=True)
    
    # 타입 정비
    df_map['행자부행정동코드'] = df_map['행자부행정동코드'].astype(str)
    df_map['통계청행정동코드'] = df_map['통계청행정동코드'].astype(str)
    
    # 2. 원본 Parquet 데이터 로드
    print("2. 원본 Parquet 데이터 로딩 중 (약 850만 행)...")
    df_raw = pd.read_parquet(PARQUET_PATH)
    df_raw['행정동코드'] = df_raw['행정동코드'].astype(str)
    df_raw['기준일ID'] = df_raw['기준일ID'].astype(str)
    
    # 3. [최적화] 요일 매핑 (주중/주말 파생 필드 생성)
    print("3. 날짜 유형(주중/주말) 고속 벡터 매핑 중...")
    unique_dates = df_raw['기준일ID'].unique()
    date_series = pd.to_datetime(unique_dates, format='%Y%m%d')
    date_type_map = {d: ('주말' if w >= 5 else '주중') for d, w in zip(unique_dates, date_series.dayofweek)}
    df_raw['날짜유형'] = df_raw['기준일ID'].map(date_type_map)
    
    # 4. 데이터 병합 (통계청 행정동코드, 자치구명, 행정동명 결합)
    print("4. 두 데이터 소스 병합 및 결측치 보정 중...")
    df_merged = pd.merge(
        df_raw,
        df_map[['행자부행정동코드', '통계청행정동코드', '시군구명', '행정동명']],
        left_on='행정동코드',
        right_on='행자부행정동코드',
        how='left'
    )
    
    if '행자부행정동코드' in df_merged.columns:
        df_merged.drop(columns=['행자부행정동코드'], inplace=True)
        
    df_merged['시군구명'] = df_merged['시군구명'].fillna('미분류')
    df_merged['행정동명'] = df_merged['행정동명'].fillna('미분류')
    df_merged['통계청행정동코드'] = df_merged['통계청행정동코드'].fillna('미분류')
    
    # 5. SQLite 연결 객체 생성
    print("5. SQLite DB 접속 및 집계 테이블 생성 시작...")
    conn = sqlite3.connect(DB_PATH)
    
    # --- [집계 1] 구별 지도 시각화용 데이터 (district_map_agg) ---
    print("   - 자치구별 지도 시각화 테이블 생성 중...")
    df_dist_type = df_merged.groupby(['시군구명', '시간대구분', '날짜유형'], as_index=False, observed=False)['생활인구수'].mean()
    df_dist_total = df_merged.groupby(['시군구명', '시간대구분'], as_index=False, observed=False)['생활인구수'].mean()
    df_dist_total['날짜유형'] = '전체'
    df_dist_agg = pd.concat([df_dist_type, df_dist_total], ignore_index=True)
    df_dist_agg.to_sql('district_map_agg', conn, if_exists='replace', index=False)
    
    # --- [집계 2] 동별 지도 시각화용 데이터 (dong_map_agg) ---
    print("   - 행정동별 지도 시각화 테이블 생성 중 (시간 소요)...")
    df_dong_type = df_merged.groupby(['통계청행정동코드', '행정동명', '시군구명', '시간대구분', '날짜유형'], as_index=False, observed=False)['생활인구수'].mean()
    df_dong_total = df_merged.groupby(['통계청행정동코드', '행정동명', '시군구명', '시간대구분'], as_index=False, observed=False)['생활인구수'].mean()
    df_dong_total['날짜유형'] = '전체'
    df_dong_agg = pd.concat([df_dong_type, df_dong_total], ignore_index=True)
    df_dong_agg.to_sql('dong_map_agg', conn, if_exists='replace', index=False)
    
    # --- [집계 3] 동별 성/연령 상세 데이터 (dong_demographics_agg) ---
    print("   - 인구통계학적 특성용 자치구/행정동별 집계 테이블 생성 중...")
    df_demo_agg = df_merged.groupby(['시군구명', '행정동명', '성별', '연령대'], as_index=False, observed=False)['생활인구수'].sum()
    df_demo_agg.to_sql('dong_demographics_agg', conn, if_exists='replace', index=False)
    
    # --- [집계 4] 시간대별 추이 데이터 (time_pattern_agg) ---
    print("   - 시간대별 추이 분석용 집계 테이블 생성 중...")
    df_time_agg = df_merged.groupby(['시군구명', '행정동명', '시간대구분'], as_index=False, observed=False)['생활인구수'].mean()
    df_time_agg.to_sql('time_pattern_agg', conn, if_exists='replace', index=False)
    
    # --- [집계 5] 1% 통계용 샘플 데이터 (statistical_sample) ---
    print("   - 1% 통계용 균등 샘플 추출 및 테이블 생성 중...")
    df_sample = df_merged.sample(frac=0.01, random_state=42).reset_index(drop=True)
    df_sample.to_sql('statistical_sample', conn, if_exists='replace', index=False)
    
    # --- [집계 6] 매핑 메타데이터 테이블 (mapping_info) ---
    print("   - 기본 매핑 정보 메타테이블 생성 중...")
    df_map.to_sql('mapping_info', conn, if_exists='replace', index=False)
    
    # 커밋 및 닫기
    conn.commit()
    conn.close()
    
    print("\n=== SQLite 데이터베이스 빌드 완료 ===")
    print(f"DB 파일 위치: {DB_PATH}")
    print(f"파일 용량: {os.path.getsize(DB_PATH) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    build_database()
