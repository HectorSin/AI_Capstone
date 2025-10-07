"""
Airflow DAG 모니터링 유틸리티

DAG 실행 상태를 모니터링하고 메트릭을 수집하는 함수들
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from airflow.models import TaskInstance, DagRun
from airflow.utils.context import Context
from airflow.utils.state import State

logger = logging.getLogger(__name__)

def collect_task_metrics(context: Context) -> Dict[str, Any]:
    """
    Task 실행 메트릭을 수집하는 함수
    
    Args:
        context: Airflow Context 객체
    
    Returns:
        Dict[str, Any]: 수집된 메트릭
    """
    task_instance: TaskInstance = context['task_instance']
    dag_run: DagRun = context['dag_run']
    
    # Task 실행 시간 계산
    start_date = task_instance.start_date
    end_date = task_instance.end_date or datetime.now()
    duration = (end_date - start_date).total_seconds() if start_date else 0
    
    metrics = {
        'task_id': task_instance.task_id,
        'dag_id': task_instance.dag_id,
        'dag_run_id': dag_run.run_id,
        'execution_date': context['execution_date'],
        'state': task_instance.state,
        'try_number': task_instance.try_number,
        'start_date': start_date.isoformat() if start_date else None,
        'end_date': end_date.isoformat(),
        'duration_seconds': duration,
        'log_url': task_instance.log_url,
        'collected_at': datetime.now().isoformat()
    }
    
    logger.info(f"Task 메트릭 수집: {task_instance.task_id} - {duration:.2f}초")
    
    # XCom에 메트릭 저장
    task_instance.xcom_push(key='task_metrics', value=metrics)
    
    return metrics

def collect_dag_metrics(dag_run: DagRun) -> Dict[str, Any]:
    """
    DAG 실행 메트릭을 수집하는 함수
    
    Args:
        dag_run: DagRun 객체
    
    Returns:
        Dict[str, Any]: 수집된 메트릭
    """
    # DAG 실행 시간 계산
    start_date = dag_run.start_date
    end_date = dag_run.end_date or datetime.now()
    duration = (end_date - start_date).total_seconds() if start_date else 0
    
    # Task 상태별 개수 계산
    task_states = {}
    for task_instance in dag_run.get_task_instances():
        state = task_instance.state
        task_states[state] = task_states.get(state, 0) + 1
    
    metrics = {
        'dag_id': dag_run.dag_id,
        'dag_run_id': dag_run.run_id,
        'execution_date': dag_run.execution_date.isoformat(),
        'state': dag_run.state,
        'start_date': start_date.isoformat() if start_date else None,
        'end_date': end_date.isoformat(),
        'duration_seconds': duration,
        'task_states': task_states,
        'total_tasks': sum(task_states.values()),
        'collected_at': datetime.now().isoformat()
    }
    
    logger.info(f"DAG 메트릭 수집: {dag_run.dag_id} - {duration:.2f}초")
    
    return metrics

def check_dag_health(dag_run: DagRun) -> Dict[str, Any]:
    """
    DAG 건강 상태를 확인하는 함수
    
    Args:
        dag_run: DagRun 객체
    
    Returns:
        Dict[str, Any]: 건강 상태 정보
    """
    health_info = {
        'dag_id': dag_run.dag_id,
        'dag_run_id': dag_run.run_id,
        'execution_date': dag_run.execution_date.isoformat(),
        'is_healthy': True,
        'issues': [],
        'checked_at': datetime.now().isoformat()
    }
    
    # Task 상태 확인
    failed_tasks = []
    running_tasks = []
    stuck_tasks = []
    
    for task_instance in dag_run.get_task_instances():
        if task_instance.state == State.FAILED:
            failed_tasks.append(task_instance.task_id)
        elif task_instance.state == State.RUNNING:
            running_tasks.append(task_instance.task_id)
            
            # 30분 이상 실행 중인 Task 확인
            if task_instance.start_date and (datetime.now() - task_instance.start_date).total_seconds() > 1800:
                stuck_tasks.append(task_instance.task_id)
    
    # 건강 상태 판단
    if failed_tasks:
        health_info['is_healthy'] = False
        health_info['issues'].append(f"실패한 Task: {failed_tasks}")
    
    if stuck_tasks:
        health_info['is_healthy'] = False
        health_info['issues'].append(f"응답 없는 Task: {stuck_tasks}")
    
    # DAG 실행 시간이 너무 긴 경우
    if dag_run.start_date and (datetime.now() - dag_run.start_date).total_seconds() > 3600:  # 1시간
        health_info['is_healthy'] = False
        health_info['issues'].append("DAG 실행 시간 초과")
    
    health_info['failed_tasks'] = failed_tasks
    health_info['running_tasks'] = running_tasks
    health_info['stuck_tasks'] = stuck_tasks
    
    logger.info(f"DAG 건강 상태: {dag_run.dag_id} - {'건강' if health_info['is_healthy'] else '문제 있음'}")
    
    return health_info

def send_health_alert(health_info: Dict[str, Any]) -> None:
    """
    건강 상태 알림을 보내는 함수
    
    Args:
        health_info: 건강 상태 정보
    """
    if not health_info['is_healthy']:
        try:
            # 실제 알림 구현 (이메일, 슬랙, 웹훅 등)
            logger.warning(f"DAG 건강 상태 알림: {health_info['dag_id']}")
            
            # 예시: 로그에 건강 상태 정보 출력
            logger.warning(f"""
            ===== DAG HEALTH ALERT =====
            DAG ID: {health_info['dag_id']}
            DAG Run ID: {health_info['dag_run_id']}
            Execution Date: {health_info['execution_date']}
            Issues: {', '.join(health_info['issues'])}
            Failed Tasks: {health_info['failed_tasks']}
            Stuck Tasks: {health_info['stuck_tasks']}
            Checked At: {health_info['checked_at']}
            ============================
            """)
            
        except Exception as e:
            logger.error(f"건강 상태 알림 전송 실패: {e}")

def log_performance_metrics(metrics: Dict[str, Any]) -> None:
    """
    성능 메트릭을 로깅하는 함수
    
    Args:
        metrics: 메트릭 정보
    """
    try:
        # 성능 메트릭 로깅
        logger.info(f"""
        ===== PERFORMANCE METRICS =====
        DAG ID: {metrics['dag_id']}
        Duration: {metrics['duration_seconds']:.2f}초
        Total Tasks: {metrics['total_tasks']}
        Task States: {metrics['task_states']}
        ===============================
        """)
        
        # 성능 임계값 확인
        if metrics['duration_seconds'] > 1800:  # 30분
            logger.warning(f"DAG 실행 시간이 길어짐: {metrics['duration_seconds']:.2f}초")
        
        # 실패율 확인
        total_tasks = metrics['total_tasks']
        failed_tasks = metrics['task_states'].get(State.FAILED, 0)
        if total_tasks > 0 and (failed_tasks / total_tasks) > 0.5:  # 50% 이상 실패
            logger.warning(f"DAG 실패율이 높음: {failed_tasks}/{total_tasks} ({failed_tasks/total_tasks*100:.1f}%)")
        
    except Exception as e:
        logger.error(f"성능 메트릭 로깅 실패: {e}")

def get_dag_summary(dag_run: DagRun) -> Dict[str, Any]:
    """
    DAG 실행 요약 정보를 생성하는 함수
    
    Args:
        dag_run: DagRun 객체
    
    Returns:
        Dict[str, Any]: 요약 정보
    """
    summary = {
        'dag_id': dag_run.dag_id,
        'dag_run_id': dag_run.run_id,
        'execution_date': dag_run.execution_date.isoformat(),
        'state': dag_run.state,
        'start_date': dag_run.start_date.isoformat() if dag_run.start_date else None,
        'end_date': dag_run.end_date.isoformat() if dag_run.end_date else None,
        'duration_seconds': 0,
        'task_summary': {},
        'created_at': datetime.now().isoformat()
    }
    
    # 실행 시간 계산
    if dag_run.start_date:
        end_time = dag_run.end_date or datetime.now()
        summary['duration_seconds'] = (end_time - dag_run.start_date).total_seconds()
    
    # Task 요약
    for task_instance in dag_run.get_task_instances():
        task_id = task_instance.task_id
        summary['task_summary'][task_id] = {
            'state': task_instance.state,
            'try_number': task_instance.try_number,
            'start_date': task_instance.start_date.isoformat() if task_instance.start_date else None,
            'end_date': task_instance.end_date.isoformat() if task_instance.end_date else None,
            'duration_seconds': 0
        }
        
        # Task 실행 시간 계산
        if task_instance.start_date:
            task_end_time = task_instance.end_date or datetime.now()
            summary['task_summary'][task_id]['duration_seconds'] = (task_end_time - task_instance.start_date).total_seconds()
    
    return summary
