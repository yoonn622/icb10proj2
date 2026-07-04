"""
이 스크립트는 city_brand_crosstab.csv 데이터를 기반으로 위경도 좌표를 활용하여
지역별 버거지수 분포를 나타내는 산점도(Scatter Plot)를 시각화하고 이미지 파일로 저장합니다.

- 입력 파일: burger_index/data/city_brand_crosstab.csv
- 출력 이미지: burger_index/images/burger_index_scatter.png
- 작성일: 2026-07-04
"""

import os
import platform
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_burger_index_scatter():
    # 1. 한글 깨짐 방지를 위한 폰트 세팅 (요구사항 1)
    if platform.system() == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False)

    # 경로 정의
    csv_path = 'burger_index/data/city_brand_crosstab.csv'
    image_dir = 'burger_index/images'
    output_image = os.path.join(image_dir, 'burger_index_scatter.png')

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} 파일이 존재하지 않습니다.")
        return

    # 데이터 로드 (BOM 대응을 위해 utf-8-sig 인코딩 사용)
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 컬럼명을 요구사항에 맞춰 리네임 ('위도' -> '위도_중앙값', '경도' -> '경도_중앙값')
    df = df.rename(columns={'위도': '위도_중앙값', '경도': '경도_중앙값'})

    # 결측치 제거 (위도, 경도, 버거지수 중 하나라도 NaN인 데이터와 '합계' 행 제거)
    plot_df = df.dropna(subset=['위도_중앙값', '경도_중앙값', '버거지수'])
    plot_df = plot_df[plot_df['시도시군구명'] != '합계']

    # 2. 산점도 그리기 (요구사항 2, 4)
    # 우리나라 지도 비율(상하가 더 긴 형태)에 맞춰 figsize 설정
    plt.figure(figsize=(12, 16))
    
    # sns.scatterplot 사용
    sns.scatterplot(
        data=plot_df,
        x='경도_중앙값',
        y='위도_중앙값',
        size='버거지수',
        sizes=(40, 400),
        hue='버거지수',
        palette='YlOrRd',
        alpha=0.6,
        edgecolor='gray',
        linewidth=0.5
    )

    # 3. 데이터 포인트 옆에 텍스트 이름표 라벨링 추가 (요구사항 3)
    for _, row in plot_df.iterrows():
        # 좌표 겹침을 최소화하기 위해 텍스트 오프셋 적용
        plt.text(
            row['경도_중앙값'] + 0.008, 
            row['위도_중앙값'] + 0.003, 
            row['시도시군구명'], 
            fontsize=7.5, 
            alpha=0.7, 
            color='#333333',
            va='center'
        )

    # 4. 차트 레이아웃 및 스타일 가공
    plt.title('지역별 위경도 좌표 기준 버거지수 분포도', fontsize=18, fontweight='bold', pad=25)
    plt.xlabel('경도_중앙값', fontsize=12, labelpad=10)
    plt.ylabel('위도_중앙값', fontsize=12, labelpad=10)
    
    # 축 테두리를 없애고 가로/세로 그리드선만 투명하게 표시해 깔끔한 레이아웃 구성
    sns.despine(left=True, bottom=True)
    plt.grid(True, linestyle='--', alpha=0.3, color='#bdc3c7')
    
    # 범례 위치 조정 및 투명도 설정
    plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1.0), frameon=True, shadow=False)
    
    plt.tight_layout()

    # 이미지 파일로 저장
    os.makedirs(image_dir, exist_ok=True)
    plt.savefig(output_image, dpi=200, bbox_inches='tight')
    plt.close()

    print(f"성공적으로 버거지수 산점도 시각화 이미지를 저장했습니다: {output_image}")

if __name__ == '__main__':
    visualize_burger_index_scatter()
