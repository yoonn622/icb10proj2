"""
이 스크립트는 burger_index/data/burger_crosstab.csv 데이터를 기반으로
버거 브랜드(KFC, 롯데리아, 맥도날드, 버거킹) 간 매장 수의 상관계수를 산출하고,
이를 마스크 처리 없이 전체 상관계수 히트맵(Heatmap)으로 시각화하여 이미지 파일로 저장합니다.

- 입력 파일: burger_index/data/burger_crosstab.csv
- 출력 이미지: burger_index/images/correlation_heatmap.png
- 작성일: 2026-07-01
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import koreanize_matplotlib  # 한글 깨짐 방지용

def visualize_heatmap():
    # 파일 경로 설정 (워크스페이스 내 상대경로 규칙 준수)
    input_file = 'burger_index/data/burger_crosstab.csv'
    image_dir = 'burger_index/images'
    output_image = os.path.join(image_dir, 'correlation_heatmap.png')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} 파일이 존재하지 않습니다.")
        return

    # 데이터 로드
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # '합계' 행 제거 (상관관계 분석 왜곡 방지)
    df_clean = df[df['시도시군구명'] != '합계'].copy()
    
    # 분석 대상 브랜드 컬럼
    brand_cols = ['KFC', '롯데리아', '맥도날드', '버거킹']
    
    # 데이터 타입 변환
    df_clean[brand_cols] = df_clean[brand_cols].astype(int)
    
    # 피어슨 상관계수 행렬 산출
    corr_matrix = df_clean[brand_cols].corr(method='pearson')
    
    # 한글 폰트 설정
    if platform.system() == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False)
    
    # 히트맵 시각화 크기 설정
    plt.figure(figsize=(6, 5))
    
    # 히트맵 그리기 (참고 이미지의 coolwarm 컬러맵 및 -1.0 ~ 1.0 범위 지정)
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                vmin=-1.0, vmax=1.0, linewidths=0.5)
    
    # 제목 및 축 이름 레이아웃 수정
    plt.title('4대 버거 브랜드 매장 수 상관계수 히트맵', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('')
    plt.ylabel('')
    plt.tight_layout()
    
    # 이미지 저장
    os.makedirs(image_dir, exist_ok=True)
    plt.savefig(output_image, dpi=150)
    plt.close()
    
    print(f"성공적으로 히트맵 이미지를 저장했습니다: {output_image}")
    print("\n[상관계수 행렬]")
    print(corr_matrix)

if __name__ == '__main__':
    visualize_heatmap()
