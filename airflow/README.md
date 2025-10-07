# AI 팟캐스트 생성 Airflow DAG

## 🎯 개요

이 프로젝트는 AI 팟캐스트 생성 시스템을 위한 Apache Airflow DAG들을 포함합니다. 각 AI 단계를 독립적인 DAG로 구현하여 모듈화하고 확장성을 높였습니다.

## 📋 구현된 DAG들

### 1. 메인 DAG
- **`ai_podcast_generation`**: 전체 AI 팟캐스트 생성 워크플로우
- **`full_pipeline_dag`**: 단계별 파이프라인 통합 DAG

### 2. 개별 AI 단계 DAG
- **`url_analysis_dag`**: URL 분석을 통한 뉴스 수집
- **`topic_generation_dag`**: 주제 생성 및 보고서 작성
- **`script_generation_dag`**: 팟캐스트 대본 생성
- **`audio_generation_dag`**: TTS를 통한 음성 파일 생성

### 3. 모니터링 DAG
- **`ai_podcast_monitoring`**: 시스템 상태 모니터링 및 알림

## 🏗️ DAG 구조

```
airflow/
├── dags/
│   ├── ai_podcast_dag.py          # 메인 AI 팟캐스트 생성 DAG
│   ├── url_analysis_dag.py        # URL 분석 DAG
│   ├── topic_generation_dag.py    # 주제 생성 DAG
│   ├── script_generation_dag.py   # 스크립트 생성 DAG
│   ├── audio_generation_dag.py    # 오디오 생성 DAG
│   ├── full_pipeline_dag.py       # 전체 파이프라인 DAG
│   ├── monitoring_dag.py          # 모니터링 DAG
│   ├── test_dags.py               # DAG 테스트 스크립트
│   └── utils/
│       ├── error_handlers.py      # 에러 처리 유틸리티
│       └── monitoring.py          # 모니터링 유틸리티
├── logs/                          # Airflow 로그
├── plugins/                       # Airflow 플러그인
├── data/                          # 데이터 저장소
├── airflow.cfg                    # Airflow 설정
├── requirements.txt               # Airflow 컨테이너용 Python 의존성
├── docker-compose.yml             # Docker Compose 설정
└── README.md                      # 이 파일
```

## 📦 의존성 관리

### Airflow 컨테이너용 requirements.txt
Airflow 컨테이너에서 사용하는 Python 패키지들은 `requirements.txt` 파일에 정의되어 있습니다:

- **LangChain 패키지**: `langchain==0.1.0`, `langchain-core==0.1.52`, `langsmith==0.1.147`
- **JSON 처리**: `orjson==3.10.15`
- **HTTP 클라이언트**: `requests==2.31.0`, `httpx==0.23.3`
- **데이터 검증**: `pydantic==2.5.2`

이 파일은 Docker Compose를 통해 Airflow 컨테이너에 자동으로 마운트되며, 컨테이너 시작 시 패키지들이 설치됩니다.

## 🚀 설치 및 실행

### 1. Docker Compose 사용 (권장)

```bash
# Airflow 디렉토리로 이동
cd /home/smart/capstone/airflow

# Docker Compose로 Airflow 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# Airflow UI 접속
# http://localhost:8080
# 사용자명: admin, 비밀번호: admin
```

### 2. 로컬 설치

```bash
# Python 가상환경 생성
python -m venv airflow_env
source airflow_env/bin/activate  # Linux/Mac
# airflow_env\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# Airflow 데이터베이스 초기화
airflow db init

# Airflow 사용자 생성
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Airflow 웹서버 시작
airflow webserver --port 8080

# 새 터미널에서 스케줄러 시작
airflow scheduler
```

## 🔧 DAG 실행 방법

### 1. Airflow UI에서 실행

