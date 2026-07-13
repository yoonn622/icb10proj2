"""
SQLite 데이터베이스(seoul_pops.db)에 연결하여 사전에 집계된 테이블들을 로드하고,
Streamlit 캐시(st.cache_data)를 활용하여 대시보드 로딩 성능을 극대화하는 데이터 로더 모듈입니다.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st

# 데이터베이스 경로 정의 (상대경로 규칙 준수)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "seoul_pops.db")

def get_db_connection():
    """
    SQLite 데이터베이스 파일에 연결을 반환합니다.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"SQLite DB 파일을 찾을 수 없습니다: {DB_PATH}. build_db.py를 먼저 가동해 주세요.")
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def load_mapping_data():
    """
    [SQLite 기반] 행정동 매핑 정보를 로드합니다.
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM mapping_info", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB 매핑 정보 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def get_aggregated_by_dong():
    """
    [SQLite 기반] 인구통계학적 분석용 구/동별 성별·연령대 집계 데이터를 반환합니다.
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM dong_demographics_agg", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB 인구통계 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def get_aggregated_by_time():
    """
    [SQLite 기반] 시간대별 생활인구 평균 패턴 테이블을 반환합니다.
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM time_pattern_agg", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB 시간대 패턴 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def get_sampled_data(sample_frac=0.01):
    """
    [SQLite 기반] 기술 통계 및 Box Plot 분석을 위한 사전 추출된 1% 균등 샘플 데이터를 반환합니다.
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM statistical_sample", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB 1% 통계 샘플 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def get_aggregated_for_district_map():
    """
    [SQLite 기반] 서울시 자치구(구별) 코로플리스 지도 시각화용 [구, 시간대, 날짜유형] 집계 데이터를 반환합니다.
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM district_map_agg", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB 구별 지도 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def get_aggregated_for_dong_map():
    """
    [SQLite 기반] 서울시 행정동(동별) 코로플리스 지도 시각화용 [동코드, 동명, 구, 시간대, 날짜유형] 집계 데이터를 반환합니다.
    """
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM dong_map_agg", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB 동별 지도 데이터 로드 실패: {e}")
        return pd.DataFrame()
