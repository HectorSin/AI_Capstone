"""
AI 작업 관리를 위한 서비스 클래스
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.database.models import AIJob, JobLog, JobStatusEnum, JobTypeEnum
from app.schemas import AIJobCreate, AIJobUpdate, JobStatus, JobType
from app.config import settings
from app.utils.internal_runner import run_ai_job_internal
from app.services.notification_service import notification_service
from app.config import settings

logger = logging.getLogger(__name__)

class AIJobService:
    """AI 작업 관리를 담당하는 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_job(self, job_data: AIJobCreate) -> AIJob:
        """
        새로운 AI 작업을 생성
        
        Args:
            job_data: 작업 생성 데이터
            
        Returns:
            AIJob: 생성된 작업 객체
        """
        try:
            # 데이터베이스에 작업 생성
            db_job = AIJob(
                job_type=JobTypeEnum(job_data.job_type.value),
                user_id=job_data.user_id,
                topic_id=job_data.topic_id,
                input_data=job_data.input_data,
                priority=job_data.priority,
                status=JobStatusEnum.PENDING
            )
            
            self.db.add(db_job)
            # AsyncSession 사용: commit/refresh는 await 필요
            commit = getattr(self.db, "commit", None)
            refresh = getattr(self.db, "refresh", None)
            if commit and callable(commit):
                try:
                    await commit()
                except TypeError:
                    self.db.commit()
            else:
                self.db.commit()
            if refresh and callable(refresh):
                try:
                    await refresh(db_job)
                except TypeError:
                    self.db.refresh(db_job)
            else:
                self.db.refresh(db_job)

            # 생성 직후 None 값이 남아 응답 검증에 실패하는 경우를 방지
            # (DB default가 반영되지 않은 드문 케이스 대비)
            if db_job.progress is None:
                db_job.progress = 0
            if db_job.created_at is None:
                db_job.created_at = datetime.now()
            if db_job.updated_at is None:
                db_job.updated_at = datetime.now()
            # 보정값 커밋
            if commit and callable(commit):
                try:
                    await commit()
                except TypeError:
                    self.db.commit()
            else:
                self.db.commit()
            if refresh and callable(refresh):
                try:
                    await refresh(db_job)
                except TypeError:
                    self.db.refresh(db_job)
            else:
                self.db.refresh(db_job)
            
            # 로그 기록
            await self._log_job_event(
                db_job.job_id, 
                "INFO", 
                f"작업 생성됨: {job_data.job_type.value}"
            )
            
            logger.info(f"AI 작업 생성됨: {db_job.job_id}")
            return db_job
            
        except Exception as e:
            rollback = getattr(self.db, "rollback", None)
            if rollback and callable(rollback):
                try:
                    await rollback()
                except TypeError:
                    self.db.rollback()
            else:
                self.db.rollback()
            logger.error(f"AI 작업 생성 실패: {e}")
            raise
    
    async def start_job(self, job_id: int) -> Optional[AIJob]:
        """
        AI 작업을 시작하고 Airflow DAG를 실행
        
        Args:
            job_id: 작업 ID
            
        Returns:
            Optional[AIJob]: 업데이트된 작업 객체
        """
        try:
            # 작업 조회
            db_job = self.db.query(AIJob).filter(AIJob.job_id == job_id).first()
            if not db_job:
                raise ValueError(f"작업을 찾을 수 없습니다: {job_id}")
            
            if db_job.status != JobStatusEnum.PENDING:
                raise ValueError(f"작업이 이미 시작되었거나 완료되었습니다: {db_job.status}")
            
            # 내부 실행 (Airflow 미사용)
            run_ai_job_internal(
                job_id=db_job.job_id,
                job_type=db_job.job_type.value,
                input_data=db_job.input_data,
            )
            
            # 작업 상태 업데이트
            db_job.status = JobStatusEnum.RUNNING
            db_job.started_at = datetime.now()
            # Airflow 미사용 경로에서는 dag_run_id 없음
            db_job.updated_at = datetime.now()
            
            commit = getattr(self.db, "commit", None)
            refresh = getattr(self.db, "refresh", None)
            if commit and callable(commit):
                try:
                    await commit()
                except TypeError:
                    self.db.commit()
            else:
                self.db.commit()
            if refresh and callable(refresh):
                try:
                    await refresh(db_job)
                except TypeError:
                    self.db.refresh(db_job)
            else:
                self.db.refresh(db_job)
            
            # 로그 기록
            await self._log_job_event(
                job_id, 
                "INFO", 
                "작업 시작됨"
            )
            
            # 알림 전송
            await notification_service.notify_job_started(job_id, "작업이 시작되었습니다")
            
            # 모니터링 시작
            await notification_service.start_job_monitoring_with_notifications(job_id)
            
            logger.info(f"AI 작업 시작됨: {job_id}")
            return db_job
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"AI 작업 시작 실패: {e}")
            raise
    
    async def update_job_status(
        self, 
        job_id: int, 
        status: JobStatus, 
        progress: Optional[int] = None,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[AIJob]:
        """
        AI 작업 상태를 업데이트
        
        Args:
            job_id: 작업 ID
            status: 새로운 상태
            progress: 진행률 (0-100)
            result_data: 결과 데이터
            error_message: 에러 메시지
            
        Returns:
            Optional[AIJob]: 업데이트된 작업 객체
        """
        try:
            db_job = self.db.query(AIJob).filter(AIJob.job_id == job_id).first()
            if not db_job:
                return None
            
            # 상태 업데이트
            old_status = db_job.status
            db_job.status = JobStatusEnum(status.value)
            db_job.updated_at = datetime.now()
            
            if progress is not None:
                db_job.progress = progress
            
            if result_data is not None:
                db_job.result_data = result_data
            
            if error_message is not None:
                db_job.error_message = error_message
            
            # 완료 시간 설정
            if status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
                db_job.completed_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(db_job)
            
            # 로그 기록
            await self._log_job_event(
                job_id, 
                "INFO", 
                f"상태 변경: {old_status.value} -> {status.value}"
            )
            
            # 알림 전송
            await notification_service.notify_job_status_update(
                job_id=job_id,
                status=status,
                progress=progress,
                message=f"상태 변경: {old_status.value} -> {status.value}"
            )
            
            # 완료된 경우 모니터링 중지
            if status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
                await notification_service.stop_job_monitoring_with_notifications(job_id)
                
                # 완료 알림 전송
                success = status == JobStatus.SUCCESS
                await notification_service.notify_job_completed(job_id, success)
            
            logger.info(f"AI 작업 상태 업데이트됨: {job_id} -> {status.value}")
            return db_job
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"AI 작업 상태 업데이트 실패: {e}")
            raise
    
    async def get_job(self, job_id: int) -> Optional[AIJob]:
        """
        AI 작업을 조회
        
        Args:
            job_id: 작업 ID
            
        Returns:
            Optional[AIJob]: 작업 객체
        """
        return self.db.query(AIJob).filter(AIJob.job_id == job_id).first()
    
    async def get_user_jobs(
        self, 
        user_id: int, 
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AIJob]:
        """
        사용자의 AI 작업 목록을 조회
        
        Args:
            user_id: 사용자 ID
            status: 상태 필터
            job_type: 작업 타입 필터
            limit: 조회 개수 제한
            offset: 오프셋
            
        Returns:
            List[AIJob]: 작업 목록
        """
        query = self.db.query(AIJob).filter(AIJob.user_id == user_id)
        
        if status:
            query = query.filter(AIJob.status == JobStatusEnum(status.value))
        
        if job_type:
            query = query.filter(AIJob.job_type == JobTypeEnum(job_type.value))
        
        return query.order_by(desc(AIJob.created_at)).offset(offset).limit(limit).all()
    
    async def cancel_job(self, job_id: int) -> bool:
        """
        AI 작업을 취소
        
        Args:
            job_id: 작업 ID
            
        Returns:
            bool: 취소 성공 여부
        """
        try:
            db_job = self.db.query(AIJob).filter(AIJob.job_id == job_id).first()
            if not db_job:
                return False
            
            if db_job.status in [JobStatusEnum.SUCCESS, JobStatusEnum.FAILED, JobStatusEnum.CANCELLED]:
                return False
            
            # Airflow 미사용: 외부 DAG 취소 로직 제거
            
            # 작업 상태 업데이트
            db_job.status = JobStatusEnum.CANCELLED
            db_job.completed_at = datetime.now()
            db_job.updated_at = datetime.now()
            
            self.db.commit()
            
            # 로그 기록
            await self._log_job_event(job_id, "INFO", "작업 취소됨")
            
            # 모니터링 중지
            await notification_service.stop_job_monitoring_with_notifications(job_id)
            
            # 취소 알림 전송
            await notification_service.notify_job_cancelled(job_id)
            
            logger.info(f"AI 작업 취소됨: {job_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"AI 작업 취소 실패: {e}")
            return False
    
    async def get_job_logs(self, job_id: int, limit: int = 100) -> List[JobLog]:
        """
        AI 작업의 로그를 조회
        
        Args:
            job_id: 작업 ID
            limit: 조회 개수 제한
            
        Returns:
            List[JobLog]: 로그 목록
        """
        return (
            self.db.query(JobLog)
            .filter(JobLog.job_id == job_id)
            .order_by(desc(JobLog.created_at))
            .limit(limit)
            .all()
        )
    
    async def _log_job_event(
        self, 
        job_id: int, 
        level: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        작업 이벤트를 로그에 기록
        
        Args:
            job_id: 작업 ID
            level: 로그 레벨
            message: 로그 메시지
            details: 추가 세부사항
        """
        try:
            log_entry = JobLog(
                job_id=job_id,
                level=level,
                message=message,
                details=details
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"작업 로그 기록 실패: {e}")
    
    def _get_dag_id_for_job_type(self, job_type: JobTypeEnum) -> str:
        """
        작업 타입에 따른 DAG ID를 반환
        
        Args:
            job_type: 작업 타입
            
        Returns:
            str: DAG ID
        """
        dag_mapping = {
            JobTypeEnum.URL_ANALYSIS: "url_analysis_dag",
            JobTypeEnum.TOPIC_GENERATION: "topic_generation_dag",
            JobTypeEnum.SCRIPT_GENERATION: "script_generation_dag",
            JobTypeEnum.AUDIO_GENERATION: "audio_generation_dag",
            JobTypeEnum.FULL_PIPELINE: "full_pipeline_dag"
        }
        
        return dag_mapping.get(job_type, "default_dag")
