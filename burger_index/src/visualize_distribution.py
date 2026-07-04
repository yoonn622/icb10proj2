"""
이 스크립트는 burger_index/data/burger_crosstab.csv 데이터를 기반으로
각 시도시군구별 버거 브랜드(KFC, 롯데리아, 맥도날드, 버거킹)의 매장 수 분포를
박스플롯(Box Plot)과 바이올린플롯(Violin Plot)을 사용해 1x2 레이아웃으로 시각화하고 이미지로 저장합니다.

- 입력 파일: burger_index/data/burger_crosstab.csv
- 출력 이미지: burger_index/images/brand_distribution_plots.png
- 작성일: 2026-07-01
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import koreanize_matplotlib  # 한글 깨짐 방지용

def visualize_distribution():
    # 파일 경로 설정 (워크스페이스 내 상대경로 규칙 준수)
    input_file = 'burger_index/data/burger_crosstab.csv'
    image_dir = 'burger_index/images'
    output_image = os.path.join(image_dir, 'brand_distribution_plots.png')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} 파일이 존재하지 않습니다.")
        return

    # 데이터 로드
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # '합계' 행 제거 및 '합계' 열 제거 (순수 브랜드별 시군구 데이터만 필터링)
    df_clean = df[df['시도시군구명'] != '합계'].copy()
    if '합계' in df_clean.columns:
        df_clean = df_clean.drop(columns=['합계'])
        
    brand_cols = ['KFC', '롯데리아', '맥도날드', '버거킹']
    
    # Tidy 데이터 포맷으로 변환 (Seaborn 시각화 분석용)
    df_melted = pd.melt(df_clean, id_vars=['시도시군구명'], value_vars=brand_cols, 
                        var_name='브랜드', value_name='매장수')
    
    # 매장 수 컬럼 데이터 타입 변환
    df_melted['매장수'] = df_melted['매장수'].astype(int)
    
    # 한글 폰트 설정
    if platform.system() == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False)
    
    # 1행 2열 서브플롯 구성
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 브랜드별 소프트 매핑 컬러 지정
    color_map = {
        '롯데리아': '#e74c3c',  # 소프트 레드
        '맥도날드': '#f1c40f',  # 소프트 옐로우
        '버거킹': '#e67e22',   # 소프트 오렌지
        'KFC': '#c0392b'       # 다크 레드
    }
    
    # 1. 박스플롯 (Box Plot)
    sns.boxplot(ax=axes[0], data=df_melted, x='브랜드', y='매장수', hue='브랜드', palette=color_map, legend=False)
    axes[0].set_title('시도시군구별 브랜드 매장 수 분포 (Box Plot)', fontsize=12, fontweight='bold', pad=12)
    axes[0].set_xlabel('브랜드', fontsize=10)
    axes[0].set_ylabel('시도시군구별 매장 수 (개)', fontsize=10)
    axes[0].spines['top'].set_visible(False)
    axes[0].spines['right'].set_visible(False)
    axes[0].yaxis.grid(True, linestyle='--', alpha=0.5, color='#bdc3c7')
    axes[0].set_axisbelow(True)
    
    # 2. 바이올린플롯 (Violin Plot)
    # inner='quartile' 설정으로 사분위선 노출
    sns.violinplot(ax=axes[1], data=df_melted, x='브랜드', y='매장수', hue='브랜드', palette=color_map, legend=False, inner='quart')
    axes[1].set_title('시도시군구별 브랜드 매장 수 분포 (Violin Plot)', fontsize=12, fontweight='bold', pad=12)
    axes[1].set_xlabel('브랜드', fontsize=10)
    axes[1].set_ylabel('시도시군구별 매장 수 (개)', fontsize=10)
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['right'].set_visible(False)
    axes[1].yaxis.grid(True, linestyle='--', alpha=0.5, color='#bdc3c7')
    axes[1].set_axisbelow(True)
    
    # 전체 제목 레이아웃 설정
    plt.suptitle('전국 시도시군구별 버거 브랜드 매장 수 분포 비교', fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout(pad=2.0)
    
    # 이미지 저장
    os.makedirs(image_dir, exist_ok=True)
    plt.savefig(output_image, dpi=150)
    plt.close()
    
    print(f"성공적으로 분포 시각화 이미지를 저장했습니다: {output_image}")
    
    # 기술통계 데이터 집계 출력
    print("\n[브랜드별 시도시군구 매장 수 기술통계]")
    summary_stats = df_clean[brand_cols].describe()
    print(summary_stats)

if __name__ == '__main__':
    visualize_distribution()
