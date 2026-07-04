"""
이 스크립트는 burger_index/data/burger.csv 데이터를 로드하여
4대 버거 브랜드(롯데리아, 맥도날드, 버거킹, KFC)의 전국 총 매장 수를 집계하고,
이를 세련된 막대그래프(Bar Chart)로 시각화하여 이미지 파일로 저장합니다.

- 입력 파일: burger_index/data/burger.csv
- 출력 이미지: burger_index/images/brand_count_barplot.png
- 작성일: 2026-07-01
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import platform
import koreanize_matplotlib  # 한글 깨짐 방지용

def visualize_brand_count():
    # 파일 경로 설정 (워크스페이스 내 상대경로 규칙 준수)
    input_file = 'burger_index/data/burger.csv'
    image_dir = 'burger_index/images'
    output_image = os.path.join(image_dir, 'brand_count_barplot.png')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} 파일이 존재하지 않습니다.")
        return

    # 데이터 로드
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 각 브랜드별 총 매장 수 집계 (불리언 컬럼의 합계 사용)
    brand_counts = {
        '롯데리아': df['롯데리아_여부'].sum(),
        '맥도날드': df['맥도날드_여부'].sum(),
        '버거킹': df['버거킹_여부'].sum(),
        'KFC': df['KFC_여부'].sum()
    }
    
    # 데이터프레임 생성 및 매장 수 기준 내림차순 정렬
    counts_df = pd.DataFrame(list(brand_counts.items()), columns=['브랜드', '매장수'])
    counts_df = counts_df.sort_values(by='매장수', ascending=False).reset_index(drop=True)

    # 한글 폰트 설정
    if platform.system() == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False)
    
    # 그래프 캔버스 크기 설정
    plt.figure(figsize=(7, 5))
    
    # 브랜드별 소프트 아이덴티티 컬러 매핑 (세련된 소프트 톤 컬러 적용)
    color_map = {
        '롯데리아': '#e74c3c',  # 소프트 레드
        '맥도날드': '#f1c40f',  # 소프트 옐로우
        '버거킹': '#e67e22',   # 소프트 오렌지/브라운
        'KFC': '#c0392b'       # 다크 레드
    }
    plot_colors = [color_map[b] for b in counts_df['브랜드']]
    
    # 막대그래프 드로잉
    bars = plt.bar(counts_df['브랜드'], counts_df['매장수'], color=plot_colors, edgecolor='none', width=0.55)
    
    # 막대 상단에 구체적인 매장 수 수치 텍스트 어노테이션 추가
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height + 15, f'{int(height):,}개', 
                 ha='center', va='bottom', fontsize=11, fontweight='bold', color='#2c3e50')
                 
    # 그래프 타이틀 및 축 레이블 설정
    plt.title('전국 4대 버거 브랜드 총 매장 수 비교', fontsize=14, fontweight='bold', pad=20)
    plt.ylabel('매장 수 (개)', fontsize=10, labelpad=10)
    
    # y축 표시 한계 설정 (상단 텍스트 겹침 방지 여유 공간 확보)
    plt.ylim(0, counts_df['매장수'].max() + 150) 
    
    # 그래프 테두리선(Spines) 정리 - 세련된 Flat 디자인 추구
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # 가로 보조 격자선 추가 (막대 뒤쪽 레이어에 배치)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#bdc3c7')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # 이미지 파일 저장
    os.makedirs(image_dir, exist_ok=True)
    plt.savefig(output_image, dpi=150)
    plt.close()
    
    print(f"성공적으로 브랜드별 빈도수 막대그래프를 저장했습니다: {output_image}")
    print("\n[브랜드별 매장 수 집계]")
    print(counts_df)

if __name__ == '__main__':
    visualize_brand_count()
