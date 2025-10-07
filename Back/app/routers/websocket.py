"""
WebSocket 라우터
"""
import logging
from fastapi import APIRouter, WebSocket, Depends, HTTPException
from app.websocket.endpoints import websocket_endpoint, get_websocket_stats
from app.auth import get_current_user
from app.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_route(websocket: WebSocket, user_id: int):
    """
    WebSocket 연결 엔드포인트
    
    Args:
        websocket: WebSocket 연결 객체
        user_id: 사용자 ID
    """
    await websocket_endpoint(websocket, user_id)

@router.get("/stats", summary="WebSocket 연결 통계")
async def get_connection_stats(current_user: User = Depends(get_current_user)):
    """
    WebSocket 연결 통계를 조회합니다.
    """
    try:
        stats = await get_websocket_stats()
        return stats
    except Exception as e:
        logger.error(f"WebSocket 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
