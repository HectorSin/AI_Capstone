"""
WebSocket 엔드포인트
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.websocket.connection_manager import connection_manager
from app.schemas import WebSocketMessage, JobStatusUpdate, JobStatus
from app.database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket 연결을 처리하는 엔드포인트
    
    Args:
        websocket: WebSocket 연결 객체
        user_id: 사용자 ID
    """
    await connection_manager.connect(websocket, user_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                await handle_websocket_message(websocket, user_id, message_data)
            except json.JSONDecodeError:
                await send_error_message(websocket, "Invalid JSON format")
            except Exception as e:
                logger.error(f"WebSocket 메시지 처리 오류: {e}")
                await send_error_message(websocket, f"Message processing error: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info(f"사용자 {user_id} WebSocket 연결 해제됨")
    except Exception as e:
        logger.error(f"WebSocket 연결 오류: {e}")
    finally:
        connection_manager.disconnect(websocket, user_id)

async def handle_websocket_message(websocket: WebSocket, user_id: int, message_data: Dict[str, Any]):
    """
    WebSocket 메시지를 처리합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        user_id: 사용자 ID
        message_data: 메시지 데이터
    """
    message_type = message_data.get("type")
    
    if message_type == "subscribe_job":
        await handle_subscribe_job(websocket, user_id, message_data)
    elif message_type == "unsubscribe_job":
        await handle_unsubscribe_job(websocket, user_id, message_data)
    elif message_type == "get_job_status":
        await handle_get_job_status(websocket, user_id, message_data)
    elif message_type == "ping":
        await handle_ping(websocket, user_id)
    else:
        await send_error_message(websocket, f"Unknown message type: {message_type}")

async def handle_subscribe_job(websocket: WebSocket, user_id: int, message_data: Dict[str, Any]):
    """
    작업 구독 요청을 처리합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        user_id: 사용자 ID
        message_data: 메시지 데이터
    """
    job_id = message_data.get("job_id")
    
    if not job_id:
        await send_error_message(websocket, "job_id is required")
        return
    
    try:
        job_id = int(job_id)
    except ValueError:
        await send_error_message(websocket, "Invalid job_id format")
        return
    
    # 작업 존재 및 권한 확인
    async with AsyncSessionLocal() as db:
        from app.services.ai_job_service import AIJobService
        job_service = AIJobService(db)
        job = await job_service.get_job(job_id)
        
        if not job:
            await send_error_message(websocket, f"Job {job_id} not found")
            return
        
        if job.user_id != user_id:
            await send_error_message(websocket, "Access denied")
            return
        
        # 구독 등록
        connection_manager.subscribe_job(websocket, job_id, user_id)
        
        # 구독 확인 메시지 전송
        response = WebSocketMessage(
            type="subscription_confirmed",
            job_id=job_id,
            data={"message": f"Subscribed to job {job_id}"},
            timestamp=datetime.now()
        )
        
        await websocket.send_text(response.model_dump_json())
        
        logger.info(f"사용자 {user_id}이 작업 {job_id} 구독함")

async def handle_unsubscribe_job(websocket: WebSocket, user_id: int, message_data: Dict[str, Any]):
    """
    작업 구독 해제 요청을 처리합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        user_id: 사용자 ID
        message_data: 메시지 데이터
    """
    job_id = message_data.get("job_id")
    
    if not job_id:
        await send_error_message(websocket, "job_id is required")
        return
    
    try:
        job_id = int(job_id)
    except ValueError:
        await send_error_message(websocket, "Invalid job_id format")
        return
    
    # 구독 해제
    connection_manager.unsubscribe_job(websocket, job_id)
    
    # 해제 확인 메시지 전송
    response = WebSocketMessage(
        type="unsubscription_confirmed",
        job_id=job_id,
        data={"message": f"Unsubscribed from job {job_id}"},
        timestamp=datetime.now()
    )
    
    await websocket.send_text(response.model_dump_json())
    
    logger.info(f"사용자 {user_id}이 작업 {job_id} 구독 해제함")

async def handle_get_job_status(websocket: WebSocket, user_id: int, message_data: Dict[str, Any]):
    """
    작업 상태 조회 요청을 처리합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        user_id: 사용자 ID
        message_data: 메시지 데이터
    """
    job_id = message_data.get("job_id")
    
    if not job_id:
        await send_error_message(websocket, "job_id is required")
        return
    
    try:
        job_id = int(job_id)
    except ValueError:
        await send_error_message(websocket, "Invalid job_id format")
        return
    
    async with AsyncSessionLocal() as db:
        from app.services.ai_job_service import AIJobService
        job_service = AIJobService(db)
        job = await job_service.get_job(job_id)
        
        if not job:
            await send_error_message(websocket, f"Job {job_id} not found")
            return
        
        if job.user_id != user_id:
            await send_error_message(websocket, "Access denied")
            return
        
        # 작업 상태 전송
        status_update = JobStatusUpdate(
            job_id=job.job_id,
            status=JobStatus(job.status.value),
            progress=job.progress,
            message=f"Current status: {job.status.value}",
            timestamp=datetime.now()
        )
        
        response = WebSocketMessage(
            type="job_status",
            job_id=job_id,
            data=status_update.model_dump(),
            timestamp=datetime.now()
        )
        
        await websocket.send_text(response.model_dump_json())

async def handle_ping(websocket: WebSocket, user_id: int):
    """
    Ping 요청을 처리합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        user_id: 사용자 ID
    """
    response = WebSocketMessage(
        type="pong",
        job_id=0,
        data={"message": "pong", "user_id": user_id},
        timestamp=datetime.now()
    )
    
    await websocket.send_text(response.model_dump_json())

async def send_error_message(websocket: WebSocket, error_message: str):
    """
    에러 메시지를 전송합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        error_message: 에러 메시지
    """
    response = WebSocketMessage(
        type="error",
        job_id=0,
        data={"error": error_message},
        timestamp=datetime.now()
    )
    
    try:
        await websocket.send_text(response.model_dump_json())
    except Exception as e:
        logger.error(f"에러 메시지 전송 실패: {e}")

# WebSocket 연결 통계를 위한 엔드포인트
async def get_websocket_stats():
    """
    WebSocket 연결 통계를 반환합니다.
    
    Returns:
        Dict[str, Any]: 연결 통계
    """
    return {
        "total_connections": connection_manager.get_connection_count(),
        "total_subscriptions": connection_manager.get_subscription_count(),
        "active_users": len(connection_manager.user_connections),
        "subscribed_jobs": len(connection_manager.job_subscriptions)
    }
