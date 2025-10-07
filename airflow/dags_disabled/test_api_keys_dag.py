"""
API 키 테스트 DAG

API 키가 없을 때 적절한 에러 메시지가 나오는지 테스트하는 DAG
"""

import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('/opt/airflow/ai_modules')

# 기본 인수
default_args = {
    'owner': 'ai-podcast',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}

# DAG 정의
dag = DAG(
    'test_api_keys',
    default_args=default_args,
    description='API 키 테스트 DAG',
    schedule_interval=None,  # 수동 실행만
    catchup=False,
    tags=['test', 'api-keys'],
)

def test_api_keys_validation(**context):
    """API 키 검증 테스트"""
    try:
        from modules.ai_workflow import AIWorkflow
        
        print("=" * 80)
        print("🧪 API 키 검증 테스트 시작")
        print("=" * 80)
        
        # API 키 없이 AIWorkflow 초기화 시도
        try:
            workflow = AIWorkflow(
                perplexity_api_key="",  # 빈 문자열
                google_api_key="",      # 빈 문자열
                naver_clova_client_id="",  # 빈 문자열
                naver_clova_client_secret=""  # 빈 문자열
            )
            print("❌ 예상과 다름: API 키가 없어도 초기화가 성공했습니다.")
            return {"status": "unexpected_success", "message": "API 키 없이도 초기화 성공"}
            
        except ValueError as e:
            print("✅ 예상대로 동작: API 키 없음으로 인한 ValueError 발생")
            print(f"에러 메시지: {e}")
            return {"status": "expected_error", "message": str(e)}
            
        except Exception as e:
            print(f"❌ 예상과 다른 에러: {type(e).__name__}: {e}")
            return {"status": "unexpected_error", "message": str(e)}
            
    except ImportError as e:
        print(f"❌ 모듈 임포트 실패: {e}")
        return {"status": "import_error", "message": str(e)}
    
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {e}")
        return {"status": "unexpected_error", "message": str(e)}

def test_with_dummy_keys(**context):
    """더미 API 키로 테스트"""
    try:
        from modules.ai_workflow import AIWorkflow
        
        print("=" * 80)
        print("🧪 더미 API 키로 테스트 시작")
        print("=" * 80)
        
        # 더미 API 키로 AIWorkflow 초기화 시도
        try:
            workflow = AIWorkflow(
                perplexity_api_key="dummy_perplexity_key",
                google_api_key="dummy_google_key",
                naver_clova_client_id="dummy_clova_id",
                naver_clova_client_secret="dummy_clova_secret"
            )
            print("✅ 더미 API 키로 초기화 성공")
            print("시스템 상태:", workflow.get_system_status())
            return {"status": "success", "message": "더미 API 키로 초기화 성공"}
            
        except Exception as e:
            print(f"❌ 더미 API 키로도 실패: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}
            
    except ImportError as e:
        print(f"❌ 모듈 임포트 실패: {e}")
        return {"status": "import_error", "message": str(e)}
    
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {e}")
        return {"status": "unexpected_error", "message": str(e)}

# Task 정의
start_task = DummyOperator(task_id='start', dag=dag)

test_empty_keys_task = PythonOperator(
    task_id='test_empty_api_keys',
    python_callable=test_api_keys_validation,
    dag=dag
)

test_dummy_keys_task = PythonOperator(
    task_id='test_dummy_api_keys',
    python_callable=test_with_dummy_keys,
    dag=dag
)

end_task = DummyOperator(task_id='end', dag=dag)

# Task 의존성 설정
start_task >> test_empty_keys_task >> test_dummy_keys_task >> end_task
