"""
이 스크립트는 burger.csv 데이터에서 중복된 행이나 중복된 상가업소번호가 존재하는지 확인하고
그 중복 내역(어느 컬럼이 겹치는지, 중복 건수는 얼마인지)을 검사합니다.
"""
import pandas as pd

file_path = 'burger_index/data/burger.csv'

try:
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"현재 데이터 총 행수: {len(df)}")
    
    # 1. 완전 중복 행 확인 (모든 컬럼이 일치)
    all_dup = df[df.duplicated(keep=False)]
    print(f"1. 모든 컬럼이 완벽히 중복된 행수: {len(all_dup)} (고유 중복 세트 수: {len(df[df.duplicated(keep='first')])})")
    if len(all_dup) > 0:
        print("완전 중복 샘플:")
        print(all_dup[['상가업소번호', '상호명', '도로명주소']].head(6))
        
    # 2. 상가업소번호 기준 중포 확인 (소상공인 데이터의 PK인 상가업소번호 중복)
    id_dup = df[df.duplicated(subset=['상가업소번호'], keep=False)]
    print(f"\n2. 상가업소번호(ID) 기준 중복 행수: {len(id_dup)} (고유 ID 중복 세트 수: {len(df[df.duplicated(subset=['상가업소번호'], keep='first')])})")
    if len(id_dup) > 0:
        print("상가업소번호 중복 샘플:")
        print(id_dup[['상가업소번호', '상호명', '도로명주소']].sort_values(by='상가업소번호').head(6))
        
    # 3. 상호명 + 도로명주소 기준 중복 확인
    addr_dup = df[df.duplicated(subset=['상호명', '도로명주소'], keep=False)]
    print(f"\n3. 상호명 및 도로명주소가 동일한 중복 행수: {len(addr_dup)} (고유 중복 세트 수: {len(df[df.duplicated(subset=['상호명', '도로명주소'], keep='first')])})")
    if len(addr_dup) > 0:
        print("상호명+도로명주소 중복 샘플:")
        print(addr_dup[['상가업소번호', '상호명', '도로명주소']].sort_values(by='상호명').head(6))

except Exception as e:
    print(f"Error: {e}")
