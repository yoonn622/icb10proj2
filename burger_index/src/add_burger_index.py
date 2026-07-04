"""
이 스크립트는 burger_crosstab.csv 및 burger.csv 데이터를 로드하여 버거지수를 계산하고,
시도시군구별 위도와 경도의 중간값을 계산해 파생변수로 추가합니다.
최종 결과는 엑셀에서 쉽게 볼 수 있는 utf-8-sig 인코딩을 적용해 city_brand_crosstab.csv 파일로 저장합니다.

- 버거지수 계산식: (버거킹 + 맥도날드 + KFC) / 롯데리아 (소수점 4자리 반올림)
- 위도/경도: burger.csv의 위도, 경도 값의 시도시군구별 중간값 (소수점 6자리 반올림)
- 입력 파일: 
    - burger_index/data/burger_crosstab.csv (기본 매장 수 교차표)
    - burger_index/data/burger.csv (위도, 경도 및 시도시군구 정보 포함 원본 데이터)
- 출력 파일: burger_index/data/city_brand_crosstab.csv
- 작성일: 2026-07-04
"""

import os
import pandas as pd
import numpy as np

def calculate_burger_index_with_coords():
    crosstab_path = 'burger_index/data/burger_crosstab.csv'
    burger_path = 'burger_index/data/burger.csv'
    output_path = 'burger_index/data/city_brand_crosstab.csv'
    
    if not os.path.exists(crosstab_path):
        print(f"Error: {crosstab_path} 파일이 존재하지 않습니다.")
        return
    if not os.path.exists(burger_path):
        print(f"Error: {burger_path} 파일이 존재하지 않습니다.")
        return
        
    # 1. 교차표 데이터 로드
    df = pd.read_csv(crosstab_path, encoding='utf-8')
    
    # 버거지수 열이 이미 존재한다면 제거하여 연산이 꼬이지 않게 함
    if '버거지수' in df.columns:
        df = df.drop(columns=['버거지수'])
        
    # 버거지수 계산: (버거킹 + 맥도날드 + KFC) / 롯데리아
    numerator = df['버거킹'] + df['맥도날드'] + df['KFC']
    denominator = df['롯데리아']
    
    df['버거지수'] = numerator / denominator
    df['버거지수'] = df['버거지수'].replace([np.inf, -np.inf], np.nan)
    df['버거지수'] = df['버거지수'].round(4)
    
    # 2. burger.csv에서 시도시군구별 위도/경도 중간값 계산
    burger_df = pd.read_csv(burger_path, encoding='utf-8')
    
    # 시도시군구명 생성
    burger_df['정제_시도명'] = burger_df['정제_시도명'].fillna('')
    burger_df['정제_시군구명'] = burger_df['정제_시군구명'].fillna('')
    burger_df['시도시군구명'] = (burger_df['정제_시도명'] + ' ' + burger_df['정제_시군구명']).str.strip()
    
    # 위도, 경도 컬럼 수치형 변환
    burger_df['위도'] = pd.to_numeric(burger_df['위도'], errors='coerce')
    burger_df['경도'] = pd.to_numeric(burger_df['경도'], errors='coerce')
    
    # 그룹화하여 중간값 계산
    coords_df = burger_df.groupby('시도시군구명')[['위도', '경도']].median().reset_index()
    coords_df['위도'] = coords_df['위도'].round(6)
    coords_df['경도'] = coords_df['경도'].round(6)
    
    # 3. 데이터 병합 (교차표 기준 Left Merge)
    merged_df = pd.merge(df, coords_df, on='시도시군구명', how='left')
    
    # 4. 저장 및 확인
    merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"성공적으로 버거지수와 위도/경도 중간값을 계산하여 {output_path}에 저장했습니다.")
    
    # 상위 10개 행과 하위 5개 행(합계 포함)을 출력하여 확인
    print("\n[상위 10개 행 미리보기]")
    print(merged_df.head(10))
    print("\n[하위 5개 행 미리보기]")
    print(merged_df.tail(5))

if __name__ == '__main__':
    calculate_burger_index_with_coords()
