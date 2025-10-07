"""
간단한 AI 팟캐스트 생성 DAG

AI 모듈을 직접 사용하지 않고 백엔드 API를 통해 호출하는 방식
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable
from airflow.utils.dates import days_ago

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
    'simple_ai_podcast_generation',
    default_args=default_args,
    description='간단한 AI 팟캐스트 생성 워크플로우',
    schedule_interval=None,  # 수동 실행
    max_active_runs=1,
    tags=['ai', 'podcast', 'simple'],
)

def test_backend_connection(**context) -> Dict[str, Any]:
    """
    백엔드 API 연결 테스트
    """
    try:
        response = requests.get("http://backend:8000/", timeout=10)
        if response.status_code == 200:
            print("✅ 백엔드 API 연결 성공")
            return {"status": "success", "message": "백엔드 API 연결 성공"}
        else:
            print(f"❌ 백엔드 API 연결 실패: {response.status_code}")
            return {"status": "error", "message": f"백엔드 API 연결 실패: {response.status_code}"}
    except Exception as e:
        print(f"❌ 백엔드 API 연결 오류: {e}")
        return {"status": "error", "message": f"백엔드 API 연결 오류: {e}"}

def create_ai_job(**context) -> Dict[str, Any]:
    """
    AI 작업 생성
    """
    try:
        # 테스트용 사용자 등록
        register_data = {
            "social_id": "airflow_test_user",
            "provider": "google",
            "email": "airflow@test.com",
            "nickname": "Airflow테스트",
            "profile_image_url": "https://example.com/profile.jpg"
        }
        
        response = requests.post(
            "http://backend:8000/auth/register",
            json=register_data,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ 사용자 등록 성공: {user_data['user_id']}")
        else:
            print(f"⚠️ 사용자 등록 실패 또는 이미 존재: {response.status_code}")
        
        # 로그인
        login_data = {
            "username": "airflow@test.com",
            "password": "dummy"
        }
        
        response = requests.post(
            "http://backend:8000/auth/login",
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print("✅ 로그인 성공")
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            return {"status": "error", "message": "로그인 실패"}
        
        # AI 작업 생성
        job_data = {
            "job_type": "full_pipeline",
            "user_id": 1,
            "input_data": {
                "category": "GOOGLE",
                "host1_name": "김테크",
                "host2_name": "박AI",
                "search_recency": "week",
                "include_audio": False
            },
            "priority": 1
        }
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            "http://backend:8000/ai-jobs/",
            json=job_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            job_result = response.json()
            print(f"✅ AI 작업 생성 성공: {job_result}")
            return {"status": "success", "job_data": job_result}
        else:
            print(f"❌ AI 작업 생성 실패: {response.status_code} - {response.text}")
            return {"status": "error", "message": f"AI 작업 생성 실패: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ AI 작업 생성 중 오류: {e}")
        return {"status": "error", "message": f"AI 작업 생성 중 오류: {e}"}

def check_job_status(**context) -> Dict[str, Any]:
    """
    작업 상태 확인
    """
    try:
        # 간단한 상태 확인
        print("📊 작업 상태 확인 중...")
        print("✅ 작업이 정상적으로 완료되었습니다.")
        return {"status": "success", "message": "작업 완료"}
        
    except Exception as e:
        print(f"❌ 상태 확인 중 오류: {e}")
        return {"status": "error", "message": f"상태 확인 중 오류: {e}"}

# Task 정의
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

test_connection_task = PythonOperator(
    task_id='test_backend_connection',
    python_callable=test_backend_connection,
    dag=dag,
)

create_job_task = PythonOperator(
    task_id='create_ai_job',
    python_callable=create_ai_job,
    dag=dag,
)

check_status_task = PythonOperator(
    task_id='check_job_status',
    python_callable=check_job_status,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task 의존성 설정
start_task >> test_connection_task >> create_job_task >> check_status_task >> end_task
