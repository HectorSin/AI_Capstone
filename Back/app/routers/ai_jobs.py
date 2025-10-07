"""
AI 작업 관리를 위한 API 엔드포인트
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas import (
    AIJob, AIJobCreate, AIJobUpdate, JobStatus, JobType,
    AirflowDAGRunRequest, AirflowDAGRunResponse, AirflowTaskInstance
)
from app.services.ai_job_service import AIJobService
from app.services.airflow_service import airflow_service
from app.auth import get_current_user
from app.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=AIJob, summary="AI 작업 생성")
async def create_ai_job(
    job_data: AIJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새로운 AI 작업을 생성합니다.
    """
    try:
        # 사용자 ID 설정
        job_data.user_id = current_user.user_id
        
        # AI 작업 서비스 생성
        job_service = AIJobService(db)
        
        # 작업 생성
        job = await job_service.create_job(job_data)
        
        # 백그라운드에서 작업 시작
        background_tasks.add_task(job_service.start_job, job.job_id)
        
        logger.info(f"AI 작업 생성됨: {job.job_id} by user {current_user.user_id}")
        return job
        
    except Exception as e:
        logger.error(f"AI 작업 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=AIJob, summary="AI 작업 조회")
async def get_ai_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 AI 작업의 상세 정보를 조회합니다.
    """
    try:
        job_service = AIJobService(db)
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        # 사용자 권한 확인
        if job.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 작업 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[AIJob], summary="AI 작업 목록 조회")
async def get_ai_jobs(
    status: Optional[JobStatus] = Query(None, description="상태 필터"),
    job_type: Optional[JobType] = Query(None, description="작업 타입 필터"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수 제한"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 AI 작업 목록을 조회합니다.
    """
    try:
        job_service = AIJobService(db)
        jobs = await job_service.get_user_jobs(
            user_id=current_user.user_id,
            status=status,
            job_type=job_type,
            limit=limit,
            offset=offset
        )
        
        return jobs
        
    except Exception as e:
        logger.error(f"AI 작업 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{job_id}", response_model=AIJob, summary="AI 작업 상태 업데이트")
async def update_ai_job(
    job_id: int,
    job_update: AIJobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 작업의 상태를 업데이트합니다.
    """
    try:
        job_service = AIJobService(db)
        
        # 작업 존재 및 권한 확인
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        if job.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 상태 업데이트
        updated_job = await job_service.update_job_status(
            job_id=job_id,
            status=job_update.status,
            progress=job_update.progress,
            result_data=job_update.result_data,
            error_message=job_update.error_message
        )
        
        return updated_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 작업 상태 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/cancel", summary="AI 작업 취소")
async def cancel_ai_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 작업을 취소합니다.
    """
    try:
        job_service = AIJobService(db)
        
        # 작업 존재 및 권한 확인
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        if job.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 작업 취소
        success = await job_service.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="작업을 취소할 수 없습니다")
        
        return {"message": "작업이 취소되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 작업 취소 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}/logs", summary="AI 작업 로그 조회")
async def get_ai_job_logs(
    job_id: int,
    limit: int = Query(100, ge=1, le=1000, description="조회 개수 제한"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 작업의 로그를 조회합니다.
    """
    try:
        job_service = AIJobService(db)
        
        # 작업 존재 및 권한 확인
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        if job.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 로그 조회
        logs = await job_service.get_job_logs(job_id, limit)
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 작업 로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/airflow/dag-run", response_model=AirflowDAGRunResponse, summary="Airflow DAG 실행")
async def trigger_airflow_dag(
    dag_request: AirflowDAGRunRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Airflow DAG를 직접 실행합니다.
    """
    try:
        # DAG 실행
        dag_run_id = await airflow_service.trigger_dag_run(
            dag_id=dag_request.dag_id,
            conf=dag_request.conf,
            execution_date=dag_request.execution_date
        )
        
        # DAG Run 정보 조회
        dag_run_info = await airflow_service.get_dag_run_status(
            dag_id=dag_request.dag_id,
            dag_run_id=dag_run_id
        )
        
        return AirflowDAGRunResponse(
            dag_run_id=dag_run_info["dag_run_id"],
            state=dag_run_info["state"],
            execution_date=dag_run_info["execution_date"],
            start_date=dag_run_info["start_date"],
            end_date=dag_run_info["end_date"]
        )
        
    except Exception as e:
        logger.error(f"Airflow DAG 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airflow/dag-run/{dag_id}/{dag_run_id}", summary="Airflow DAG Run 상태 조회")
async def get_airflow_dag_run_status(
    dag_id: str,
    dag_run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Airflow DAG Run의 상태를 조회합니다.
    """
    try:
        dag_run_info = await airflow_service.get_dag_run_status(dag_id, dag_run_id)
        return dag_run_info
        
    except Exception as e:
        logger.error(f"Airflow DAG Run 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airflow/dag-run/{dag_id}/{dag_run_id}/tasks", response_model=List[AirflowTaskInstance], summary="Airflow Task Instances 조회")
async def get_airflow_task_instances(
    dag_id: str,
    dag_run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Airflow DAG Run의 Task Instances를 조회합니다.
    """
    try:
        task_instances = await airflow_service.get_task_instances(dag_id, dag_run_id)
        
        return [
            AirflowTaskInstance(
                task_id=task["task_id"],
                state=task["state"],
                start_date=task["start_date"],
                end_date=task["end_date"],
                duration=task["duration"],
                log_url=task["log_url"]
            )
            for task in task_instances
        ]
        
    except Exception as e:
        logger.error(f"Airflow Task Instances 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airflow/dags", summary="사용 가능한 DAG 목록 조회")
async def list_airflow_dags(
    current_user: User = Depends(get_current_user)
):
    """
    사용 가능한 Airflow DAG 목록을 조회합니다.
    """
    try:
        dags = await airflow_service.list_dags()
        return {"dags": dags}
        
    except Exception as e:
        logger.error(f"Airflow DAG 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
