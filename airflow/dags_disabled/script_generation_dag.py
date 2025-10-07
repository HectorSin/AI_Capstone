"""
스크립트 생성 DAG

이 DAG는 주제를 바탕으로 팟캐스트 대본을 생성합니다.
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

from modules.content_generation import ScriptGenerator
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
    'script_generation_dag',
    default_args=default_args,
    description='주제를 바탕으로 팟캐스트 대본 생성',
    schedule_interval=None,
    max_active_runs=1,
    tags=['ai', 'script-generation', 'podcast'],
    doc_md=__doc__,
)

def generate_script(**context) -> Dict[str, Any]:
    """
    팟캐스트 대본을 생성하는 함수
    
    Returns:
        Dict[str, Any]: 생성된 대본 정보
    """
    # DAG Run conf에서 설정 가져오기
    dag_run_conf = context.get('dag_run').conf or {}
    
    job_id = dag_run_conf.get('job_id')
    user_id = dag_run_conf.get('user_id')
    input_data = dag_run_conf.get('input_data', {})
    
    print(f"스크립트 생성 시작 - Job ID: {job_id}, User ID: {user_id}")
    
    try:
        # ScriptGenerator 초기화
        script_generator = ScriptGenerator()
        
        # 주제 데이터가 있는 경우 대본 생성
        if 'topic_data' in input_data:
            # 임시 보고서 파일 생성
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(input_data['topic_data']['full_content'])
                temp_report_file = f.name
            
            try:
                # 대본 생성
                host1_name = input_data.get('host1_name', '김테크')
                host2_name = input_data.get('host2_name', '박AI')
                
                script_content = script_generator.generate_podcast_script_from_md(
                    md_file_path=temp_report_file,
                    host1_name=host1_name,
                    host2_name=host2_name
                )
                
                if not script_content:
                    raise AirflowException("대본 생성 실패")
                
                # 결과 저장
                output_data = {
                    'job_id': job_id,
                    'user_id': user_id,
                    'script_data': {
                        'title': f"{input_data['topic_data']['title']} - 팟캐스트 대본",
                        'content': script_content,
                        'host1_name': host1_name,
                        'host2_name': host2_name,
                        'category': input_data['topic_data']['category'],
                        'created_at': datetime.now().isoformat()
                    },
                    'status': 'success',
                    'completed_at': datetime.now().isoformat()
                }
                
                print("스크립트 생성 완료")
                return output_data
                
            finally:
                # 임시 파일 삭제
                if os.path.exists(temp_report_file):
                    os.remove(temp_report_file)
        else:
            # 주제 데이터가 없는 경우 기본 대본 생성
            output_data = {
                'job_id': job_id,
                'user_id': user_id,
                'script_data': {
                    'title': f"{input_data.get('category', 'AI')} - 팟캐스트 대본",
                    'content': f"안녕하세요, {input_data.get('host1_name', '김테크')}입니다.\n안녕하세요, {input_data.get('host2_name', '박AI')}입니다.\n오늘은 {input_data.get('category', 'AI')} 분야의 최신 동향에 대해 이야기해보겠습니다.",
                    'host1_name': input_data.get('host1_name', '김테크'),
                    'host2_name': input_data.get('host2_name', '박AI'),
                    'category': input_data.get('category', 'AI'),
                    'created_at': datetime.now().isoformat()
                },
                'status': 'success',
                'completed_at': datetime.now().isoformat()
            }
            
            print("기본 스크립트 생성 완료")
            return output_data
        
    except Exception as e:
        print(f"스크립트 생성 중 오류 발생: {e}")
        error_data = {
            'job_id': job_id,
            'user_id': user_id,
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }
        raise AirflowException(f"스크립트 생성 실패: {str(e)}")

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

generate_script_task = PythonOperator(
    task_id='generate_script',
    python_callable=generate_script,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> generate_script_task >> end_task
