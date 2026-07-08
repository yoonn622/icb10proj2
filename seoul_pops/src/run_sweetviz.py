"""
서울시 생활인구 Tidy-Data 데이터셋에 대해 중요 파생변수(행정동명, 요일_kor, 주중_주말)를 결합하고,
한글 폰트 깨짐 방지 설정을 적용하여 Sweetviz 데이터 프로파일링 리포트(HTML)를 생성하는 스크립트입니다.
"""

import pandas as pd
import numpy as np
import sweetviz as sv
import matplotlib.pyplot as plt
import matplotlib
import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# 1. Matplotlib 전역 한글 폰트 적용 (맑은 고딕)
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rcParams['axes.unicode_minus'] = False

# 2. Sweetviz 라이브러리 자체 한글/CJK 폰트 활성화 설정 주입 (가장 중요)
sv.config_parser.set("General", "use_cjk_font", "1")

def main():
    parquet_path = "seoul_pops/data/LOCAL_PEOPLE_DONG_202606_tidy.parquet"
    xlsx_path = "seoul_pops/data/행정동코드_매핑정보_20241218.xlsx"
    output_html_path = "seoul_pops/report/sweetviz_report.html"
    
    print("=== [1] 데이터 로드 ===")
    df = pd.read_parquet(parquet_path)
    df_map = pd.read_excel(xlsx_path, sheet_name='행정동코드').iloc[1:]
    
    print("=== [2] 중요 누락 파생변수 결합 (행정동명, 요일_kor, 주중_주말) ===")
    # 행정동명 결합
    df_map['행자부행정동코드'] = df_map['행자부행정동코드'].astype(str)
    code_to_name = dict(zip(df_map['행자부행정동코드'], df_map['행정동명']))
    df['행정동명'] = df['행정동코드'].astype(str).map(code_to_name)
    
    # 시간대구분 및 생활인구수 타입 보정
    df['시간대구분'] = df['시간대구분'].astype(int)
    df['생활인구수'] = df['생활인구수'].astype(float)
    
    # 요일 변수 생성
    date_series = pd.to_datetime(df['기준일ID'].astype(str), format='%Y%m%d')
    df['요일'] = date_series.dt.day_name()
    
    # 한국어 요일 변환
    weekday_map = {
        'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
        'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
    }
    df['요일_kor'] = df['요일'].map(weekday_map)
    df['요일_kor'] = pd.Categorical(df['요일_kor'], 
                                   categories=['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'], 
                                   ordered=True)
    
    # 주중_주말 변수 생성
    df['주중_주말'] = np.where(df['요일'].isin(['Saturday', 'Sunday']), '주말', '주중')
    df['주중_주말'] = df['주중_주말'].astype('category')
    
    # 불필요한 영문 요일 컬럼 삭제
    df = df.drop(columns=['요일'])
    
    # 100,000행 무작위 샘플링 (사용자 캡처와 동일 조건 수립)
    print(f"Original shape: {df.shape}")
    sample_size = 100000
    df_sample = df.sample(n=sample_size, random_state=42)
    print(f"Sampled shape: {df_sample.shape}")
    
    print("=== [3] Sweetviz 리포트 빌드 (한글 폰트 적용 완료) ===")
    report = sv.analyze(df_sample)
    
    print("=== [4] HTML 파일 저장 ===")
    report.show_html(output_html_path, open_browser=False)
    print(f"Sweetviz HTML 프로파일링 리포트 저장 완료: {output_html_path}")

if __name__ == "__main__":
    main()
