"""
매핑된 통합 결과 파일(ec_mapped_with_api.csv)의 성분 매핑 현황과
하드 필터 태깅 수량을 검증하고 요약 결과를 출력하는 스크립트입니다.
"""

import os
import sys
import pandas as pd

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    file_path = os.path.join("project2", "data", "ec_mapped_with_api.csv")
    if not os.path.exists(file_path):
        print(f"❌ 파일 없음: {file_path}")
        return

    df = pd.read_csv(file_path, encoding='utf-8-sig')
    print("=== [매핑 성분 top 15] ===")
    print(df['matched_ingredient'].value_counts().head(15))
    print("\n=== [하드 필터 태깅 현황] ===")
    print(df['hard_filter_trigger'].value_counts(dropna=False))

if __name__ == "__main__":
    main()
