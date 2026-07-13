# SQLite 데이터베이스 구축을 통한 대시보드 로딩 성능 극대화 계획

이 계획은 850만 행의 Parquet 파일 및 엑셀 매핑 정보를 미리 집계하여 **SQLite 데이터베이스 파일 (`seoul_pops.db`)**로 가공·저장해 두고, 대시보드 구동 시점에는 Parquet 대신 이 최적화된 DB 테이블에서 데이터를 다이렉트로 가져와 대시보드 첫 로딩 속도를 20초 대에서 **1초 미만**으로 획기적으로 단축하기 위한 고도화 계획입니다.

## User Review Required

> [!IMPORTANT]
> - **SQLite 데이터베이스 구축**: 
>   - 일회성 DB 구축 스크립트(`build_db.py`)를 개발하여 Parquet 데이터와 Excel 데이터를 미리 가공, 결합하고 날짜 유형(주중/주말/전체) 및 공간적 요소를 집계한 테이블들을 생성해 `seoul_pops/data/seoul_pops.db` 파일로 저장합니다.
>   - 지도 분석용 구별 집계(`district_map_agg`), 동별 집계(`dong_map_agg`), 세부 분석용 동별 특성(`dong_demographics_agg`), 시간대별 추이(`time_pattern_agg`), 그리고 기술 통계 분석을 위한 1% 균등 샘플링(`statistical_sample`) 테이블로 구성합니다.
> - **대시보드 데이터 로더 개편**:
>   - `data_loader.py`가 Parquet 및 Excel을 직접 스캔하는 비효율적인 프로세스를 중단하고, 미리 구축된 SQLite 파일에 접속하여 캐싱(`st.cache_data`) 상태로 테이블을 로드하도록 쿼리 인터페이스를 재설계합니다.
> - **데이터 독립성 보장**:
>   - DB 파일 생성 이후에는 Parquet 파일의 압축 해제나 850만 행 연산 메모리 낭비 없이 대시보드가 단독 가동되어 서버 비용 및 디스크 입출력(I/O) 성능이 95% 이상 최적화됩니다.

## Open Questions

> [!NOTE]
> - SQLite 데이터베이스 파일(`seoul_pops.db`)의 용량은 약 10MB~20MB 내외로 축소될 것으로 계산되어 배포 및 관리 용이성이 극적으로 상승합니다. 원본 Parquet 데이터를 계속 보관할지, 아니면 DB 파일로 완전히 이전하여 가볍게 대시보드를 유지할지 선택하실 수 있습니다.

## Proposed Changes

### seoul_pops

`seoul_pops` 프로젝트 디렉토리 하위의 소스코드와 데이터 구조를 고도화합니다.

---

#### [NEW] [build_db.py](file:///c:/Users/82104/Desktop/icb10proj2/seoul_pops/src/build_db.py)

- 850만 행 데이터를 한 번 읽어 정제하고 집계 테이블을 생성하여 SQLite DB에 적재하는 파이프라인 파일입니다.
- 평일/주말 판별 Vectorized 연산을 적용하고, 구별/동별/시간대별/성별/연령대별로 그룹핑한 집계 데이터 및 1% 통계용 샘플 데이터셋을 SQLite에 저장합니다.

#### [MODIFY] [data_loader.py](file:///c:/Users/82104/Desktop/icb10proj2/seoul_pops/src/data_loader.py)

- SQLite DB 파일 (`seoul_pops.db`) 연결 및 조회 로직을 반영합니다.
- 기존 Parquet 로더 함수들을 SQLite 조회 함수들로 완전 대체하고, 각 데이터 조회 결과에 `st.cache_data`를 입혀 메모리 캐시 속도를 유지합니다.

#### [MODIFY] [app.py](file:///c:/Users/82104/Desktop/icb10proj2/seoul_pops/src/app.py)

- 개편된 `data_loader.py`의 SQLite 기반 로드 인터페이스 명칭과 동기화합니다.
- 대시보드 로딩 시 `st.spinner("생활인구 및 지리정보 데이터를 불러오고 있습니다...")` 스피너가 0.5초 이내에 빠르게 통과하는지 리팩토링 검증을 진행합니다.

---

## Verification Plan

### Automated Tests
- SQLite DB 구축 명령을 실행하여 데이터베이스 파일이 무결하게 생성되는지 검증합니다.
  ```powershell
  .venv\Scripts\python seoul_pops/src/build_db.py
  ```
- Streamlit을 재구동하여 초기 데이터 로딩 속도가 1초 이내로 단축되는지 로그 및 콘솔 지연 시간을 검증합니다.
- 브라우저 서브에이전트를 띄워 지도 조작 및 탭 전환 시 에러 팝업 없이 렌더링되는지 확인합니다.

### Manual Verification
- 지도의 구별/동별 선택, 시간대 슬라이더 조정 시 3구 KPI 카드와 Choropleth 밀도가 SQLite 매핑 데이터 기반으로 정상 갱신되는지 최종 확인합니다.
