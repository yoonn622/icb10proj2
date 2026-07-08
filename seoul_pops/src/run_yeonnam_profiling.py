"""
서울시 생활인구 Tidy-Data 데이터셋에서 연남동(행정동코드: 11440710) 데이터만 필터링하고
Matplotlib 한글 폰트(맑은 고딕)를 강제 적용하여 한글 깨짐이 완벽히 해결된
fg-data-profiling(ydata-profiling) 데이터 프로파일링 리포트(HTML)를 생성하는 스크립트입니다.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import koreanize_matplotlib
import sys
import os


try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Matplotlib 한글 폰트 설정 (ydata-profiling 내부 차트 렌더링용 폰트 확보)
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rcParams['axes.unicode_minus'] = False

# ydata-profiling 임포트
from ydata_profiling import ProfileReport

def main():
    parquet_path = "seoul_pops/data/LOCAL_PEOPLE_DONG_202606_tidy.parquet"
    xlsx_path = "seoul_pops/data/행정동코드_매핑정보_20241218.xlsx"
    output_html_path = "seoul_pops/report/yeonnam_data_profiling.html"
    
    print("=== [1] 데이터 로드 및 연남동 필터링 ===")
    df = pd.read_parquet(parquet_path)
    
    # 연남동 행정동코드 11440710 필터링
    df_yeonnam = df[df['행정동코드'].astype(str) == '11440710'].copy()
    
    # 명칭 조인 추가 (보고서에 행정동명이 확실히 표기되도록 함)
    df_map = pd.read_excel(xlsx_path, sheet_name='행정동코드').iloc[1:]
    df_map['행자부행정동코드'] = df_map['행자부행정동코드'].astype(str)
    code_to_name = dict(zip(df_map['행자부행정동코드'], df_map['행정동명']))
    df_yeonnam['행정동명'] = df_yeonnam['행정동코드'].astype(str).map(code_to_name)

    # 기본 중요 파생 변수 결합 (시간대별, 요일별 분석을 강화하기 위해 주중/주말 및 요일명 추가)
    print("=== [2] 요일 및 주중/주말 파생변수 생성 ===")
    date_series = pd.to_datetime(df_yeonnam['기준일ID'].astype(str), format='%Y%m%d')
    df_yeonnam['요일'] = date_series.dt.day_name()
    
    weekday_map = {
        'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
        'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
    }
    df_yeonnam['요일_kor'] = df_yeonnam['요일'].map(weekday_map)
    df_yeonnam['요일_kor'] = pd.Categorical(df_yeonnam['요일_kor'], 
                                   categories=['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'], 
                                   ordered=True)
    
    df_yeonnam['주중_주말'] = np.where(df_yeonnam['요일'].isin(['Saturday', 'Sunday']), '주말', '주중')
    df_yeonnam['주중_주말'] = df_yeonnam['주중_주말'].astype('category')
    
    # 임시 영문 요일 컬럼 삭제
    df_yeonnam = df_yeonnam.drop(columns=['요일'])
    
    # 최종 분석할 카테고리 컬럼 순서 지정 및 정제
    df_yeonnam['기준일ID'] = df_yeonnam['기준일ID'].astype('category')
    df_yeonnam['행정동코드'] = df_yeonnam['행정동코드'].astype('category')
    df_yeonnam['성별'] = df_yeonnam['성별'].astype('category')
    df_yeonnam['연령대'] = df_yeonnam['연령대'].astype('category')
    df_yeonnam['행정동명'] = df_yeonnam['행정동명'].astype('category')
    
    print(f"Yeonnam-dong data shape for profiling: {df_yeonnam.shape}")
    
    print("=== [3] fg-data-profiling (ydata-profiling) 보고서 빌드 ===")
    # 연남동 데이터 전체(20,160행)에 대해 세부 프로파일링 수행 (한글 폰트 적용 상태)
    profile = ProfileReport(
        df_yeonnam, 
        title="서울시 마포구 연남동 생활인구 데이터 프로파일링 보고서", 
        minimal=True
    )
    
    print("=== [4] HTML 파일 저장 ===")
    profile.to_file(output_html_path)
    print(f"연남동 HTML 프로파일링 리포트가 성공적으로 저장되었습니다: {output_html_path}")

if __name__ == "__main__":
    main()