1. Airflow UI 접속 (http://localhost:8080)
2. DAG 목록에서 원하는 DAG 선택
3. "Trigger DAG" 버튼 클릭
4. Configuration에 다음 JSON 입력:

```json
{
  "job_id": "test_job_001",
  "user_id": 1,
  "input_data": {
    "category": "GOOGLE",
    "host1_name": "김테크",
    "host2_name": "박AI",
    "search_recency": "week",
    "include_audio": true
  }
}
```

### 2. 명령행에서 실행

```bash
# DAG 실행
airflow dags trigger ai_podcast_generation \
  --conf '{"job_id": "test_job_001", "user_id": 1, "input_data": {"category": "GOOGLE"}}'

# DAG 상태 확인
airflow dags state ai_podcast_generation 2024-01-15

# Task 실행
airflow tasks run ai_podcast_generation collect_news 2024-01-15
```

## 📊 모니터링

### 1. DAG 상태 모니터링

- **Airflow UI**: http://localhost:8080
- **DAG 목록**: 모든 DAG의 실행 상태 확인
- **Task 로그**: 각 Task의 상세 로그 확인
- **그래프 뷰**: DAG 의존성 및 실행 흐름 시각화

### 2. 시스템 리소스 모니터링

```bash
# 모니터링 DAG 실행
airflow dags trigger ai_podcast_monitoring

# 시스템 리소스 확인
docker stats
```

### 3. 로그 확인

```bash
# Airflow 로그
tail -f /home/smart/capstone/airflow/logs/scheduler/latest/scheduler.log

# 특정 DAG 로그
tail -f /home/smart/capstone/airflow/logs/dags/ai_podcast_generation/collect_news/2024-01-15T10:00:00+00:00/1.log
```

## 🧪 테스트

### 1. DAG 검증

```bash
# DAG 검증 실행
python /home/smart/capstone/airflow/dags/test_dags.py

# 단위 테스트 실행
python -m pytest /home/smart/capstone/airflow/dags/test_dags.py -v
```

### 2. DAG 테스트 실행

```bash
# DAG 테스트 실행
airflow dags test ai_podcast_generation 2024-01-15

# Task 테스트 실행
airflow tasks test ai_podcast_generation collect_news 2024-01-15
```

## ⚙️ 설정

### 1. 환경변수 설정

```bash
# .env 파일 생성
cat > /home/smart/capstone/airflow/.env << EOF
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////home/smart/capstone/airflow/airflow.db
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True
EOF
```

### 2. DAG 설정

```python
# DAG 기본 설정
default_args = {
    'owner': 'ai-podcast-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}
```

## 🔍 문제 해결

### 1. 일반적인 문제

**DAG가 보이지 않는 경우:**
```bash
# DAG 파일 권한 확인
ls -la /home/smart/capstone/airflow/dags/

# Airflow 스케줄러 재시작
docker-compose restart airflow-scheduler
```

**Task 실행 실패:**
```bash
# Task 로그 확인
airflow tasks log ai_podcast_generation collect_news 2024-01-15

# DAG 재실행
airflow dags trigger ai_podcast_generation
```

### 2. 로그 분석

```bash
# 에러 로그 필터링
grep -i error /home/smart/capstone/airflow/logs/scheduler/latest/scheduler.log

# 특정 DAG 로그만 확인
find /home/smart/capstone/airflow/logs -name "*ai_podcast_generation*" -type f
```

## 📈 성능 최적화

### 1. 리소스 설정

```yaml
# docker-compose.yml에서 리소스 제한 설정
services:
  airflow-scheduler:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### 2. 병렬 처리

```python
# DAG 설정에서 병렬 처리 설정
dag = DAG(
    'ai_podcast_generation',
    max_active_runs=1,
    max_active_tasks=16,
    concurrency=16,
)
```

## 📚 추가 자료

- [Apache Airflow 공식 문서](https://airflow.apache.org/docs/)
- [Airflow DAG 모범 사례](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Airflow 모니터링 가이드](https://airflow.apache.org/docs/apache-airflow/stable/logging-monitoring/index.html)
