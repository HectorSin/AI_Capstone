"""
AI 모듈 임포트 테스트 DAG
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago

# AI 모듈 경로 추가
sys.path.append('/opt/airflow/ai_modules')

# DAG 기본 설정
default_args = {
    'owner': 'ai-podcast-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

# DAG 정의
dag = DAG(
    'test_ai_import',
    default_args=default_args,
    description='AI 모듈 임포트 테스트',
    schedule_interval=None,  # 수동 실행
    max_active_runs=1,
    tags=['test', 'ai', 'import'],
)

def test_ai_import(**context) -> Dict[str, Any]:
    """
    AI 모듈 임포트 테스트
    """
    try:
        print("🔍 AI 모듈 임포트 테스트 시작...")
        
        # 기본 모듈들 임포트 테스트
        from modules.data_collection import NewsCollector
        print("✅ NewsCollector 임포트 성공")
        
        from modules.content_generation import ReportGenerator, ScriptGenerator
        print("✅ ReportGenerator, ScriptGenerator 임포트 성공")
        
        from modules.audio_processing import AudioManager
        print("✅ AudioManager 임포트 성공")
        
        from modules.ai_workflow import AIWorkflow
        print("✅ AIWorkflow 임포트 성공")
        
        print("🎉 모든 AI 모듈 임포트 성공!")
        return {"status": "success", "message": "모든 AI 모듈 임포트 성공"}
        
    except Exception as e:
        print(f"❌ AI 모듈 임포트 실패: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"AI 모듈 임포트 실패: {e}"}

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

test_import_task = PythonOperator(
    task_id='test_ai_import',
    python_callable=test_ai_import,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> test_import_task >> end_task
