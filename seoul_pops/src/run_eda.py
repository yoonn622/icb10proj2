"""
서울시 행정동별 생활인구 데이터(LOCAL_PEOPLE_DONG_202606_tidy.parquet)를 
기반으로 심층적인 탐색적 데이터 분석(EDA)을 수행하는 스크립트입니다.
11가지 다각적 시각화 이미지를 생성하고, 이에 대응하는 마크다운 요약 테이블 
데이터를 텍스트 파일로 생성합니다.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
import os
import io

def main():
    # 0. 디렉터리 준비
    os.makedirs("seoul_pops/images", exist_ok=True)
    os.makedirs("seoul_pops/report", exist_ok=True)
    
    # 1. 데이터 로드
    parquet_path = "seoul_pops/data/LOCAL_PEOPLE_DONG_202606_tidy.parquet"
    xlsx_path = "seoul_pops/data/행정동코드_매핑정보_20241218.xlsx"
    
    print("=== [1] 데이터 로드 및 요일/주중 파생변수 생성 ===")
    df = pd.read_parquet(parquet_path)
    df_map = pd.read_excel(xlsx_path, sheet_name='행정동코드').iloc[1:]
    
    # 행정동 명칭 매핑용 딕셔너리
    df_map['행자부행정동코드'] = df_map['행자부행정동코드'].astype(str)
    code_to_name = dict(zip(df_map['행자부행정동코드'], df_map['행정동명']))
    df['행정동명'] = df['행정동코드'].astype(str).map(code_to_name)
    
    # 시간대구분 및 생활인구수 타입 보정
    df['시간대구분'] = df['시간대구분'].astype(int)
    df['생활인구수'] = df['생활인구수'].astype(float)
    
    # 기준일ID를 날짜형으로 파싱하여 요일 및 주중/주말 변수 생성
    # 기준일ID는 category 타입이므로 문자로 변경 후 datetime 변환
    date_series = pd.to_datetime(df['기준일ID'].astype(str), format='%Y%m%d')
    df['요일'] = date_series.dt.day_name() # English 요일
    
    # 한국어 요일 변환 및 순서 지정
    weekday_map = {
        'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
        'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
    }
    df['요일_kor'] = df['요일'].map(weekday_map)
    df['요일_kor'] = pd.Categorical(df['요일_kor'], 
                                   categories=['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'], 
                                   ordered=True)
    
    # 주중/주말 구분
    df['주중_주말'] = np.where(df['요일'].isin(['Saturday', 'Sunday']), '주말', '주중')
    df['주중_주말'] = df['주중_주말'].astype('category')
    
    # 연령대 카테고리 순서 정의
    age_order = [
        '0세부터9세', '10세부터14세', '15세부터19세', '20세부터24세', '25세부터29세', 
        '30세부터34세', '35세부터39세', '40세부터44세', '45세부터49세', '50세부터54세', 
        '55세부터59세', '60세부터64세', '65세부터69세', '70세이상'
    ]
    df['연령대'] = pd.Categorical(df['연령대'], categories=age_order, ordered=True)
    
    print(f"Data Rows: {df.shape[0]:,}, Cols: {df.shape[1]}")
    
    # 보고서 테이블 텍스트를 임시 버퍼에 기록
    table_buffer = io.StringIO()
    table_buffer.write("# EDA 결과 요약 통계 테이블 모음\n\n")
    
    # ----------------------------------------------------
    # 시각화 1: 단변량 (수치형) - 생활인구수 분포
    # ----------------------------------------------------
    print("Plotting 1: Value Distribution...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    # 원본 분포
    axes[0].hist(df['생활인구수'].dropna(), bins=50, color='skyblue', edgecolor='black', alpha=0.7)
    axes[0].set_title("생활인구수 원본 분포 히스토그램", fontsize=12)
    axes[0].set_xlabel("생활인구수 (명)")
    axes[0].set_ylabel("빈도 (Frequency)")
    axes[0].grid(True, linestyle=':', alpha=0.6)
    
    # 로그 스케일 분포
    log_val = np.log1p(df['생활인구수'].dropna())
    axes[1].hist(log_val, bins=50, color='salmon', edgecolor='black', alpha=0.7)
    axes[1].set_title("생활인구수 로그 스케일 [log(x+1)] 분포 히스토그램", fontsize=12)
    axes[1].set_xlabel("log(생활인구수 + 1)")
    axes[1].set_ylabel("빈도 (Frequency)")
    axes[1].grid(True, linestyle=':', alpha=0.6)
    
    plt.suptitle("생활인구수 수치 분포 탐색", fontsize=14, y=0.98)
    fig_path = "seoul_pops/images/eda_01_val_dist.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 1 요약 통계
    desc_val = df['생활인구수'].describe().to_frame().T
    table_buffer.write("### [테이블 1] 생활인구수 수치 통계량 요약\n")
    table_buffer.write(desc_val.to_markdown() + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 2: 단변량 (범주형) - 연령대별 레코드 빈도
    # ----------------------------------------------------
    print("Plotting 2: Age group record frequencies...")
    age_counts = df['연령대'].value_counts().reindex(age_order)
    
    plt.figure(figsize=(12, 5))
    plt.bar(age_counts.index, age_counts.values, color='lightgreen', edgecolor='black', alpha=0.8, width=0.6)
    plt.title("데이터셋 내 연령대별 관측치 레코드 빈도 분포", fontsize=13, pad=15)
    plt.xlabel("연령대", fontsize=11)
    plt.ylabel("관측 레코드 수 (건)", fontsize=11)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    fig_path = "seoul_pops/images/eda_02_age_freq.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 2 요약 통계
    df_age_counts = age_counts.to_frame(name='레코드수').reset_index()
    df_age_counts['비율(%)'] = (df_age_counts['레코드수'] / df_age_counts['레코드수'].sum() * 100).round(2)
    table_buffer.write("### [테이블 2] 연령대별 레코드 빈도 및 비율\n")
    table_buffer.write(df_age_counts.to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 3: 이변량 - 시간대별 평균 생활인구수
    # ----------------------------------------------------
    print("Plotting 3: Hourly trend...")
    time_avg = df.groupby('시간대구분')['생활인구수'].mean().reset_index()
    
    plt.figure(figsize=(10, 5))
    plt.plot(time_avg['시간대구분'], time_avg['생활인구수'], marker='o', color='purple', linewidth=2)
    plt.title("서울시 전체 평균 시간대별 생활인구수 추이", fontsize=13, pad=15)
    plt.xlabel("시간대 (시)", fontsize=11)
    plt.ylabel("평균 생활인구수 (명)", fontsize=11)
    plt.xticks(range(0, 24))
    plt.grid(True, linestyle=':', alpha=0.6)
    
    fig_path = "seoul_pops/images/eda_03_time_trend.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 3 요약 통계
    table_buffer.write("### [테이블 3] 시간대별 평균 생활인구수\n")
    table_buffer.write(time_avg.to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 4: 이변량 - 연령대별 평균 생활인구수
    # ----------------------------------------------------
    print("Plotting 4: Average population by age...")
    age_avg = df.groupby('연령대', observed=False)['생활인구수'].mean().reset_index()
    
    plt.figure(figsize=(12, 5))
    plt.bar(age_avg['연령대'], age_avg['생활인구수'], color='orange', edgecolor='black', alpha=0.7, width=0.6)
    plt.title("연령대별 평균 생활인구수 비교", fontsize=13, pad=15)
    plt.xlabel("연령대", fontsize=11)
    plt.ylabel("평균 생활인구수 (명)", fontsize=11)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    fig_path = "seoul_pops/images/eda_04_age_trend.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 4 요약 통계
    table_buffer.write("### [테이블 4] 연령대별 평균 생활인구수\n")
    table_buffer.write(age_avg.to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 5: 이변량 - 성별 평균 생활인구수 비교
    # ----------------------------------------------------
    print("Plotting 5: Average population by gender...")
    gender_avg = df.groupby('성별', observed=False)['생활인구수'].mean().reset_index()
    
    plt.figure(figsize=(6, 5))
    plt.bar(gender_avg['성별'], gender_avg['생활인구수'], color=['pink', 'lightblue'], edgecolor='black', width=0.5, alpha=0.8)
    plt.title("성별 평균 생활인구수 비교", fontsize=13, pad=15)
    plt.xlabel("성별", fontsize=11)
    plt.ylabel("평균 생활인구수 (명)", fontsize=11)
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    
    fig_path = "seoul_pops/images/eda_05_gender_trend.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 5 요약 통계
    table_buffer.write("### [테이블 5] 성별 평균 생활인구수\n")
    table_buffer.write(gender_avg.to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 6: 이변량 (시계열) - 요일별 평균 생활인구수
    # ----------------------------------------------------
    print("Plotting 6: Weekday trend...")
    day_avg = df.groupby('요일_kor', observed=False)['생활인구수'].mean().reset_index()
    
    plt.figure(figsize=(10, 5))
    plt.plot(day_avg['요일_kor'], day_avg['생활인구수'], marker='s', color='teal', linewidth=2, markersize=8)
    plt.title("요일별 평균 생활인구수 변동 추이", fontsize=13, pad=15)
    plt.xlabel("요일", fontsize=11)
    plt.ylabel("평균 생활인구수 (명)", fontsize=11)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    fig_path = "seoul_pops/images/eda_06_weekday_trend.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 6 요약 통계
    table_buffer.write("### [테이블 6] 요일별 평균 생활인구수\n")
    table_buffer.write(day_avg.to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 7: 다변량 - 성별 및 연령대별 생활인구 히트맵
    # ----------------------------------------------------
    print("Plotting 7: Gender-Age Heatmap...")
    pivot_heatmap = df.pivot_table(
        index='연령대',
        columns='성별',
        values='생활인구수',
        aggfunc='mean',
        observed=False
    ).reindex(age_order)
    
    plt.figure(figsize=(8, 8))
    # matplotlib 스타일을 고려해 히트맵 그리기
    # sns 스타일 설정 없이 직접 피규어 생성
    im = plt.imshow(pivot_heatmap.values, cmap='YlGnBu', aspect='auto')
    plt.colorbar(im, label="평균 생활인구수 (명)")
    plt.title("성별 및 연령대별 평균 생활인구 히트맵", fontsize=13, pad=15)
    
    # 라벨 및 틱 설정
    plt.yticks(range(len(age_order)), age_order)
    plt.xticks(range(2), pivot_heatmap.columns)
    plt.xlabel("성별", fontsize=11)
    plt.ylabel("연령대", fontsize=11)
    
    # 텍스트 주석 추가
    for i in range(len(age_order)):
        for j in range(2):
            val = pivot_heatmap.values[i, j]
            plt.text(j, i, f"{val:.1f}", ha="center", va="center", 
                     color="black" if val < pivot_heatmap.values.max()*0.7 else "white", fontsize=9)
            
    fig_path = "seoul_pops/images/eda_07_gender_age_heatmap.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 7 요약 통계
    table_buffer.write("### [테이블 7] 성별/연령대별 평균 생활인구 피벗 교차표\n")
    table_buffer.write(pivot_heatmap.reset_index().to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 8: 다변량 - 주중 vs 주말 시간대별 생활인구 변화
    # ----------------------------------------------------
    print("Plotting 8: Weekday vs Weekend Hourly trend...")
    weekday_weekend_avg = df.groupby(['주중_주말', '시간대구분'], observed=False)['생활인구수'].mean().reset_index()
    
    plt.figure(figsize=(10, 5))
    for label, grp in weekday_weekend_avg.groupby('주중_주말', observed=False):
        plt.plot(grp['시간대구분'], grp['생활인구수'], marker='o', label=label, linewidth=2)
    plt.title("주중 vs 주말 시간대별 평균 생활인구 비교", fontsize=13, pad=15)
    plt.xlabel("시간대 (시)", fontsize=11)
    plt.ylabel("평균 생활인구수 (명)", fontsize=11)
    plt.xticks(range(0, 24))
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(title="주중/주말 구분")
    
    fig_path = "seoul_pops/images/eda_08_weekday_weekend_trend.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 8 요약 통계
    pivot_ww = weekday_weekend_avg.pivot(index='시간대구분', columns='주중_주말', values='생활인구수')
    table_buffer.write("### [테이블 8] 시간대별 주중 및 주말 평균 생활인구\n")
    table_buffer.write(pivot_ww.reset_index().to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 9: 다변량 - 시간대별 성별 생활인구 추이
    # ----------------------------------------------------
    print("Plotting 9: Hourly Gender trend...")
    time_gender_avg = df.groupby(['성별', '시간대구분'], observed=False)['생활인구수'].mean().reset_index()
    
    plt.figure(figsize=(10, 5))
    for label, grp in time_gender_avg.groupby('성별', observed=False):
        plt.plot(grp['시간대구분'], grp['생활인구수'], marker='x', label=label, linewidth=2)
    plt.title("시간대별 성별 평균 생활인구 변동 추이", fontsize=13, pad=15)
    plt.xlabel("시간대 (시)", fontsize=11)
    plt.ylabel("평균 생활인구수 (명)", fontsize=11)
    plt.xticks(range(0, 24))
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(title="성별")
    
    fig_path = "seoul_pops/images/eda_09_time_gender_trend.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 9 요약 통계
    pivot_tg = time_gender_avg.pivot(index='시간대구분', columns='성별', values='생활인구수')
    table_buffer.write("### [테이블 9] 시간대별 성별 평균 생활인구\n")
    table_buffer.write(pivot_tg.reset_index().to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 10: 공간 분석 - 평균 생활인구수 상위 30개 행정동
    # ----------------------------------------------------
    print("Plotting 10: Top 30 Dong by average population...")
    dong_avg = df.groupby('행정동명', observed=False)['생활인구수'].mean().reset_index()
    top_30_dong = dong_avg.sort_values(by='생활인구수', ascending=False).head(30)
    
    plt.figure(figsize=(10, 10))
    plt.barh(top_30_dong['행정동명'][::-1], top_30_dong['생활인구수'][::-1], color='darkcyan', edgecolor='black', alpha=0.8)
    plt.title("평균 생활인구수 상위 30개 행정동", fontsize=13, pad=15)
    plt.xlabel("평균 생활인구수 (명)", fontsize=11)
    plt.ylabel("행정동명", fontsize=11)
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    
    fig_path = "seoul_pops/images/eda_10_dong_top30.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    # 시각화 10 요약 통계
    table_buffer.write("### [테이블 10] 평균 생활인구 상위 30개 행정동 목록\n")
    table_buffer.write(top_30_dong.to_markdown(index=False) + "\n\n")
    
    # ----------------------------------------------------
    # 시각화 11: 복합 분석 - 연령대별 생활인구수 분포 박스플롯
    # ----------------------------------------------------
    print("Plotting 11: Outlier check with Box Plot...")
    # 박스플롯은 데이터 포인트 수가 너무 많아 기본 생성 시 매우 조밀해질 수 있으므로 샘플링하여 렌더링
    df_sample = df.sample(n=100000, random_state=42)
    
    plt.figure(figsize=(12, 6))
    box_data = [df_sample[df_sample['연령대'] == age]['생활인구수'].dropna().values for age in age_order]
    
    # Outliers를 투명하게 점 형태로 시각화
    plt.boxplot(box_data, tick_labels=age_order, patch_artist=True,
                boxprops=dict(facecolor='lightblue', color='blue', alpha=0.7),
                flierprops=dict(marker='o', markerfacecolor='red', markersize=3, alpha=0.1, markeredgecolor='none'))
    plt.title("연령대별 생활인구수 분포 및 아웃라이어 파악 (Box Plot)", fontsize=13, pad=15)
    plt.xlabel("연령대", fontsize=11)
    plt.ylabel("생활인구수 (명)", fontsize=11)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    
    fig_path = "seoul_pops/images/eda_11_age_boxplot.png"
    plt.savefig(fig_path, bbox_inches='tight', dpi=150)
    plt.close()
    # 시각화 11 요약 통계
    # pandas agg에서 q1, q3 바로 적용
    box_summary = df.groupby('연령대', observed=False)['생활인구수'].agg([
        ('Min', 'min'),
        ('Q1', lambda x: np.percentile(x.dropna(), 25)),
        ('Median', 'median'),
        ('Q3', lambda x: np.percentile(x.dropna(), 75)),
        ('Max', 'max')
    ]).reset_index()

    
    table_buffer.write("### [테이블 11] 연령대별 생활인구 분위수 요약\n")
    table_buffer.write(box_summary.to_markdown(index=False) + "\n\n")
    
    # 요약 통계 파일 저장
    tables_txt_path = "seoul_pops/report/eda_tables.txt"
    with open(tables_txt_path, "w", encoding="utf-8") as f:
        f.write(table_buffer.getvalue())
        
    print(f"=== 모든 EDA 분석 및 시각화 완료! 요약 테이블 저장: {tables_txt_path} ===")

if __name__ == "__main__":
    main()
