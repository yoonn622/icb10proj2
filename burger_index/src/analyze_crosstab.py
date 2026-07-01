"""
이 스크립트는 burger.csv 데이터를 기반으로 각 버거 브랜드 파생변수와
상권업종대분류명 간의 교차표(Crosstab)를 작성하고, 그 결과를 분석 보고서(burger_report.md)에 추가합니다.
"""

import os
import pandas as pd

def add_crosstab_to_report():
    csv_path = 'burger_index/data/burger.csv'
    report_path = 'burger_index/report/burger_report.md'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} 파일이 존재하지 않습니다.")
        return
        
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    # 각 브랜드별 파생변수가 존재하는지 확인하고, 없을 경우 생성
    brands = ['버거킹', '맥도날드', 'KFC', '롯데리아']
    for brand in brands:
        flag_col = f"{brand}_여부"
        if flag_col not in df.columns:
            if brand == '버거킹':
                df[flag_col] = df['상호명'].str.contains(r'버거킹|burger\s?king', case=False, na=False)
            elif brand == '맥도날드':
                df[flag_col] = df['상호명'].str.contains(r'맥도날드|mcdonald', case=False, na=False)
            elif brand == 'KFC':
                df[flag_col] = df['상호명'].str.contains(r'kfc|케이에프씨', case=False, na=False)
            elif brand == '롯데리아':
                df[flag_col] = df['상호명'].str.contains(r'롯데리아|lotteria', case=False, na=False)
                
    # 상권업종대분류명 결측치 처리
    df['상권업종대분류명'] = df['상권업종대분류명'].fillna('미분류')
    
    # 교차표 데이터 집계
    ct_data = {}
    for brand in brands:
        flag_col = f"{brand}_여부"
        # 각 브랜드가 참(True)인 행을 대상으로 상권업종대분류명 별 빈도수 계산
        ct_data[brand] = df[df[flag_col] == True].groupby('상권업종대분류명').size()
        
    # 데이터프레임으로 변환 및 정렬
    crosstab_df = pd.DataFrame(ct_data).fillna(0).astype(int)
    
    # 행 합계 및 열 합계 계산
    crosstab_df['합계'] = crosstab_df.sum(axis=1)
    
    # 전체 합계 행 추가
    total_row = crosstab_df.sum(axis=0)
    total_row.name = '합계'
    crosstab_df = pd.concat([crosstab_df, pd.DataFrame([total_row])])
    
    # 인덱스 이름 설정
    crosstab_df.index.name = '상권업종대분류명'
    
    # 기존 보고서 파일 읽기
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
    else:
        report_content = "# 버거 브랜드 전국 매장 분포 리포트\n\n"
        
    # 교차표 마크다운 생성
    crosstab_md = "## 4. 브랜드별 상권업종대분류명 교차표\n\n"
    crosstab_md += "| 상권업종대분류명 | 버거킹 | 맥도날드 | KFC | 롯데리아 | 합계 |\n"
    crosstab_md += "| --- | --- | --- | --- | --- | --- |\n"
    
    # 합계 행을 제외하고 출력한 뒤, 마지막에 합계 행을 강조하여 출력
    for idx, row in crosstab_df.iterrows():
        if idx == '합계':
            continue
        crosstab_md += f"| {idx} | {row['버거킹']:,} | {row['맥도날드']:,} | {row['KFC']:,} | {row['롯데리아']:,} | **{row['합계']:,}** |\n"
    
    # 합계 행 추가
    crosstab_md += f"| **합계** | **{crosstab_df.loc['합계', '버거킹']:,}** | **{crosstab_df.loc['합계', '맥도날드']:,}** | **{crosstab_df.loc['합계', 'KFC']:,}** | **{crosstab_df.loc['합계', '롯데리아']:,}** | **{crosstab_df.loc['합계', '합계']:,}** |\n\n"
    
    # 기존 보고서에 "4. 브랜드별 상권업종대분류명 교차표" 섹션이 이미 있는지 확인하고 대체 또는 추가
    if "## 4. 브랜드별 상권업종대분류명 교차표" in report_content:
        # 기존 섹션 앞부분과 뒷부분 분할하여 교체
        parts = report_content.split("## 4. 브랜드별 상권업종대분류명 교차표")
        # 다음 대단원이 있으면 그 뒤는 보존
        next_section_idx = parts[1].find("\n## ")
        if next_section_idx != -1:
            report_content = parts[0] + crosstab_md + parts[1][next_section_idx:]
        else:
            report_content = parts[0] + crosstab_md
    else:
        # 맨 뒤에 추가
        report_content = report_content.strip() + "\n\n" + crosstab_md
        
    # 보고서 갱신
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print("교차표가 보고서에 성공적으로 반영되었습니다.")
    print(crosstab_df)

if __name__ == '__main__':
    add_crosstab_to_report()
