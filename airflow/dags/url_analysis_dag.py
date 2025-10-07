"""
URL 분석 DAG

이 DAG는 URL 분석을 통한 뉴스 수집을 담당합니다.
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

from modules.data_collection import NewsCollector
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
    'url_analysis_dag',
    default_args=default_args,
    description='URL 분석을 통한 뉴스 수집',
    schedule_interval=None,
    max_active_runs=1,
    tags=['ai', 'url-analysis', 'news-collection'],
    doc_md=__doc__,
)

def analyze_urls(**context) -> Dict[str, Any]:
    """
    URL 분석을 수행하는 함수
    
    Returns:
        Dict[str, Any]: 분석 결과
    """
    # DAG Run conf에서 설정 가져오기
    dag_run_conf = context.get('dag_run').conf or {}
    
    job_id = dag_run_conf.get('job_id')
    user_id = dag_run_conf.get('user_id')
    input_data = dag_run_conf.get('input_data', {})
    
    print(f"URL 분석 시작 - Job ID: {job_id}, User ID: {user_id}")
    
    try:
        # NewsCollector 초기화
        news_collector = NewsCollector(
            api_key=AISettings.PERPLEXITY_API_KEY,
            config_path=AISettings.CONFIG_PATH
        )
        
        # URL 분석 수행
        category = input_data.get('category', 'GOOGLE')
        search_recency = input_data.get('search_recency', 'week')
        
        result = news_collector.collect_news_by_category(
            category=category,
            search_recency=search_recency
        )
        
        if 'error' in result:
            raise AirflowException(f"URL 분석 실패: {result['error']}")
        
        # 결과 저장
        output_data = {
            'job_id': job_id,
            'user_id': user_id,
            'category': category,
            'search_recency': search_recency,
            'result': result,
            'status': 'success',
            'completed_at': datetime.now().isoformat()
        }
        
        print(f"URL 분석 완료: {len(result.get('articles', []))}개 기사 수집")
        return output_data
        
    except Exception as e:
        print(f"URL 분석 중 오류 발생: {e}")
        error_data = {
            'job_id': job_id,
            'user_id': user_id,
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }
        raise AirflowException(f"URL 분석 실패: {str(e)}")

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

analyze_urls_task = PythonOperator(
    task_id='analyze_urls',
    python_callable=analyze_urls,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> analyze_urls_task >> end_task
