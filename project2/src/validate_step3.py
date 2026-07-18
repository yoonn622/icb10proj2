"""
Step 3 공공데이터 연계 매핑 결과물(ec_mapped_with_api.csv)의 데이터 정합성,
데이터 구조, 결측치, 하드 필터 태깅 샘플을 데이터 과학자 관점에서 최종 검증하는 스크립트입니다.
"""

import os
import sys
import pandas as pd

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def validate_pipeline():
    ec_raw_path = os.path.join("project2", "data", "ec_standardized_total.csv")
    mapped_path = os.path.join("project2", "data", "ec_mapped_with_api.csv")
    
    print("=" * 65)
    print("🔬 [데이터 과학자 관점] Step 3 결과물 최종 정합성 검증 보고서")
    print("=" * 65 + "\n")
    
    # 1. 파일 존재 여부 및 행 수 비교
    if not os.path.exists(mapped_path):
        print(f"❌ 오류: {mapped_path} 파일이 존재하지 않습니다.")
        return
        
    df_raw = pd.read_csv(ec_raw_path, encoding='utf-8-sig')
    df_mapped = pd.read_csv(mapped_path, encoding='utf-8-sig')
    
    len_raw = len(df_raw)
    len_mapped = len(df_mapped)
    
    print("1️⃣ [전체 데이터 정합성 확인]")
    print(f" - 이커머스 원본 통합 행 수 : {len_raw:,}건")
    print(f" - 매핑 최종 결과물 행 수   : {len_mapped:,}건")
    
    if len_raw == len_mapped:
        print(" -> ✅ [정합성 검증 성공] 전체 행 수가 정확히 일치합니다! (28,239건)")
    else:
        print(f" -> ⚠️ [경고] 행 수가 불일치합니다! ({len_raw} vs {len_mapped})")
        
    print("\n--- 데이터프레임 구조 (.info()) ---")
    df_mapped.info()
    
    print("\n" + "=" * 65)
    print("2️⃣ [안전 필터 태깅 상태 샘플 검증]")
    print("=" * 65)
    
    # hard_filter_trigger가 None/NaN이 아닌 항목 필터링
    df_filtered = df_mapped[
        df_mapped['hard_filter_trigger'].notna() & 
        (df_mapped['hard_filter_trigger'] != 'None')
    ]
    
    print(f" - 안전 필터 태깅 총 건수: {len(df_filtered):,}건")
    print(" - 태깅 카운트 상세:")
    print(df_filtered['hard_filter_trigger'].value_counts())
    
    print("\n[하드 필터 적용 상품 샘플 (상위 5건)]")
    sample_cols = ['product_name', 'matched_ingredient', 'hard_filter_trigger']
    sample_df = df_filtered[sample_cols].head(5)
    
    for idx, row in sample_df.reset_index(drop=True).iterrows():
        print(f"\n Sample #{idx+1}")
        print(f"   · 상품명: {row['product_name']}")
        print(f"   · 매핑 원료: {row['matched_ingredient']}")
        print(f"   · 적용 필터: {row['hard_filter_trigger']}")

    print("\n" + "=" * 65)
    print("3️⃣ [결측치 및 데이터 무결성 점검]")
    print("=" * 65)
    null_summary = df_mapped.isnull().sum()
    print(" - 컬럼별 결측치 수:")
    print(null_summary)

if __name__ == "__main__":
    validate_pipeline()
