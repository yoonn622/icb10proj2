"""
이 스크립트는 burger.csv 데이터를 바탕으로 시도시군구명(정제_시도명 + 정제_시군구명)과
브랜드명 간의 빈도수 교차표(Crosstab)를 생성하고, 이를 별도의 CSV 파일로 저장합니다.

- 입력 파일: burger_index/data/burger.csv
- 출력 파일: burger_index/data/sigungu_brand_crosstab.csv
- 작성일: 2026-07-01
"""

import os
import pandas as pd

def generate_crosstab():
    # 파일 경로 정의 (워크스페이스 안에서는 상대경로 사용 규칙 준수)
    input_file = 'burger_index/data/burger.csv'
    output_dir = 'burger_index/data'
    output_file = os.path.join(output_dir, 'sigungu_brand_crosstab.csv')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} 파일이 존재하지 않습니다.")
        return

    # 데이터 로드
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 1. 시도명과 시군구명을 공백 기준으로 합침
    # 결측치 방지 처리
    df['정제_시도명'] = df['정제_시도명'].fillna('')
    df['정제_시군구명'] = df['정제_시군구명'].fillna('')
    
    df['시도시군구명'] = (df['정제_시도명'] + ' ' + df['정제_시군구명']).str.strip()
    
    # 2. 빈도수 교차표 생성
    # margines=True를 설정하여 행/열 합계를 추가
    crosstab_df = pd.crosstab(df['시도시군구명'], df['브랜드명'], margins=True, margins_name='합계')
    
    # 인덱스 이름 정리
    crosstab_df.index.name = '시도시군구명'
    
    # 3. CSV로 저장 (인덱스 포함)
    os.makedirs(output_dir, exist_ok=True)
    crosstab_df.to_csv(output_file, encoding='utf-8')
    print(f"성공적으로 교차표를 생성하여 저장했습니다: {output_file}")
    
    # 상위 10개 행 출력하여 확인
    print("\n[교차표 상위 10개 행 미리보기]")
    print(crosstab_df.head(10))

if __name__ == '__main__':
    generate_crosstab()
