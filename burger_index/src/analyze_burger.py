"""
이 스크립트는 burger.csv 데이터를 로드하여 다음과 같은 전처리를 수행합니다:
1. 상권업종대분류명 '과학·기술', '교육' 카테고리 데이터 제외
2. 상호명과 도로명주소가 완벽히 일치하는 중복 데이터 제거 (첫 번째 행만 유지)
3. 시도코드/시군구코드 대표 명칭 정제 및 브랜드 식별 컬럼 추가
4. 정제된 데이터를 burger.csv에 다시 저장하고, 그에 기초한 전체 통계 리포트(burger_report.md)를 생성합니다.
"""

import os
import pandas as pd

def process_and_analyze_burger_data():
    csv_path = 'burger_index/data/burger.csv'
    report_path = 'burger_index/report/burger_report.md'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} 파일이 존재하지 않습니다.")
        return
        
    # 1. 데이터 로드
    df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
    initial_len = len(df)
    
    # 2. 무관한 상권업종대분류명('과학·기술', '교육') 데이터 제외 필터링
    exclude_categories = ['과학·기술', '교육']
    df_filtered = df[~df['상권업종대분류명'].isin(exclude_categories)].copy()
    filtered_len = len(df_filtered)
    removed_categories_cnt = initial_len - filtered_len
    
    # 3. 중복 데이터 분석 (상호명 + 도로명주소 기준)
    # 중복 분석을 위해 중복되는 데이터셋 확보
    duplicated_mask = df_filtered.duplicated(subset=['상호명', '도로명주소'], keep=False)
    dup_df = df_filtered[duplicated_mask]
    total_duplicated_rows = len(dup_df)
    unique_duplicate_sets = len(df_filtered[df_filtered.duplicated(subset=['상호명', '도로명주소'], keep='first')])
    
    # 중복 제거 (첫 번째 값만 남김)
    df_dedup = df_filtered.drop_duplicates(subset=['상호명', '도로명주소'], keep='first').copy()
    dedup_len = len(df_dedup)
    removed_duplicates_cnt = filtered_len - dedup_len
    
    print(f"필터링 전 데이터: {initial_len}개")
    print(f" -> 카테고리 필터링 후: {filtered_len}개 (제외: {removed_categories_cnt}개)")
    print(f" -> 중복 제거 후: {dedup_len}개 (제외: {removed_duplicates_cnt}개)")
    
    # 4. 각 브랜드별 매핑 여부 컬럼 추가/갱신 (대소문자 무관)
    df_dedup['버거킹_여부'] = df_dedup['상호명'].str.contains(r'버거킹|burger\s?king', case=False, na=False)
    df_dedup['맥도날드_여부'] = df_dedup['상호명'].str.contains(r'맥도날드|mcdonald', case=False, na=False)
    df_dedup['KFC_여부'] = df_dedup['상호명'].str.contains(r'kfc|케이에프씨', case=False, na=False)
    df_dedup['롯데리아_여부'] = df_dedup['상호명'].str.contains(r'롯데리아|lotteria', case=False, na=False)
    
    def determine_brand(row):
        brands = []
        if row['버거킹_여부']:
            brands.append('버거킹')
        if row['맥도날드_여부']:
            brands.append('맥도날드')
        if row['KFC_여부']:
            brands.append('KFC')
        if row['롯데리아_여부']:
            brands.append('롯데리아')
        return ','.join(brands) if brands else '기타'
        
    df_dedup['브랜드명'] = df_dedup.apply(determine_brand, axis=1)
    
    # 5. 코드와 명칭 간 불일치 오류를 막기 위해 각 코드별 대표 명칭 매핑 테이블 생성
    sido_map = df_dedup.groupby('시도코드')['시도명'].agg(lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0]).to_dict()
    sigungu_map = df_dedup.groupby('시군구코드')['시군구명'].agg(lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0]).to_dict()
    
    df_dedup['정제_시도명'] = df_dedup['시도코드'].map(sido_map)
    df_dedup['정제_시군구명'] = df_dedup['시군구코드'].map(sigungu_map)
    
    # 6. 전처리 및 중복 제거가 완료된 최종 데이터를 burger.csv 파일에 다시 저장 (UTF-8 인코딩)
    df_dedup.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"최종 중복 제거된 CSV가 갱신되어 저장되었습니다: {csv_path}")
    
    # 7. 통계 분석 집계
    # 브랜드별 요약
    total_bk = df_dedup['버거킹_여부'].sum()
    total_mc = df_dedup['맥도날드_여부'].sum()
    total_kfc = df_dedup['KFC_여부'].sum()
    total_lot = df_dedup['롯데리아_여부'].sum()
    total_sum = len(df_dedup)
    
    # 시도별 요약 (단순 건수 표)
    sido_grouped = df_dedup.groupby(['시도코드', '정제_시도명']).agg(
        버거킹=('버거킹_여부', 'sum'),
        맥도날드=('맥도날드_여부', 'sum'),
        KFC=('KFC_여부', 'sum'),
        롯데리아=('롯데리아_여부', 'sum'),
        합계=('상가업소번호', 'count')
    ).reset_index().sort_values(by='시도코드')
    
    # 지역별(시도명) 브랜드 교차표 집계
    sido_crosstab = df_dedup.groupby('정제_시도명').agg(
        KFC=('KFC_여부', 'sum'),
        롯데리아=('롯데리아_여부', 'sum'),
        맥도날드=('맥도날드_여부', 'sum'),
        버거킹=('버거킹_여부', 'sum')
    )
    sido_crosstab = sido_crosstab.sort_index()  # 가나다 순 정렬
    sido_crosstab['총계'] = sido_crosstab.sum(axis=1)
    
    sido_total_row = sido_crosstab.sum(axis=0)
    sido_total_row.name = '총계'
    sido_crosstab = pd.concat([sido_crosstab, pd.DataFrame([sido_total_row])])
    
    # 시군구별 요약
    sigungu_grouped = df_dedup.groupby(['시도코드', '정제_시도명', '시군구코드', '정제_시군구명']).agg(
        버거킹=('버거킹_여부', 'sum'),
        맥도날드=('맥도날드_여부', 'sum'),
        KFC=('KFC_여부', 'sum'),
        롯데리아=('롯데리아_여부', 'sum'),
        합계=('상가업소번호', 'count')
    ).reset_index().sort_values(by=['시도코드', '시군구코드']).reset_index(drop=True)
    
    # 상권업종대분류명 x 브랜드 교차표 집계
    df_dedup['상권업종대분류명'] = df_dedup['상권업종대분류명'].fillna('미분류')
    ct_data = {}
    for brand in ['버거킹', '맥도날드', 'KFC', '롯데리아']:
        flag_col = f"{brand}_여부"
        ct_data[brand] = df_dedup[df_dedup[flag_col] == True].groupby('상권업종대분류명').size()
        
    crosstab_df = pd.DataFrame(ct_data).fillna(0).astype(int)
    crosstab_df['합계'] = crosstab_df.sum(axis=1)
    
    total_row = crosstab_df.sum(axis=0)
    total_row.name = '합계'
    crosstab_df = pd.concat([crosstab_df, pd.DataFrame([total_row])])
    crosstab_df.index.name = '상권업종대분류명'
    
    # 8. 마크다운 보고서 생성
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 버거 브랜드 전국 매장 분포 및 업종 분류 리포트\n\n")
        f.write("소상공인시장진흥공단 상가(상권)정보 데이터를 기반으로 전처리 및 정제한 버거 브랜드(버거킹, 맥도날드, KFC, 롯데리아)의 전국 매장 정보입니다.\n")
        f.write("> **전처리 요약**: 무관 업종 제외 및 상호명/도로명주소 기준 중복 데이터 제거가 적용된 최종 보고서입니다.\n\n")
        
        # 0. 중복 및 필터링 내역
        f.write("## 1. 데이터 정제 및 중복 제거 내역\n\n")
        f.write(f"- **최초 데이터 건수**: {initial_len:,}개\n")
        f.write(f"- **업종 필터링**: 과학·기술 및 교육 업종 무관 데이터 **{removed_categories_cnt:,}개 제외** (필터링 후 {filtered_len:,}개)\n")
        f.write(f"- **중복 데이터 정제**: 상호명과 도로명주소가 동일한 중복 데이터 **{removed_duplicates_cnt:,}개 제거** (첫 번째 행만 유지)\n")
        f.write(f"- **최종 유효 데이터 건수**: **{dedup_len:,}개**\n\n")
        
        f.write("### 중복 발생 상세 샘플 (일부)\n")
        f.write("동일한 주소와 상호명으로 등록되어 중복 처리된 데이터의 일부 사례입니다.\n\n")
        f.write("| 상가업소번호 | 상호명 | 도로명주소 |\n")
        f.write("| --- | --- | --- |\n")
        # 중복 발생 데이터의 상위 5개 샘플 기록
        sample_dup = dup_df[['상가업소번호', '상호명', '도로명주소']].sort_values(by='상호명').head(5)
        for _, row in sample_dup.iterrows():
            f.write(f"| {row['상가업소번호']} | {row['상호명']} | {row['도로명주소']} |\n")
        f.write("\n---\n\n")
        
        # 1. 브랜드별 추출 결과
        f.write("## 2. 브랜드별 추출 결과 (중복 제거 후)\n\n")
        f.write("| 브랜드 | 매장 수 | 비율 |\n")
        f.write("| --- | --- | --- |\n")
        f.write(f"| 롯데리아 (Lotteria) | {total_lot:,}개 | {total_lot/total_sum*100:.2f}% |\n")
        f.write(f"| 맥도날드 (McDonald's) | {total_mc:,}개 | {total_mc/total_sum*100:.2f}% |\n")
        f.write(f"| 버거킹 (Burger King) | {total_bk:,}개 | {total_bk/total_sum*100:.2f}% |\n")
        f.write(f"| KFC | {total_kfc:,}개 | {total_kfc/total_sum*100:.2f}% |\n")
        f.write(f"| **합계** | **{total_sum:,}개** | **100.00%** |\n\n")
        
        # 2. 시도별 추출 현황
        f.write("## 3. 시도별 추출 현황\n\n")
        f.write("| 시도코드 | 시도명 | 버거킹 | 맥도날드 | KFC | 롯데리아 | 합계 |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for _, row in sido_grouped.iterrows():
            f.write(f"| {row['시도코드']} | {row['정제_시도명']} | {row['버거킹']:,} | {row['맥도날드']:,} | {row['KFC']:,} | {row['롯데리아']:,} | **{row['합계']:,}** |\n")
        f.write(f"| **전체** | **전국** | **{total_bk:,}** | **{total_mc:,}** | **{total_kfc:,}** | **{total_lot:,}** | **{total_sum:,}** |\n\n")
        
        # 3. 지역별(시도명) 브랜드 교차표
        f.write("## 4. 지역별(시도명) 브랜드 교차표\n\n")
        f.write("| 시도명 | KFC | 롯데리아 | 맥도날드 | 버거킹 | 총계 |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for idx, row in sido_crosstab.iterrows():
            if idx == '총계':
                continue
            f.write(f"| {idx} | {row['KFC']:,} | {row['롯데리아']:,} | {row['맥도날드']:,} | {row['버거킹']:,} | **{row['총계']:,}** |\n")
        f.write(f"| **총계** | **{sido_crosstab.loc['총계', 'KFC']:,}** | **{sido_crosstab.loc['총계', '롯데리아']:,}** | **{sido_crosstab.loc['총계', '맥도날드']:,}** | **{sido_crosstab.loc['총계', '버거킹']:,}** | **{sido_crosstab.loc['총계', '총계']:,}** |\n\n")
        
        # 4. 브랜드별 상권업종대분류명 교차표
        f.write("## 5. 브랜드별 상권업종대분류명 교차표 (중복 제거 후)\n\n")
        f.write("| 상권업종대분류명 | 버거킹 | 맥도날드 | KFC | 롯데리아 | 합계 |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for idx, row in crosstab_df.iterrows():
            if idx == '합계':
                continue
            f.write(f"| {idx} | {row['버거킹']:,} | {row['맥도날드']:,} | {row['KFC']:,} | {row['롯데리아']:,} | **{row['합계']:,}** |\n")
        f.write(f"| **합계** | **{crosstab_df.loc['합계', '버거킹']:,}** | **{crosstab_df.loc['합계', '맥도날드']:,}** | **{crosstab_df.loc['합계', 'KFC']:,}** | **{crosstab_df.loc['합계', '롯데리아']:,}** | **{crosstab_df.loc['합계', '합계']:,}** |\n\n")
        
        # 5. 시군구별 상세 추출 현황
        f.write("## 6. 시군구별 상세 추출 현황\n\n")
        f.write("> **참고**: '시도코드'와 '시군구코드'를 기준으로 고유값을 식별하고 명칭을 정제하여 그룹화하였습니다.\n\n")
        f.write("| 시도명 | 시군구코드 | 시군구명 | 버거킹 | 맥도날드 | KFC | 롯데리아 | 합계 |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for _, row in sigungu_grouped.iterrows():
            f.write(f"| {row['정제_시도명']} | {row['시군구코드']} | {row['정제_시군구명']} | {row['버거킹']} | {row['맥도날드']} | {row['KFC']} | {row['롯데리아']} | **{row['합계']}** |\n")
            
    print(f"최종 중복 제거 및 리포트 갱신이 완료되었습니다: {report_path}")

if __name__ == '__main__':
    process_and_analyze_burger_data()
