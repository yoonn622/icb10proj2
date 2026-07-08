"""
서울시 생활인구 Tidy-Data 데이터셋을 기반으로 fg-data-profiling(ydata-profiling)
도구를 사용하여 데이터 프로파일링 리포트(HTML)를 생성하는 스크립트입니다.
대용량 데이터(850만 행)의 연산 효율성을 위해 샘플링(n=100,000)을 적용합니다.
"""

import pandas as pd
from ydata_profiling import ProfileReport
import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def main():
    parquet_path = "seoul_pops/data/LOCAL_PEOPLE_DONG_202606_tidy.parquet"
    output_html_path = "seoul_pops/report/data_profiling_report.html"

    
    print("=== [1] 데이터 로드 ===")
    df = pd.read_parquet(parquet_path)
    
    # 854만 행 전체에 대해 프로파일링을 수행하면 OOM 및 무한 대기가 발생할 수 있으므로
    # 통계적 정합성이 유지되는 100,000행 수준으로 무작위 샘플링을 적용
    print(f"Original shape: {df.shape}")
    sample_size = 100000
    df_sample = df.sample(n=sample_size, random_state=42)
    print(f"Sampled shape: {df_sample.shape}")
    
    print("=== [2] ydata-profiling (fg-data-profiling) 보고서 빌드 ===")
    # 대용량 텍스트/카테고리 연산 오버헤드 방지를 위해 minimal=True 설정 권장
    profile = ProfileReport(
        df_sample, 
        title="서울시 동별 생활인구 데이터 프로파일링 보고서", 
        minimal=True
    )
    
    print("=== [3] HTML 파일 저장 ===")
    profile.to_file(output_html_path)
    print(f"HTML 프로파일링 리포트가 성공적으로 저장되었습니다: {output_html_path}")

if __name__ == "__main__":
    main()
