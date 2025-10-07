"""
주제 생성 DAG

이 DAG는 수집된 뉴스 데이터를 바탕으로 주제를 생성합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import os
import sys
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('/opt/airflow/ai_modules')

from modules.content_generation import ReportGenerator
from config.settings import AISettings

# DAG 기본 설정
default_args = {
    'owner': 'ai-podcast-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

# DAG 정의
dag = DAG(
    'topic_generation_dag',
    default_args=default_args,
    description='뉴스 데이터를 바탕으로 주제 생성',
    schedule_interval=None,
    max_active_runs=1,
    tags=['ai', 'topic-generation', 'content-creation'],
    doc_md=__doc__,
)

def generate_topic(**context) -> Dict[str, Any]:
    """
    주제를 생성하는 함수
    
    Returns:
        Dict[str, Any]: 생성된 주제 정보
    """
    # DAG Run conf에서 설정 가져오기
    dag_run_conf = context.get('dag_run').conf or {}
    
    job_id = dag_run_conf.get('job_id')
    user_id = dag_run_conf.get('user_id')
    input_data = dag_run_conf.get('input_data', {})
    
    print(f"주제 생성 시작 - Job ID: {job_id}, User ID: {user_id}")
    
    try:
        # ReportGenerator 초기화
        report_generator = ReportGenerator()
        
        # 뉴스 데이터가 있는 경우 보고서 생성
        if 'news_data' in input_data:
            # 임시 파일 생성
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(input_data['news_data'], f, ensure_ascii=False, indent=2)
                temp_news_file = f.name
            
            try:
                # 보고서 생성
                report_content = report_generator.generate_comprehensive_report(temp_news_file)
                
                if not report_content:
                    raise AirflowException("보고서 생성 실패")
                
                # 결과 저장
                output_data = {
                    'job_id': job_id,
                    'user_id': user_id,
                    'topic_data': {
                        'title': input_data.get('category', 'AI 뉴스'),
                        'summary': report_content[:500] + "..." if len(report_content) > 500 else report_content,
                        'full_content': report_content,
                        'category': input_data.get('category', 'AI'),
                        'created_at': datetime.now().isoformat()
                    },
                    'status': 'success',
                    'completed_at': datetime.now().isoformat()
                }
                
                print("주제 생성 완료")
                return output_data
                
            finally:
                # 임시 파일 삭제
                if os.path.exists(temp_news_file):
                    os.remove(temp_news_file)
        else:
            # 뉴스 데이터가 없는 경우 기본 주제 생성
            output_data = {
                'job_id': job_id,
                'user_id': user_id,
                'topic_data': {
                    'title': input_data.get('category', 'AI 뉴스'),
                    'summary': f"{input_data.get('category', 'AI')} 분야의 최신 동향",
                    'full_content': f"{input_data.get('category', 'AI')} 분야의 최신 동향에 대한 분석",
                    'category': input_data.get('category', 'AI'),
                    'created_at': datetime.now().isoformat()
                },
                'status': 'success',
                'completed_at': datetime.now().isoformat()
            }
            
            print("기본 주제 생성 완료")
            return output_data
        
    except Exception as e:
        print(f"주제 생성 중 오류 발생: {e}")
        error_data = {
            'job_id': job_id,
            'user_id': user_id,
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }
        raise AirflowException(f"주제 생성 실패: {str(e)}")

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

generate_topic_task = PythonOperator(
    task_id='generate_topic',
    python_callable=generate_topic,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> generate_topic_task >> end_task
