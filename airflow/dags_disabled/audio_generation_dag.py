"""
오디오 생성 DAG

이 DAG는 팟캐스트 대본을 바탕으로 음성 파일을 생성합니다.
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

from modules.audio_processing import AudioManager
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
    'audio_generation_dag',
    default_args=default_args,
    description='팟캐스트 대본을 바탕으로 음성 파일 생성',
    schedule_interval=None,
    max_active_runs=1,
    tags=['ai', 'audio-generation', 'tts'],
    doc_md=__doc__,
)

def generate_audio(**context) -> Dict[str, Any]:
    """
    음성 파일을 생성하는 함수
    
    Returns:
        Dict[str, Any]: 생성된 오디오 정보
    """
    # DAG Run conf에서 설정 가져오기
    dag_run_conf = context.get('dag_run').conf or {}
    
    job_id = dag_run_conf.get('job_id')
    user_id = dag_run_conf.get('user_id')
    input_data = dag_run_conf.get('input_data', {})
    
    print(f"오디오 생성 시작 - Job ID: {job_id}, User ID: {user_id}")
    
    try:
        # AudioManager 초기화
        audio_manager = AudioManager(
            client_id=AISettings.NAVER_CLOVA_CLIENT_ID,
            client_secret=AISettings.NAVER_CLOVA_CLIENT_SECRET
        )
        
        # TTS 사용 가능 여부 확인
        if not audio_manager.is_tts_available():
            print("TTS 시스템을 사용할 수 없습니다.")
            return {
                'job_id': job_id,
                'user_id': user_id,
                'status': 'skipped',
                'message': 'TTS 시스템 사용 불가',
                'completed_at': datetime.now().isoformat()
            }
        
        # 스크립트 데이터가 있는 경우 오디오 생성
        if 'script_data' in input_data:
            # 임시 스크립트 파일 생성
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(input_data['script_data']['content'])
                temp_script_file = f.name
            
            try:
                # 오디오 생성
                category = input_data['script_data']['category']
                output_dir = f"/home/smart/capstone/data/output/{category}_{datetime.now().strftime('%Y%m%d')}/audio"
                
                audio_result = audio_manager.create_audio_workflow(
                    script_file_path=temp_script_file,
                    category=category,
                    output_dir=output_dir
                )
                
                if not audio_result:
                    raise AirflowException("오디오 생성 실패")
                
                # 결과 저장
                output_data = {
                    'job_id': job_id,
                    'user_id': user_id,
                    'audio_data': {
                        'file_path': audio_result['audio_file'],
                        'file_size_mb': audio_result['file_size_mb'],
                        'category': category,
                        'created_at': datetime.now().isoformat()
                    },
                    'status': 'success',
                    'completed_at': datetime.now().isoformat()
                }
                
                print(f"오디오 생성 완료: {audio_result['file_size_mb']}MB")
                return output_data
                
            finally:
                # 임시 파일 삭제
                if os.path.exists(temp_script_file):
                    os.remove(temp_script_file)
        else:
            # 스크립트 데이터가 없는 경우 기본 오디오 생성
            output_data = {
                'job_id': job_id,
                'user_id': user_id,
                'audio_data': {
                    'file_path': None,
                    'file_size_mb': 0,
                    'category': input_data.get('category', 'AI'),
                    'created_at': datetime.now().isoformat()
                },
                'status': 'skipped',
                'message': '스크립트 데이터 없음',
                'completed_at': datetime.now().isoformat()
            }
            
            print("스크립트 데이터가 없어 오디오 생성 건너뜀")
            return output_data
        
    except Exception as e:
        print(f"오디오 생성 중 오류 발생: {e}")
        error_data = {
            'job_id': job_id,
            'user_id': user_id,
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }
        raise AirflowException(f"오디오 생성 실패: {str(e)}")

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

generate_audio_task = PythonOperator(
    task_id='generate_audio',
    python_callable=generate_audio,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> generate_audio_task >> end_task
