"""
비동기 작업 처리를 위한 백그라운드 태스크
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import AsyncSessionLocal
from app.services.airflow_service import airflow_service
from app.schemas import JobStatus, JobType
from app.config import settings

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """백그라운드 태스크 관리자"""
    
    def __init__(self):
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.task_interval = 30  # 30초마다 상태 체크
    
    async def start_job_monitoring(self, job_id: int):
        """
        AI 작업 모니터링을 시작합니다.
        
        Args:
            job_id: 모니터링할 작업 ID
        """
        if job_id in self.running_tasks:
            logger.warning(f"작업 {job_id}는 이미 모니터링 중입니다")
            return
        
        task = asyncio.create_task(self._monitor_job(job_id))
        self.running_tasks[job_id] = task
        
        logger.info(f"작업 {job_id} 모니터링 시작됨")
    
    async def stop_job_monitoring(self, job_id: int):
        """
        AI 작업 모니터링을 중지합니다.
        
        Args:
            job_id: 모니터링을 중지할 작업 ID
        """
        if job_id in self.running_tasks:
            task = self.running_tasks[job_id]
            task.cancel()
            del self.running_tasks[job_id]
            logger.info(f"작업 {job_id} 모니터링 중지됨")
    
    async def _monitor_job(self, job_id: int):
        """
        특정 작업의 상태를 모니터링합니다.
        
        Args:
            job_id: 모니터링할 작업 ID
        """
        async with AsyncSessionLocal() as db:
            from app.services.ai_job_service import AIJobService
            job_service = AIJobService(db)
            
            while True:
                try:
                    # 작업 상태 조회
                    job = await job_service.get_job(job_id)
                    if not job:
                        logger.error(f"작업 {job_id}를 찾을 수 없습니다")
                        break
                    
                    # 완료된 작업은 모니터링 중지
                    if job.status.value in ['success', 'failed', 'cancelled']:
                        logger.info(f"작업 {job_id} 완료됨: {job.status.value}")
                        break
                    
                    # Airflow DAG Run 상태 확인
                    if job.airflow_dag_run_id:
                        await self._check_airflow_status(job_service, job)
                    
                    # 다음 체크까지 대기
                    await asyncio.sleep(self.task_interval)
                    
                except asyncio.CancelledError:
                    logger.info(f"작업 {job_id} 모니터링이 취소되었습니다")
                    break
                except Exception as e:
                    logger.error(f"작업 {job_id} 모니터링 중 오류: {e}")
                    await asyncio.sleep(self.task_interval)
            
            if job_id in self.running_tasks:
                del self.running_tasks[job_id]
    
    async def _check_airflow_status(self, job_service, job):
        """
        Airflow DAG Run 상태를 확인하고 작업 상태를 업데이트합니다.
        
        Args:
            job_service: AI 작업 서비스
            job: AI 작업 객체
        """
        try:
            # DAG ID 결정
            dag_id = self._get_dag_id_for_job_type(job.job_type)
            
            # Airflow DAG Run 상태 조회
            dag_run_info = await airflow_service.get_dag_run_status(
                dag_id=dag_id,
                dag_run_id=job.airflow_dag_run_id
            )
            
            # Task Instances 조회
            task_instances = await airflow_service.get_task_instances(
                dag_id=dag_id,
                dag_run_id=job.airflow_dag_run_id
            )
            
            # 진행률 계산
            total_tasks = len(task_instances)
            completed_tasks = sum(1 for task in task_instances 
                                if task['state'] in ['success', 'failed', 'upstream_failed'])
            progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
            
            # 상태 매핑
            airflow_state = dag_run_info['state']
            job_status = self._map_airflow_state_to_job_status(airflow_state)
            
            # 작업 상태 업데이트
            if job_status != job.status:
                await job_service.update_job_status(
                    job_id=job.job_id,
                    status=job_status,
                    progress=progress
                )
                
                # 완료된 경우 결과 데이터 저장
                if job_status in [JobStatus.SUCCESS, JobStatus.FAILED]:
                    result_data = {
                        'airflow_dag_run_id': job.airflow_dag_run_id,
                        'dag_run_state': airflow_state,
                        'task_instances': task_instances,
                        'completed_at': datetime.now().isoformat()
                    }
                    
                    await job_service.update_job_status(
                        job_id=job.job_id,
                        status=job_status,
                        result_data=result_data
                    )
            
            # 진행률만 업데이트
            elif progress != job.progress:
                await job_service.update_job_status(
                    job_id=job.job_id,
                    progress=progress
                )
                
        except Exception as e:
            logger.error(f"Airflow 상태 확인 실패 (작업 {job.job_id}): {e}")
    
    def _get_dag_id_for_job_type(self, job_type: JobType) -> str:
        """
        작업 타입에 따른 DAG ID를 반환합니다.
        
        Args:
            job_type: 작업 타입
            
        Returns:
            str: DAG ID
        """
        dag_mapping = {
            JobType.URL_ANALYSIS: "url_analysis_dag",
            JobType.TOPIC_GENERATION: "topic_generation_dag",
            JobType.SCRIPT_GENERATION: "script_generation_dag",
            JobType.AUDIO_GENERATION: "audio_generation_dag",
            JobType.FULL_PIPELINE: "full_pipeline_dag"
        }
        
        return dag_mapping.get(job_type, "default_dag")
    
    def _map_airflow_state_to_job_status(self, airflow_state: str) -> JobStatus:
        """
        Airflow 상태를 AI 작업 상태로 매핑합니다.
        
        Args:
            airflow_state: Airflow DAG Run 상태
            
        Returns:
            JobStatus: AI 작업 상태
        """
        state_mapping = {
            'queued': JobStatus.PENDING,
            'running': JobStatus.RUNNING,
            'success': JobStatus.SUCCESS,
            'failed': JobStatus.FAILED,
            'upstream_failed': JobStatus.FAILED,
            'skipped': JobStatus.CANCELLED,
            'up_for_retry': JobStatus.RUNNING,
            'up_for_reschedule': JobStatus.RUNNING,
            'deferred': JobStatus.PENDING,
            'sensing': JobStatus.RUNNING,
            'restarting': JobStatus.RUNNING
        }
        
        return state_mapping.get(airflow_state, JobStatus.PENDING)

class JobStatusUpdater:
    """작업 상태 업데이트를 위한 유틸리티 클래스"""
    
    @staticmethod
    async def update_job_from_airflow(job_id: int, airflow_data: Dict[str, Any]):
        """
        Airflow 데이터를 기반으로 작업 상태를 업데이트합니다.
        
        Args:
            job_id: 작업 ID
            airflow_data: Airflow에서 받은 데이터
        """
        async with AsyncSessionLocal() as db:
            from app.services.ai_job_service import AIJobService
            job_service = AIJobService(db)
            
            # 작업 조회
            job = await job_service.get_job(job_id)
            if not job:
                logger.error(f"작업 {job_id}를 찾을 수 없습니다")
                return
            
            # 상태 업데이트
            if 'status' in airflow_data:
                await job_service.update_job_status(
                    job_id=job_id,
                    status=JobStatus(airflow_data['status']),
                    progress=airflow_data.get('progress', job.progress),
                    result_data=airflow_data.get('result_data')
                )

# 전역 인스턴스
background_task_manager = BackgroundTaskManager()
job_status_updater = JobStatusUpdater()
