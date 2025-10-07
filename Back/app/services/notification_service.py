"""
알림 및 상태 업데이트를 위한 서비스
"""
import logging
from typing import Optional
from datetime import datetime
from app.websocket.connection_manager import connection_manager
from app.schemas import JobStatusUpdate, JobStatus
from app.services.background_tasks import background_task_manager

logger = logging.getLogger(__name__)

class NotificationService:
    """알림 및 상태 업데이트를 담당하는 서비스"""
    
    @staticmethod
    async def notify_job_status_update(
        job_id: int, 
        status: JobStatus, 
        progress: int = None, 
        message: str = None
    ):
        """
        작업 상태 업데이트를 구독자들에게 알립니다.
        
        Args:
            job_id: 작업 ID
            status: 새로운 상태
            progress: 진행률 (0-100)
            message: 추가 메시지
        """
        try:
            status_update = JobStatusUpdate(
                job_id=job_id,
                status=status,
                progress=progress or 0,
                message=message,
                timestamp=datetime.now()
            )
            
            await connection_manager.broadcast_job_status_update(job_id, status_update)
            logger.info(f"작업 {job_id} 상태 업데이트 알림 전송됨: {status.value}")
            
        except Exception as e:
            logger.error(f"작업 {job_id} 상태 업데이트 알림 전송 실패: {e}")
    
    @staticmethod
    async def notify_job_progress_update(
        job_id: int, 
        progress: int, 
        message: str = None
    ):
        """
        작업 진행률 업데이트를 구독자들에게 알립니다.
        
        Args:
            job_id: 작업 ID
            progress: 진행률 (0-100)
            message: 추가 메시지
        """
        try:
            await connection_manager.broadcast_job_progress_update(job_id, progress, message)
            logger.info(f"작업 {job_id} 진행률 업데이트 알림 전송됨: {progress}%")
            
        except Exception as e:
            logger.error(f"작업 {job_id} 진행률 업데이트 알림 전송 실패: {e}")
    
    @staticmethod
    async def notify_job_started(job_id: int, message: str = "작업이 시작되었습니다"):
        """
        작업 시작을 구독자들에게 알립니다.
        
        Args:
            job_id: 작업 ID
            message: 알림 메시지
        """
        await NotificationService.notify_job_status_update(
            job_id=job_id,
            status=JobStatus.RUNNING,
            progress=0,
            message=message
        )
    
    @staticmethod
    async def notify_job_completed(job_id: int, success: bool = True, message: str = None):
        """
        작업 완료를 구독자들에게 알립니다.
        
        Args:
            job_id: 작업 ID
            success: 성공 여부
            message: 알림 메시지
        """
        status = JobStatus.SUCCESS if success else JobStatus.FAILED
        default_message = "작업이 완료되었습니다" if success else "작업이 실패했습니다"
        
        await NotificationService.notify_job_status_update(
            job_id=job_id,
            status=status,
            progress=100,
            message=message or default_message
        )
    
    @staticmethod
    async def notify_job_cancelled(job_id: int, message: str = "작업이 취소되었습니다"):
        """
        작업 취소를 구독자들에게 알립니다.
        
        Args:
            job_id: 작업 ID
            message: 알림 메시지
        """
        await NotificationService.notify_job_status_update(
            job_id=job_id,
            status=JobStatus.CANCELLED,
            message=message
        )
    
    @staticmethod
    async def start_job_monitoring_with_notifications(job_id: int):
        """
        작업 모니터링을 시작하고 알림을 통합합니다.
        
        Args:
            job_id: 모니터링할 작업 ID
        """
        try:
            # 백그라운드 태스크로 모니터링 시작
            await background_task_manager.start_job_monitoring(job_id)
            
            # 시작 알림 전송
            await NotificationService.notify_job_started(job_id)
            
            logger.info(f"작업 {job_id} 모니터링 및 알림 시작됨")
            
        except Exception as e:
            logger.error(f"작업 {job_id} 모니터링 시작 실패: {e}")
            await NotificationService.notify_job_status_update(
                job_id=job_id,
                status=JobStatus.FAILED,
                message=f"모니터링 시작 실패: {str(e)}"
            )
    
    @staticmethod
    async def stop_job_monitoring_with_notifications(job_id: int):
        """
        작업 모니터링을 중지합니다.
        
        Args:
            job_id: 모니터링을 중지할 작업 ID
        """
        try:
            await background_task_manager.stop_job_monitoring(job_id)
            logger.info(f"작업 {job_id} 모니터링 중지됨")
            
        except Exception as e:
            logger.error(f"작업 {job_id} 모니터링 중지 실패: {e}")

# 전역 인스턴스
notification_service = NotificationService()
