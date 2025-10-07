"""
모니터링 DAG

이 DAG는 AI 팟캐스트 생성 시스템의 전반적인 상태를 모니터링합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import DagRun, TaskInstance
from airflow.utils.state import State
from airflow.utils.dates import days_ago

# 유틸리티 임포트
from utils.monitoring import collect_dag_metrics, check_dag_health, send_health_alert, log_performance_metrics, get_dag_summary

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
    'ai_podcast_monitoring',
    default_args=default_args,
    description='AI 팟캐스트 생성 시스템 모니터링',
    schedule_interval=timedelta(minutes=30),  # 30분마다 실행
    max_active_runs=1,
    tags=['monitoring', 'ai', 'podcast'],
    doc_md=__doc__,
)

def monitor_ai_dags(**context) -> Dict[str, Any]:
    """
    AI 관련 DAG들의 상태를 모니터링하는 함수
    
    Returns:
        Dict[str, Any]: 모니터링 결과
    """
    print("AI DAG 모니터링 시작...")
    
    # 모니터링할 DAG 목록
    ai_dag_ids = [
        'ai_podcast_generation',
        'url_analysis_dag',
        'topic_generation_dag',
        'script_generation_dag',
        'audio_generation_dag',
        'full_pipeline_dag'
    ]
    
    monitoring_results = {
        'monitored_dags': [],
        'total_dags': len(ai_dag_ids),
        'healthy_dags': 0,
        'unhealthy_dags': 0,
        'monitored_at': datetime.now().isoformat()
    }
    
    for dag_id in ai_dag_ids:
        try:
            # 최근 24시간 내의 DAG Run 조회
            dag_runs = DagRun.find(
                dag_id=dag_id,
                execution_date_gte=datetime.now() - timedelta(days=1)
            )
            
            if not dag_runs:
                print(f"DAG {dag_id}: 최근 24시간 내 실행 기록 없음")
                continue
            
            # 가장 최근 DAG Run 선택
            latest_dag_run = max(dag_runs, key=lambda x: x.execution_date)
            
            # DAG 메트릭 수집
            dag_metrics = collect_dag_metrics(latest_dag_run)
            
            # DAG 건강 상태 확인
            health_info = check_dag_health(latest_dag_run)
            
            # 건강 상태 알림
            if not health_info['is_healthy']:
                send_health_alert(health_info)
            
            # 성능 메트릭 로깅
            log_performance_metrics(dag_metrics)
            
            # 결과 저장
            dag_result = {
                'dag_id': dag_id,
                'latest_run_id': latest_dag_run.run_id,
                'execution_date': latest_dag_run.execution_date.isoformat(),
                'state': latest_dag_run.state,
                'is_healthy': health_info['is_healthy'],
                'issues': health_info['issues'],
                'duration_seconds': dag_metrics['duration_seconds'],
                'total_tasks': dag_metrics['total_tasks'],
                'task_states': dag_metrics['task_states']
            }
            
            monitoring_results['monitored_dags'].append(dag_result)
            
            if health_info['is_healthy']:
                monitoring_results['healthy_dags'] += 1
            else:
                monitoring_results['unhealthy_dags'] += 1
            
            print(f"DAG {dag_id}: {'건강' if health_info['is_healthy'] else '문제 있음'}")
            
        except Exception as e:
            print(f"DAG {dag_id} 모니터링 중 오류 발생: {e}")
            monitoring_results['monitored_dags'].append({
                'dag_id': dag_id,
                'error': str(e),
                'is_healthy': False
            })
            monitoring_results['unhealthy_dags'] += 1
    
    print(f"모니터링 완료: {monitoring_results['healthy_dags']}/{monitoring_results['total_dags']}개 DAG 건강")
    return monitoring_results

def check_system_resources(**context) -> Dict[str, Any]:
    """
    시스템 리소스 상태를 확인하는 함수
    
    Returns:
        Dict[str, Any]: 리소스 상태 정보
    """
    print("시스템 리소스 확인 중...")
    
    try:
        import psutil
        
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # 네트워크 상태
        network = psutil.net_io_counters()
        
        resource_info = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk_percent,
            'disk_free_gb': disk.free / (1024**3),
            'network_bytes_sent': network.bytes_sent,
            'network_bytes_recv': network.bytes_recv,
            'checked_at': datetime.now().isoformat()
        }
        
        # 리소스 사용률 경고
        warnings = []
        if cpu_percent > 80:
            warnings.append(f"CPU 사용률 높음: {cpu_percent}%")
        if memory_percent > 80:
            warnings.append(f"메모리 사용률 높음: {memory_percent}%")
        if disk_percent > 90:
            warnings.append(f"디스크 사용률 높음: {disk_percent}%")
        
        resource_info['warnings'] = warnings
        
        print(f"시스템 리소스 상태: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%")
        if warnings:
            print(f"경고: {', '.join(warnings)}")
        
        return resource_info
        
    except ImportError:
        print("psutil 모듈이 설치되지 않았습니다. 시스템 리소스 확인을 건너뜁니다.")
        return {
            'error': 'psutil 모듈 없음',
            'checked_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"시스템 리소스 확인 중 오류 발생: {e}")
        return {
            'error': str(e),
            'checked_at': datetime.now().isoformat()
        }

def generate_monitoring_report(**context) -> Dict[str, Any]:
    """
    모니터링 보고서를 생성하는 함수
    
    Returns:
        Dict[str, Any]: 모니터링 보고서
    """
    dag_monitoring = context['task_instance'].xcom_pull(task_ids='monitor_ai_dags')
    resource_info = context['task_instance'].xcom_pull(task_ids='check_system_resources')
    
    print("모니터링 보고서 생성 중...")
    
    # 보고서 생성
    report = {
        'report_id': f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_dags': dag_monitoring['total_dags'],
            'healthy_dags': dag_monitoring['healthy_dags'],
            'unhealthy_dags': dag_monitoring['unhealthy_dags'],
            'health_percentage': (dag_monitoring['healthy_dags'] / dag_monitoring['total_dags'] * 100) if dag_monitoring['total_dags'] > 0 else 0
        },
        'dag_status': dag_monitoring['monitored_dags'],
        'system_resources': resource_info,
        'recommendations': []
    }
    
    # 권장사항 생성
    if dag_monitoring['unhealthy_dags'] > 0:
        report['recommendations'].append("일부 DAG에 문제가 있습니다. 로그를 확인하고 조치하세요.")
    
    if 'warnings' in resource_info and resource_info['warnings']:
        report['recommendations'].extend(resource_info['warnings'])
    
    if report['summary']['health_percentage'] < 50:
        report['recommendations'].append("시스템 전체 상태가 좋지 않습니다. 전체 점검을 권장합니다.")
    
    # 보고서 출력
    print("=" * 60)
    print("AI 팟캐스트 시스템 모니터링 보고서")
    print(f"생성 시간: {report['generated_at']}")
    print(f"DAG 상태: {report['summary']['healthy_dags']}/{report['summary']['total_dags']}개 건강 ({report['summary']['health_percentage']:.1f}%)")
    print(f"시스템 리소스: CPU {resource_info.get('cpu_percent', 'N/A')}%, Memory {resource_info.get('memory_percent', 'N/A')}%")
    
    if report['recommendations']:
        print("권장사항:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    print("=" * 60)
    
    return report

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

monitor_dags_task = PythonOperator(
    task_id='monitor_ai_dags',
    python_callable=monitor_ai_dags,
    dag=dag,
)

check_resources_task = PythonOperator(
    task_id='check_system_resources',
    python_callable=check_system_resources,
    dag=dag,
)

generate_report_task = PythonOperator(
    task_id='generate_monitoring_report',
    python_callable=generate_monitoring_report,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> [monitor_dags_task, check_resources_task] >> generate_report_task >> end_task
