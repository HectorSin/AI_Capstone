"""
전체 파이프라인 DAG

이 DAG는 AI 팟캐스트 생성의 전체 파이프라인을 관리합니다.
URL 분석 → 주제 생성 → 스크립트 생성 → 오디오 생성
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import os
import sys
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('/opt/airflow/ai_modules')

from modules.ai_workflow import AIWorkflow
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
    'full_pipeline_dag',
    default_args=default_args,
    description='AI 팟캐스트 생성 전체 파이프라인',
    schedule_interval=None,
    max_active_runs=1,
    tags=['ai', 'full-pipeline', 'podcast-generation'],
    doc_md=__doc__,
)

def prepare_pipeline_data(**context) -> Dict[str, Any]:
    """
    파이프라인 데이터를 준비하는 함수
    
    Returns:
        Dict[str, Any]: 준비된 파이프라인 데이터
    """
    # DAG Run conf에서 설정 가져오기
    dag_run_conf = context.get('dag_run').conf or {}
    
    job_id = dag_run_conf.get('job_id')
    user_id = dag_run_conf.get('user_id')
    input_data = dag_run_conf.get('input_data', {})
    
    print(f"파이프라인 데이터 준비 - Job ID: {job_id}, User ID: {user_id}")
    
    # 파이프라인 설정
    pipeline_config = {
        'job_id': job_id,
        'user_id': user_id,
        'category': input_data.get('category', 'GOOGLE'),
        'host1_name': input_data.get('host1_name', '김테크'),
        'host2_name': input_data.get('host2_name', '박AI'),
        'search_recency': input_data.get('search_recency', 'week'),
        'include_audio': input_data.get('include_audio', True),
        'execution_date': context['ds'],
        'dag_run_id': context['dag_run'].run_id,
    }
    
    print(f"파이프라인 설정: {pipeline_config}")
    return pipeline_config

def run_url_analysis(**context) -> Dict[str, Any]:
    """
    URL 분석을 실행하는 함수
    
    Returns:
        Dict[str, Any]: URL 분석 결과
    """
    pipeline_config = context['task_instance'].xcom_pull(task_ids='prepare_pipeline_data')
    
    print("URL 분석 실행 중...")
    
    try:
        # URL 분석 DAG 실행을 위한 설정
        url_analysis_conf = {
            'job_id': pipeline_config['job_id'],
            'user_id': pipeline_config['user_id'],
            'input_data': {
                'category': pipeline_config['category'],
                'search_recency': pipeline_config['search_recency']
            }
        }
        
        # URL 분석 결과 시뮬레이션 (실제로는 TriggerDagRunOperator 사용)
        result = {
            'job_id': pipeline_config['job_id'],
            'user_id': pipeline_config['user_id'],
            'news_data': {
                'category': pipeline_config['category'],
                'articles': [
                    {
                        'title': f"{pipeline_config['category']} 최신 뉴스 1",
                        'text': f"{pipeline_config['category']} 분야의 최신 동향에 대한 상세 내용입니다.",
                        'date': pipeline_config['execution_date'],
                        'news_url': f"https://example.com/news1"
                    },
                    {
                        'title': f"{pipeline_config['category']} 최신 뉴스 2",
                        'text': f"{pipeline_config['category']} 분야의 혁신적인 기술에 대한 내용입니다.",
                        'date': pipeline_config['execution_date'],
                        'news_url': f"https://example.com/news2"
                    }
                ]
            },
            'status': 'success',
            'completed_at': datetime.now().isoformat()
        }
        
        print(f"URL 분석 완료: {len(result['news_data']['articles'])}개 기사")
        return result
        
    except Exception as e:
        print(f"URL 분석 중 오류 발생: {e}")
        raise AirflowException(f"URL 분석 실패: {str(e)}")

def run_topic_generation(**context) -> Dict[str, Any]:
    """
    주제 생성을 실행하는 함수
    
    Returns:
        Dict[str, Any]: 주제 생성 결과
    """
    pipeline_config = context['task_instance'].xcom_pull(task_ids='prepare_pipeline_data')
    url_analysis_result = context['task_instance'].xcom_pull(task_ids='run_url_analysis')
    
    print("주제 생성 실행 중...")
    
    try:
        # 주제 생성 결과 시뮬레이션
        result = {
            'job_id': pipeline_config['job_id'],
            'user_id': pipeline_config['user_id'],
            'topic_data': {
                'title': f"{pipeline_config['category']} 분야 최신 동향",
                'summary': f"{pipeline_config['category']} 분야의 최신 동향에 대한 종합 분석",
                'full_content': f"# {pipeline_config['category']} 분야 최신 동향\\n\\n## 요약\\n{pipeline_config['category']} 분야의 최신 동향에 대한 종합 분석입니다.\\n\\n## 주요 내용\\n- 최신 기술 동향\\n- 시장 분석\\n- 향후 전망",
                'category': pipeline_config['category'],
                'created_at': datetime.now().isoformat()
            },
            'status': 'success',
            'completed_at': datetime.now().isoformat()
        }
        
        print("주제 생성 완료")
        return result
        
    except Exception as e:
        print(f"주제 생성 중 오류 발생: {e}")
        raise AirflowException(f"주제 생성 실패: {str(e)}")

def run_script_generation(**context) -> Dict[str, Any]:
    """
    스크립트 생성을 실행하는 함수
    
    Returns:
        Dict[str, Any]: 스크립트 생성 결과
    """
    pipeline_config = context['task_instance'].xcom_pull(task_ids='prepare_pipeline_data')
    topic_result = context['task_instance'].xcom_pull(task_ids='run_topic_generation')
    
    print("스크립트 생성 실행 중...")
    
    try:
        # 스크립트 생성 결과 시뮬레이션
        result = {
            'job_id': pipeline_config['job_id'],
            'user_id': pipeline_config['user_id'],
            'script_data': {
                'title': f"{pipeline_config['category']} - 팟캐스트 대본",
                'content': f"{pipeline_config['host1_name']}: 안녕하세요, 여러분! {pipeline_config['host1_name']}입니다.\\n{pipeline_config['host2_name']}: 안녕하세요, {pipeline_config['host2_name']}입니다.\\n{pipeline_config['host1_name']}: 오늘은 {pipeline_config['category']} 분야의 최신 동향에 대해 이야기해보겠습니다.\\n{pipeline_config['host2_name']}: 네, 정말 흥미로운 주제들이 많네요.",
                'host1_name': pipeline_config['host1_name'],
                'host2_name': pipeline_config['host2_name'],
                'category': pipeline_config['category'],
                'created_at': datetime.now().isoformat()
            },
            'status': 'success',
            'completed_at': datetime.now().isoformat()
        }
        
        print("스크립트 생성 완료")
        return result
        
    except Exception as e:
        print(f"스크립트 생성 중 오류 발생: {e}")
        raise AirflowException(f"스크립트 생성 실패: {str(e)}")

def run_audio_generation(**context) -> Dict[str, Any]:
    """
    오디오 생성을 실행하는 함수
    
    Returns:
        Dict[str, Any]: 오디오 생성 결과
    """
    pipeline_config = context['task_instance'].xcom_pull(task_ids='prepare_pipeline_data')
    script_result = context['task_instance'].xcom_pull(task_ids='run_script_generation')
    
    print("오디오 생성 실행 중...")
    
    # 오디오 생성이 비활성화된 경우
    if not pipeline_config.get('include_audio', True):
        print("오디오 생성이 비활성화되어 있습니다.")
        return {
            'job_id': pipeline_config['job_id'],
            'user_id': pipeline_config['user_id'],
            'status': 'skipped',
            'message': '오디오 생성 비활성화',
            'completed_at': datetime.now().isoformat()
        }
    
    try:
        # 오디오 생성 결과 시뮬레이션
        result = {
            'job_id': pipeline_config['job_id'],
            'user_id': pipeline_config['user_id'],
            'audio_data': {
                'file_path': f"/home/smart/capstone/data/output/{pipeline_config['category']}_{pipeline_config['execution_date'].replace('-', '')}/audio/podcast_{pipeline_config['execution_date'].replace('-', '')}.mp3",
                'file_size_mb': 15.5,
                'category': pipeline_config['category'],
                'created_at': datetime.now().isoformat()
            },
            'status': 'success',
            'completed_at': datetime.now().isoformat()
        }
        
        print(f"오디오 생성 완료: {result['audio_data']['file_size_mb']}MB")
        return result
        
    except Exception as e:
        print(f"오디오 생성 중 오류 발생: {e}")
        raise AirflowException(f"오디오 생성 실패: {str(e)}")

def finalize_pipeline(**context) -> Dict[str, Any]:
    """
    파이프라인을 완료하고 결과를 정리하는 함수
    
    Returns:
        Dict[str, Any]: 최종 결과
    """
    pipeline_config = context['task_instance'].xcom_pull(task_ids='prepare_pipeline_data')
    url_analysis_result = context['task_instance'].xcom_pull(task_ids='run_url_analysis')
    topic_result = context['task_instance'].xcom_pull(task_ids='run_topic_generation')
    script_result = context['task_instance'].xcom_pull(task_ids='run_script_generation')
    audio_result = context['task_instance'].xcom_pull(task_ids='run_audio_generation')
    
    print("파이프라인 완료 처리 중...")
    
    # 최종 결과 구성
    final_result = {
        'job_id': pipeline_config['job_id'],
        'user_id': pipeline_config['user_id'],
        'category': pipeline_config['category'],
        'hosts': [pipeline_config['host1_name'], pipeline_config['host2_name']],
        'search_recency': pipeline_config['search_recency'],
        'execution_date': pipeline_config['execution_date'],
        'dag_run_id': pipeline_config['dag_run_id'],
        'created_at': datetime.now().isoformat(),
        'results': {
            'url_analysis': url_analysis_result,
            'topic_generation': topic_result,
            'script_generation': script_result,
            'audio_generation': audio_result
        },
        'workflow_info': {
            'total_articles': len(url_analysis_result.get('news_data', {}).get('articles', [])),
            'has_audio': audio_result.get('status') == 'success',
            'audio_size_mb': audio_result.get('audio_data', {}).get('file_size_mb', 0)
        }
    }
    
    # 결과를 로그에 출력
    print("=" * 60)
    print("AI 팟캐스트 생성 파이프라인 완료!")
    print(f"Job ID: {final_result['job_id']}")
    print(f"카테고리: {final_result['category']}")
    print(f"진행자: {', '.join(final_result['hosts'])}")
    print(f"수집 기사: {final_result['workflow_info']['total_articles']}개")
    print(f"오디오 생성: {'예' if final_result['workflow_info']['has_audio'] else '아니오'}")
    if final_result['workflow_info']['has_audio']:
        print(f"오디오 크기: {final_result['workflow_info']['audio_size_mb']}MB")
    print("=" * 60)
    
    return final_result

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

prepare_data_task = PythonOperator(
    task_id='prepare_pipeline_data',
    python_callable=prepare_pipeline_data,
    dag=dag,
)

url_analysis_task = PythonOperator(
    task_id='run_url_analysis',
    python_callable=run_url_analysis,
    dag=dag,
)

topic_generation_task = PythonOperator(
    task_id='run_topic_generation',
    python_callable=run_topic_generation,
    dag=dag,
)

script_generation_task = PythonOperator(
    task_id='run_script_generation',
    python_callable=run_script_generation,
    dag=dag,
)

audio_generation_task = PythonOperator(
    task_id='run_audio_generation',
    python_callable=run_audio_generation,
    dag=dag,
)

finalize_task = PythonOperator(
    task_id='finalize_pipeline',
    python_callable=finalize_pipeline,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> prepare_data_task
prepare_data_task >> url_analysis_task >> topic_generation_task >> script_generation_task >> audio_generation_task >> finalize_task >> end_task
