"""
Airflow DAG 에러 처리 유틸리티

DAG 실행 중 발생하는 에러를 처리하고 알림을 보내는 함수들
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from airflow.exceptions import AirflowException
from airflow.models import TaskInstance
from airflow.utils.context import Context

logger = logging.getLogger(__name__)

def handle_task_failure(context: Context) -> None:
    """
    Task 실패 시 에러 처리 함수
    
    Args:
        context: Airflow Context 객체
    """
    task_instance: TaskInstance = context['task_instance']
    dag_run = context['dag_run']
    
    error_info = {
        'task_id': task_instance.task_id,
        'dag_id': task_instance.dag_id,
        'execution_date': context['execution_date'],
        'dag_run_id': dag_run.run_id,
        'error_message': str(context.get('exception', 'Unknown error')),
        'log_url': task_instance.log_url,
        'failed_at': datetime.now().isoformat()
    }
    
    logger.error(f"Task 실패: {error_info}")
    
    # 에러 정보를 XCom에 저장
    task_instance.xcom_push(key='error_info', value=error_info)
    
    # 추가적인 에러 처리 로직 (알림, 로깅 등)
    send_error_notification(error_info)

def handle_dag_failure(context: Context) -> None:
    """
    DAG 실패 시 에러 처리 함수
    
    Args:
        context: Airflow Context 객체
    """
    dag_run = context['dag_run']
    
    error_info = {
        'dag_id': dag_run.dag_id,
        'execution_date': context['execution_date'],
        'dag_run_id': dag_run.run_id,
        'error_message': 'DAG 실행 실패',
        'failed_at': datetime.now().isoformat()
    }
    
    logger.error(f"DAG 실패: {error_info}")
    
    # DAG 레벨 에러 처리
    send_dag_failure_notification(error_info)

def send_error_notification(error_info: Dict[str, Any]) -> None:
    """
    에러 알림을 보내는 함수
    
    Args:
        error_info: 에러 정보 딕셔너리
    """
    try:
        # 실제 알림 구현 (이메일, 슬랙, 웹훅 등)
        logger.info(f"에러 알림 전송: {error_info['task_id']}")
        
        # 예시: 로그에 에러 정보 출력
        logger.error(f"""
        ===== TASK FAILURE NOTIFICATION =====
        Task ID: {error_info['task_id']}
        DAG ID: {error_info['dag_id']}
        Execution Date: {error_info['execution_date']}
        Error Message: {error_info['error_message']}
        Log URL: {error_info['log_url']}
        Failed At: {error_info['failed_at']}
        ======================================
        """)
        
    except Exception as e:
        logger.error(f"에러 알림 전송 실패: {e}")

def send_dag_failure_notification(error_info: Dict[str, Any]) -> None:
    """
    DAG 실패 알림을 보내는 함수
    
    Args:
        error_info: 에러 정보 딕셔너리
    """
    try:
        # 실제 알림 구현
        logger.info(f"DAG 실패 알림 전송: {error_info['dag_id']}")
        
        # 예시: 로그에 DAG 실패 정보 출력
        logger.error(f"""
        ===== DAG FAILURE NOTIFICATION =====
        DAG ID: {error_info['dag_id']}
        Execution Date: {error_info['execution_date']}
        DAG Run ID: {error_info['dag_run_id']}
        Error Message: {error_info['error_message']}
        Failed At: {error_info['failed_at']}
        ====================================
        """)
        
    except Exception as e:
        logger.error(f"DAG 실패 알림 전송 실패: {e}")

def validate_task_inputs(context: Context, required_inputs: list) -> bool:
    """
    Task 입력값을 검증하는 함수
    
    Args:
        context: Airflow Context 객체
        required_inputs: 필수 입력값 목록
    
    Returns:
        bool: 검증 성공 여부
    """
    try:
        dag_run_conf = context.get('dag_run').conf or {}
        
        for input_key in required_inputs:
            if input_key not in dag_run_conf:
                raise AirflowException(f"필수 입력값이 없습니다: {input_key}")
        
        return True
        
    except Exception as e:
        logger.error(f"입력값 검증 실패: {e}")
        return False

def retry_on_failure(context: Context, max_retries: int = 3) -> bool:
    """
    실패 시 재시도 여부를 결정하는 함수
    
    Args:
        context: Airflow Context 객체
        max_retries: 최대 재시도 횟수
    
    Returns:
        bool: 재시도 여부
    """
    task_instance: TaskInstance = context['task_instance']
    
    if task_instance.try_number <= max_retries:
        logger.info(f"Task 재시도: {task_instance.try_number}/{max_retries}")
        return True
    else:
        logger.error(f"최대 재시도 횟수 초과: {max_retries}")
        return False

def cleanup_on_failure(context: Context) -> None:
    """
    실패 시 정리 작업을 수행하는 함수
    
    Args:
        context: Airflow Context 객체
    """
    try:
        # 임시 파일 정리
        import tempfile
        import os
        
        # 임시 디렉토리 정리
        temp_dir = tempfile.gettempdir()
        ai_temp_files = [f for f in os.listdir(temp_dir) if f.startswith('ai_')]
        
        for file in ai_temp_files:
            file_path = os.path.join(temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"임시 파일 삭제: {file_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {file_path}, {e}")
        
        logger.info("실패 시 정리 작업 완료")
        
    except Exception as e:
        logger.error(f"정리 작업 중 오류 발생: {e}")

def log_task_progress(context: Context, progress_message: str) -> None:
    """
    Task 진행 상황을 로깅하는 함수
    
    Args:
        context: Airflow Context 객체
        progress_message: 진행 상황 메시지
    """
    task_instance: TaskInstance = context['task_instance']
    
    logger.info(f"[{task_instance.task_id}] {progress_message}")
    
    # XCom에 진행 상황 저장
    task_instance.xcom_push(key='progress', value={
        'message': progress_message,
        'timestamp': datetime.now().isoformat(),
        'task_id': task_instance.task_id
    })
