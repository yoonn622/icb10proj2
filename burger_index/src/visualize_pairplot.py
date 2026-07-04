"""
이 스크립트는 burger_index/data/burger_crosstab.csv 데이터를 로드하여
시도시군구명에 따른 버거 브랜드(KFC, 롯데리아, 맥도날드, 버거킹) 매장 수의 관계를 보여주는
페어플롯(Pairplot)을 시각화하고 이미지 파일로 저장합니다.

- 입력 파일: burger_index/data/burger_crosstab.csv (없을 경우 기존 데이터를 복사하여 생성)
- 출력 이미지: burger_index/images/pairplot_sigungu_brand.png
- 작성일: 2026-07-01
"""

import os
import shutil
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
import koreanize_matplotlib  # 한글 깨짐 방지용

def visualize_pairplot():
    # 파일 경로 정의
    original_crosstab = 'burger_index/data/sigungu_brand_crosstab.csv'
    target_crosstab = 'burger_index/data/burger_crosstab.csv'
    image_dir = 'burger_index/images'
    output_image = os.path.join(image_dir, 'pairplot_sigungu_brand.png')
    
    # burger_crosstab.csv 파일이 없으면 기존 복사본 사용
    if not os.path.exists(target_crosstab):
        if os.path.exists(original_crosstab):
            shutil.copy(original_crosstab, target_crosstab)
            print(f"'{original_crosstab}' 파일을 '{target_crosstab}'로 복사했습니다.")
        else:
            print(f"Error: {original_crosstab} 파일이 존재하지 않아 교차표 데이터를 불러올 수 없습니다.")
            return

    # 데이터 로드
    df = pd.read_csv(target_crosstab, encoding='utf-8')
    
    # '합계' 행 및 '합계' 열 제거 (페어플롯 시각화에 왜곡을 주지 않기 위해)
    df_clean = df[df['시도시군구명'] != '합계'].copy()
    if '합계' in df_clean.columns:
        df_clean = df_clean.drop(columns=['합계'])
        
    brand_cols = ['KFC', '롯데리아', '맥도날드', '버거킹']
    
    # 필수 컬럼 검증
    for col in brand_cols:
        if col not in df_clean.columns:
            print(f"Error: 필수 컬럼인 '{col}'이 데이터에 없습니다.")
            return
            
    # 데이터 타입 변환
    df_clean[brand_cols] = df_clean[brand_cols].astype(int)

    # Matplotlib 한글 폰트 설정 및 기본 스타일 유지
    import platform
    if platform.system() == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False)
    
    # PairGrid 정의 (sns.set_theme() 없이 사용)
    g = sns.PairGrid(df_clean[brand_cols])
    
    # 대각선 영역: KDE 분포 곡선 시각화
    g.map_diag(sns.kdeplot, fill=True)
    
    # 상관계수 계산 및 회귀선 표기 함수 정의
    def reg_with_corr(x, y, **kwargs):
        ax = plt.gca()
        # 회귀선과 산점도 시각화
        sns.regplot(x=x, y=y, ax=ax, scatter_kws={'alpha': 0.6, 's': 20}, line_kws={'color': 'red'}, **kwargs)
        # 피어슨 상관계수 산출
        r, _ = pearsonr(x, y)
        # 서브플롯 우측 상단에 텍스트 표기
        ax.text(0.95, 0.95, f'r = {r:.2f}', transform=ax.transAxes,
                horizontalalignment='right', verticalalignment='top',
                weight='bold', color='darkred', fontsize=10)
                
    # 상삼각 영역: 회귀선(regplot) 및 상관계수 적용
    g.map_upper(reg_with_corr)
    
    # 하삼각 영역: 마스크 처리 (보이지 않게 숨김)
    for i in range(len(brand_cols)):
        for j in range(len(brand_cols)):
            if i > j:
                g.axes[i, j].set_visible(False)
                
    # 전체 제목 설정
    g.fig.suptitle('전국 시도시군구별 버거 브랜드 매장 수 간의 상관관계 (상삼각 Pairplot)', y=1.02, fontsize=14, fontweight='bold')
    
    # 저장 디렉토리 보장 및 저장
    os.makedirs(image_dir, exist_ok=True)
    plt.savefig(output_image, bbox_inches='tight', dpi=150)
    plt.close()
    
    print(f"성공적으로 페어플롯 이미지를 저장했습니다: {output_image}")

if __name__ == '__main__':
    visualize_pairplot()
