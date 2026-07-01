"""
이 스크립트는 burger_index/data 폴더 내의 전국 소상공인 상가정보 CSV 데이터에서
상호명에 '버거킹', '맥도날드', 'KFC', '롯데리아' (영문명 포함)가 들어간 데이터를 추출하여
하나의 통합 파일(burger.csv)로 저장합니다.
"""

import os
import glob
import pandas as pd

def extract_burger_data():
    # 데이터 경로 및 출력 경로 설정
    data_dir = 'burger_index/data'
    output_file = os.path.join(data_dir, 'burger.csv')
    
    # 상가정보 CSV 파일 목록 수집
    csv_files = glob.glob(os.path.join(data_dir, '소상공인시장진흥공단_상가(상권)정보_*.csv'))
    print(f"찾은 CSV 파일 개수: {len(csv_files)}")
    
    # 추출할 브랜드 정규식 패턴 (대소문자 무관)
    # 버거킹: 버거킹, burgerking, burger king
    # 맥도날드: 맥도날드, mcdonald, mcdonalds, mcdonald's
    # KFC: kfc, 케이에프씨
    # 롯데리아: 롯데리아, lotteria
    pattern = r'버거킹|burger\s?king|맥도날드|mcdonald|kfc|케이에프씨|롯데리아|lotteria'
    
    collected_dfs = []
    
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        print(f"파일 처리 중: {file_name}")
        try:
            # 대용량 파일이므로 메모리 효율을 위해 low_memory=False 사용
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            
            # 상호명이 NaN인 행은 제외
            df = df[df['상호명'].notna()]
            
            # 정규식 패턴 매칭 (대소문자 구분 없음)
            matched_df = df[df['상호명'].str.contains(pattern, case=False, na=False, regex=True)]
            
            if not matched_df.empty:
                print(f"  -> {file_name}: {len(matched_df)}개 행 추출됨")
                collected_dfs.append(matched_df)
            else:
                print(f"  -> {file_name}: 매칭되는 데이터 없음")
                
        except Exception as e:
            print(f"  -> {file_name} 처리 중 에러 발생: {e}")
            
    if collected_dfs:
        # 데이터 통합
        final_df = pd.concat(collected_dfs, ignore_index=True)
        print(f"\n전체 추출된 행의 개수: {len(final_df)}")
        
        # 파일 저장 (UTF-8 인코딩)
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"성공적으로 '{output_file}'에 저장되었습니다.")
        
        # 각 브랜드별 매칭 건수 임시 요약 출력
        summary = {
            '버거킹': final_df['상호명'].str.contains(r'버거킹|burger\s?king', case=False, na=False).sum(),
            '맥도날드': final_df['상호명'].str.contains(r'맥도날드|mcdonald', case=False, na=False).sum(),
            'KFC': final_df['상호명'].str.contains(r'kfc|케이에프씨', case=False, na=False).sum(),
            '롯데리아': final_df['상호명'].str.contains(r'롯데리아|lotteria', case=False, na=False).sum()
        }
        print("브랜드별 추출 건수:")
        for brand, count in summary.items():
            print(f"  - {brand}: {count}건")
    else:
        print("추출된 데이터가 없습니다.")

if __name__ == '__main__':
    extract_burger_data()
