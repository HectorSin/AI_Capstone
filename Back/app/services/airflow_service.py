"""
Airflow API 연동을 위한 서비스 클래스
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from airflow_client.client.api import dag_api, dag_run_api, task_instance_api
from airflow_client.client.model.dag_run import DAGRun
from airflow_client.client.model.basic_dag_run import BasicDAGRun
from airflow_client.client.model.task_instance import TaskInstance
from airflow_client.client import ApiClient, Configuration
from airflow_client.client.exceptions import ApiException
from app.config import settings

logger = logging.getLogger(__name__)

class AirflowService:
    """Airflow API와의 연동을 담당하는 서비스 클래스"""
    
    def __init__(self):
        self.config = Configuration(
            host=settings.airflow_host,
            username=settings.airflow_username,
            password=settings.airflow_password
        )
        self.api_client = ApiClient(self.config)
        self.dag_api = dag_api.DAGApi(self.api_client)
        self.dag_run_api = dag_run_api.DAGRunApi(self.api_client)
        self.task_instance_api = task_instance_api.TaskInstanceApi(self.api_client)
    
    async def trigger_dag_run(
        self, 
        dag_id: str, 
        conf: Optional[Dict[str, Any]] = None,
        execution_date: Optional[datetime] = None
    ) -> str:
        """
        DAG 실행을 트리거하고 DAG Run ID를 반환
        
        Args:
            dag_id: 실행할 DAG의 ID
            conf: DAG 실행 시 전달할 설정 데이터
            execution_date: 실행 날짜 (기본값: 현재 시간)
            
        Returns:
            str: DAG Run ID
            
        Raises:
            ApiException: Airflow API 호출 실패 시
        """
        try:
            if execution_date is None:
                execution_date = datetime.now()
            
            dag_run_request = BasicDAGRun(
                conf=conf or {},
                execution_date=execution_date
            )
            
            response = self.dag_run_api.post_dag_run(
                dag_id=dag_id,
                dag_run_request=dag_run_request
            )
            
            logger.info(f"DAG {dag_id} 실행 트리거됨. DAG Run ID: {response.dag_run_id}")
            return response.dag_run_id
            
        except ApiException as e:
            logger.error(f"DAG {dag_id} 실행 실패: {e}")
            raise
    
    async def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> Dict[str, Any]:
        """
        DAG Run의 상태를 조회
        
        Args:
            dag_id: DAG ID
            dag_run_id: DAG Run ID
            
        Returns:
            Dict[str, Any]: DAG Run 상태 정보
        """
        try:
            dag_run = self.dag_run_api.get_dag_run(
                dag_id=dag_id,
                dag_run_id=dag_run_id
            )
            
            return {
                "dag_run_id": dag_run.dag_run_id,
                "state": dag_run.state,
                "execution_date": dag_run.execution_date,
                "start_date": dag_run.start_date,
                "end_date": dag_run.end_date,
                "conf": dag_run.conf
            }
            
        except ApiException as e:
            logger.error(f"DAG Run {dag_run_id} 상태 조회 실패: {e}")
            raise
    
    async def get_task_instances(
        self, 
        dag_id: str, 
        dag_run_id: str
    ) -> List[Dict[str, Any]]:
        """
        DAG Run의 모든 Task Instance 상태를 조회
        
        Args:
            dag_id: DAG ID
            dag_run_id: DAG Run ID
            
        Returns:
            List[Dict[str, Any]]: Task Instance 목록
        """
        try:
            task_instances = self.task_instance_api.get_task_instances(
                dag_id=dag_id,
                dag_run_id=dag_run_id
            )
            
            result = []
            for task in task_instances.task_instances:
                result.append({
                    "task_id": task.task_id,
                    "state": task.state,
                    "start_date": task.start_date,
                    "end_date": task.end_date,
                    "duration": task.duration,
                    "log_url": f"{settings.airflow_host}/log?dag_id={dag_id}&task_id={task.task_id}&execution_date={task.execution_date}"
                })
            
            return result
            
        except ApiException as e:
            logger.error(f"Task Instances 조회 실패: {e}")
            raise
    
    async def get_task_logs(
        self, 
        dag_id: str, 
        task_id: str, 
        dag_run_id: str,
        limit: int = 100
    ) -> str:
        """
        특정 Task의 로그를 조회
        
        Args:
            dag_id: DAG ID
            task_id: Task ID
            dag_run_id: DAG Run ID
            limit: 조회할 로그 라인 수
            
        Returns:
            str: Task 로그
        """
        try:
            logs = self.task_instance_api.get_task_instance_logs(
                dag_id=dag_id,
                task_id=task_id,
                dag_run_id=dag_run_id,
                limit=limit
            )
            
            return logs.content if hasattr(logs, 'content') else str(logs)
            
        except ApiException as e:
            logger.error(f"Task {task_id} 로그 조회 실패: {e}")
            raise
    
    async def cancel_dag_run(self, dag_id: str, dag_run_id: str) -> bool:
        """
        DAG Run을 취소
        
        Args:
            dag_id: DAG ID
            dag_run_id: DAG Run ID
            
        Returns:
            bool: 취소 성공 여부
        """
        try:
            self.dag_run_api.delete_dag_run(
                dag_id=dag_id,
                dag_run_id=dag_run_id
            )
            
            logger.info(f"DAG Run {dag_run_id} 취소됨")
            return True
            
        except ApiException as e:
            logger.error(f"DAG Run {dag_run_id} 취소 실패: {e}")
            return False
    
    async def get_dag_info(self, dag_id: str) -> Dict[str, Any]:
        """
        DAG 정보를 조회
        
        Args:
            dag_id: DAG ID
            
        Returns:
            Dict[str, Any]: DAG 정보
        """
        try:
            dag = self.dag_api.get_dag(dag_id=dag_id)
            
            return {
                "dag_id": dag.dag_id,
                "description": dag.description,
                "is_paused": dag.is_paused,
                "is_subdag": dag.is_subdag,
                "fileloc": dag.fileloc,
                "owners": dag.owners,
                "tags": dag.tags,
                "timetable_description": dag.timetable_description
            }
            
        except ApiException as e:
            logger.error(f"DAG {dag_id} 정보 조회 실패: {e}")
            raise
    
    async def list_dags(self) -> List[str]:
        """
        사용 가능한 DAG 목록을 조회
        
        Returns:
            List[str]: DAG ID 목록
        """
        try:
            dags = self.dag_api.get_dags()
            
            return [dag.dag_id for dag in dags.dags]
            
        except ApiException as e:
            logger.error(f"DAG 목록 조회 실패: {e}")
            raise

# 전역 인스턴스
airflow_service = AirflowService()
