"""
AI 팟캐스트 생성 DAG

이 DAG는 AI 팟캐스트 생성의 전체 워크플로우를 관리합니다.
1. 데이터 수집 (뉴스 수집)
2. 콘텐츠 생성 (보고서 + 대본)
3. 오디오 처리 (TTS 음성 생성)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import sys
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.exceptions import AirflowException
from airflow.utils.dates import days_ago

# 유틸리티 임포트
from utils.error_handlers import handle_task_failure, handle_dag_failure, validate_task_inputs, retry_on_failure, cleanup_on_failure, log_task_progress
from utils.monitoring import collect_task_metrics, collect_dag_metrics, check_dag_health, send_health_alert, log_performance_metrics

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('/opt/airflow/ai_modules')

from modules.ai_workflow import AIWorkflow
from config.settings import AISettings

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
    'on_failure_callback': handle_task_failure,
    'on_retry_callback': retry_on_failure,
    'on_success_callback': collect_task_metrics,
}

# DAG 정의
dag = DAG(
    'ai_podcast_generation',
    default_args=default_args,
    description='AI 팟캐스트 생성 워크플로우',
    schedule_interval=None,  # 수동 실행
    max_active_runs=1,
    tags=['ai', 'podcast', 'content-generation'],
    doc_md=__doc__,
)

def get_dag_config(**context) -> Dict[str, Any]:
    """
    DAG 실행 설정을 가져오는 함수
    
    Returns:
        Dict[str, Any]: DAG 실행 설정
    """
    # Airflow Variable에서 설정 가져오기
    category = Variable.get("podcast_category", default_var="GOOGLE")
    host1_name = Variable.get("host1_name", default_var="김테크")
    host2_name = Variable.get("host2_name", default_var="박AI")
    search_recency = Variable.get("search_recency", default_var="week")
    include_audio = Variable.get("include_audio", default_var="true").lower() == "true"
    
    # DAG Run conf에서 설정 가져오기 (우선순위 높음)
    dag_run_conf = context.get('dag_run').conf or {}
    
    config = {
        'category': dag_run_conf.get('category', category),
        'host1_name': dag_run_conf.get('host1_name', host1_name),
        'host2_name': dag_run_conf.get('host2_name', host2_name),
        'search_recency': dag_run_conf.get('search_recency', search_recency),
        'include_audio': dag_run_conf.get('include_audio', include_audio),
        'output_dir': '/home/smart/capstone/data/output',
        'execution_date': context['ds'],
        'dag_run_id': context['dag_run'].run_id,
    }
    
    print(f"DAG 설정: {config}")
    return config

def validate_environment(**context) -> Dict[str, Any]:
    """
    환경 설정을 검증하는 함수
    
    Returns:
        Dict[str, Any]: 검증 결과
    """
    print("환경 설정 검증 중...")
    
    # 설정 검증
    validation = AISettings.validate_settings()
    
    if not validation['valid']:
        error_msg = f"환경 설정 오류: {', '.join(validation['errors'])}"
        print(error_msg)
        raise AirflowException(error_msg)
    
    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"경고: {warning}")
    
    print("환경 설정 검증 완료")
    return validation

def collect_news_data(**context) -> Dict[str, Any]:
    """
    뉴스 데이터를 수집하는 함수
    
    Returns:
        Dict[str, Any]: 수집된 뉴스 데이터
    """
    config = context['task_instance'].xcom_pull(task_ids='get_config')
    
    # 진행 상황 로깅
    log_task_progress(context, f"뉴스 수집 시작: {config['category']}")
    
    try:
        # 입력값 검증
        if not validate_task_inputs(context, ['category']):
            raise AirflowException("필수 입력값 검증 실패")
        
        # AI 워크플로우 초기화
        workflow = AIWorkflow(
            perplexity_api_key=AISettings.PERPLEXITY_API_KEY,
            google_api_key=AISettings.GOOGLE_API_KEY,
            naver_clova_client_id=AISettings.NAVER_CLOVA_CLIENT_ID,
            naver_clova_client_secret=AISettings.NAVER_CLOVA_CLIENT_SECRET,
            config_path=AISettings.CONFIG_PATH
        )
        
        # 뉴스 수집
        news_result = workflow.news_collector.collect_news_by_category(
            category=config['category'],
            search_recency=config['search_recency']
        )
        
        if 'error' in news_result:
            raise AirflowException(f"뉴스 수집 실패: {news_result['error']}")
        
        # 결과를 XCom에 저장
        log_task_progress(context, f"뉴스 수집 완료: {len(news_result.get('articles', []))}개 기사")
        return news_result
        
    except Exception as e:
        log_task_progress(context, f"뉴스 수집 중 오류 발생: {e}")
        cleanup_on_failure(context)
        raise AirflowException(f"뉴스 수집 실패: {str(e)}")

def generate_content(**context) -> Dict[str, Any]:
    """
    콘텐츠를 생성하는 함수 (보고서 + 대본)
    
    Returns:
        Dict[str, Any]: 생성된 콘텐츠 정보
    """
    config = context['task_instance'].xcom_pull(task_ids='get_config')
    news_data = context['task_instance'].xcom_pull(task_ids='collect_news')
    
    print(f"콘텐츠 생성 시작: {config['category']}")
    
    try:
        # AI 워크플로우 초기화
        workflow = AIWorkflow(
            perplexity_api_key=AISettings.PERPLEXITY_API_KEY,
            google_api_key=AISettings.GOOGLE_API_KEY,
            naver_clova_client_id=AISettings.NAVER_CLOVA_CLIENT_ID,
            naver_clova_client_secret=AISettings.NAVER_CLOVA_CLIENT_SECRET,
            config_path=AISettings.CONFIG_PATH
        )
        
        # 임시 뉴스 파일 생성
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
            temp_news_file = f.name
        
        try:
            # 콘텐츠 생성
            content_result = workflow.content_manager.run_complete_workflow(
                json_file_path=temp_news_file,
                category=config['category'],
                host1_name=config['host1_name'],
                host2_name=config['host2_name']
            )
            
            if not content_result:
                raise AirflowException("콘텐츠 생성 실패")
            
            print("콘텐츠 생성 완료")
            return content_result
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_news_file):
                os.remove(temp_news_file)
        
    except Exception as e:
        print(f"콘텐츠 생성 중 오류 발생: {e}")
        raise AirflowException(f"콘텐츠 생성 실패: {str(e)}")

def generate_audio(**context) -> Dict[str, Any]:
    """
    오디오를 생성하는 함수 (TTS)
    
    Returns:
        Dict[str, Any]: 생성된 오디오 정보
    """
    config = context['task_instance'].xcom_pull(task_ids='get_config')
    content_result = context['task_instance'].xcom_pull(task_ids='generate_content')
    
    print(f"오디오 생성 시작: {config['category']}")
    
    # 오디오 생성이 비활성화된 경우
    if not config['include_audio']:
        print("오디오 생성이 비활성화되어 있습니다.")
        return {'audio_generated': False, 'message': '오디오 생성 비활성화'}
    
    try:
        # AI 워크플로우 초기화
        workflow = AIWorkflow(
            perplexity_api_key=AISettings.PERPLEXITY_API_KEY,
            google_api_key=AISettings.GOOGLE_API_KEY,
            naver_clova_client_id=AISettings.NAVER_CLOVA_CLIENT_ID,
            naver_clova_client_secret=AISettings.NAVER_CLOVA_CLIENT_SECRET,
            config_path=AISettings.CONFIG_PATH
        )
        
        # TTS 사용 가능 여부 확인
        if not workflow.audio_manager.is_tts_available():
            print("TTS 시스템을 사용할 수 없습니다.")
            return {'audio_generated': False, 'message': 'TTS 시스템 사용 불가'}
        
        # 오디오 생성
        audio_result = workflow.audio_manager.create_audio_workflow(
            script_file_path=content_result['script_file'],
            category=config['category']
        )
        
        if not audio_result:
            raise AirflowException("오디오 생성 실패")
        
        print("오디오 생성 완료")
        return audio_result
        
    except Exception as e:
        print(f"오디오 생성 중 오류 발생: {e}")
        raise AirflowException(f"오디오 생성 실패: {str(e)}")

def finalize_workflow(**context) -> Dict[str, Any]:
    """
    워크플로우를 완료하고 결과를 정리하는 함수
    
    Returns:
        Dict[str, Any]: 최종 결과
    """
    config = context['task_instance'].xcom_pull(task_ids='get_config')
    news_data = context['task_instance'].xcom_pull(task_ids='collect_news')
    content_result = context['task_instance'].xcom_pull(task_ids='generate_content')
    audio_result = context['task_instance'].xcom_pull(task_ids='generate_audio')
    
    print("워크플로우 완료 처리 중...")
    
    # 최종 결과 구성
    final_result = {
        'category': config['category'],
        'hosts': [config['host1_name'], config['host2_name']],
        'search_recency': config['search_recency'],
        'execution_date': config['execution_date'],
        'dag_run_id': config['dag_run_id'],
        'created_at': datetime.now().isoformat(),
        'files': {
            'news_data': news_data,
            'report_file': content_result['report_file'],
            'script_file': content_result['script_file']
        },
        'folders': content_result['folders'],
        'workflow_info': {
            'total_articles': len(news_data.get('articles', [])),
            'has_audio': audio_result.get('audio_generated', False)
        }
    }
    
    if audio_result.get('audio_generated', False):
        final_result['files']['audio_file'] = audio_result['audio_file']
        final_result['workflow_info']['audio_size_mb'] = audio_result.get('file_size_mb', 0)
    
    # 결과를 로그에 출력
    print("=" * 60)
    print("AI 팟캐스트 생성 워크플로우 완료!")
    print(f"카테고리: {final_result['category']}")
    print(f"진행자: {', '.join(final_result['hosts'])}")
    print(f"수집 기사: {final_result['workflow_info']['total_articles']}개")
    print(f"오디오 생성: {'예' if final_result['workflow_info']['has_audio'] else '아니오'}")
    print("=" * 60)
    
    return final_result

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

get_config_task = PythonOperator(
    task_id='get_config',
    python_callable=get_dag_config,
    dag=dag,
)

validate_env_task = PythonOperator(
    task_id='validate_environment',
    python_callable=validate_environment,
    dag=dag,
)

collect_news_task = PythonOperator(
    task_id='collect_news',
    python_callable=collect_news_data,
    dag=dag,
)

generate_content_task = PythonOperator(
    task_id='generate_content',
    python_callable=generate_content,
    dag=dag,
)

generate_audio_task = PythonOperator(
    task_id='generate_audio',
    python_callable=generate_audio,
    dag=dag,
)

finalize_task = PythonOperator(
    task_id='finalize_workflow',
    python_callable=finalize_workflow,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> get_config_task >> validate_env_task >> collect_news_task
collect_news_task >> generate_content_task >> generate_audio_task >> finalize_task >> end_task
