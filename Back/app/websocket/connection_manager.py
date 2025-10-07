"""
WebSocket 연결 관리를 위한 클래스
"""
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket
from datetime import datetime
from app.schemas import WebSocketMessage, JobStatusUpdate

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결을 관리하는 클래스"""
    
    def __init__(self):
        # 사용자별 연결 관리: {user_id: [websocket1, websocket2, ...]}
        self.user_connections: Dict[int, List[WebSocket]] = {}
        # 작업별 구독 관리: {job_id: {user_id1, user_id2, ...}}
        self.job_subscriptions: Dict[int, Set[int]] = {}
        # 연결별 구독 작업 관리: {websocket: {job_id1, job_id2, ...}}
        self.connection_subscriptions: Dict[WebSocket, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        WebSocket 연결을 수락하고 사용자 연결 목록에 추가합니다.
        
        Args:
            websocket: WebSocket 연결 객체
            user_id: 사용자 ID
        """
        await websocket.accept()
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        
        self.user_connections[user_id].append(websocket)
        self.connection_subscriptions[websocket] = set()
        
        logger.info(f"사용자 {user_id} WebSocket 연결됨")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        WebSocket 연결을 해제합니다.
        
        Args:
            websocket: WebSocket 연결 객체
            user_id: 사용자 ID
        """
        # 사용자 연결 목록에서 제거
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            
            # 사용자 연결이 없으면 사용자 항목 제거
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 구독 정보 정리
        if websocket in self.connection_subscriptions:
            subscribed_jobs = self.connection_subscriptions[websocket].copy()
            for job_id in subscribed_jobs:
                self.unsubscribe_job(websocket, job_id)
            
            del self.connection_subscriptions[websocket]
        
        logger.info(f"사용자 {user_id} WebSocket 연결 해제됨")
    
    def subscribe_job(self, websocket: WebSocket, job_id: int, user_id: int):
        """
        특정 작업의 상태 업데이트를 구독합니다.
        
        Args:
            websocket: WebSocket 연결 객체
            job_id: 구독할 작업 ID
            user_id: 사용자 ID
        """
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        
        self.job_subscriptions[job_id].add(user_id)
        self.connection_subscriptions[websocket].add(job_id)
        
        logger.info(f"사용자 {user_id}이 작업 {job_id} 구독함")
    
    def unsubscribe_job(self, websocket: WebSocket, job_id: int):
        """
        특정 작업의 상태 업데이트 구독을 해제합니다.
        
        Args:
            websocket: WebSocket 연결 객체
            job_id: 구독 해제할 작업 ID
        """
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].discard(job_id)
        
        # 작업 구독자 목록에서 사용자 제거
        if job_id in self.job_subscriptions:
            # 해당 작업을 구독하는 모든 사용자 중에서 이 연결의 사용자 찾기
            for user_id, connections in self.user_connections.items():
                if websocket in connections:
                    self.job_subscriptions[job_id].discard(user_id)
                    break
            
            # 구독자가 없으면 작업 항목 제거
            if not self.job_subscriptions[job_id]:
                del self.job_subscriptions[job_id]
        
        logger.info(f"작업 {job_id} 구독 해제됨")
    
    async def send_to_user(self, user_id: int, message: WebSocketMessage):
        """
        특정 사용자에게 메시지를 전송합니다.
        
        Args:
            user_id: 사용자 ID
            message: 전송할 메시지
        """
        if user_id not in self.user_connections:
            logger.warning(f"사용자 {user_id}의 연결을 찾을 수 없습니다")
            return
        
        message_json = message.model_dump_json()
        disconnected_connections = []
        
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"사용자 {user_id}에게 메시지 전송 실패: {e}")
                disconnected_connections.append(websocket)
        
        # 연결이 끊어진 WebSocket 정리
        for websocket in disconnected_connections:
            self.disconnect(websocket, user_id)
    
    async def send_to_job_subscribers(self, job_id: int, message: WebSocketMessage):
        """
        특정 작업을 구독하는 모든 사용자에게 메시지를 전송합니다.
        
        Args:
            job_id: 작업 ID
            message: 전송할 메시지
        """
        if job_id not in self.job_subscriptions:
            logger.warning(f"작업 {job_id}의 구독자를 찾을 수 없습니다")
            return
        
        message_json = message.model_dump_json()
        disconnected_connections = []
        
        for user_id in self.job_subscriptions[job_id]:
            if user_id in self.user_connections:
                for websocket in self.user_connections[user_id]:
                    try:
                        await websocket.send_text(message_json)
                    except Exception as e:
                        logger.error(f"사용자 {user_id}에게 메시지 전송 실패: {e}")
                        disconnected_connections.append((websocket, user_id))
        
        # 연결이 끊어진 WebSocket 정리
        for websocket, user_id in disconnected_connections:
            self.disconnect(websocket, user_id)
    
    async def broadcast_job_status_update(self, job_id: int, status_update: JobStatusUpdate):
        """
        작업 상태 업데이트를 구독자들에게 브로드캐스트합니다.
        
        Args:
            job_id: 작업 ID
            status_update: 상태 업데이트 정보
        """
        message = WebSocketMessage(
            type="job_status_update",
            job_id=job_id,
            data=status_update.model_dump(),
            timestamp=datetime.now()
        )
        
        await self.send_to_job_subscribers(job_id, message)
    
    async def broadcast_job_progress_update(self, job_id: int, progress: int, message: str = None):
        """
        작업 진행률 업데이트를 구독자들에게 브로드캐스트합니다.
        
        Args:
            job_id: 작업 ID
            progress: 진행률 (0-100)
            message: 추가 메시지
        """
        status_update = JobStatusUpdate(
            job_id=job_id,
            status="running",  # 진행률 업데이트는 보통 running 상태
            progress=progress,
            message=message,
            timestamp=datetime.now()
        )
        
        await self.broadcast_job_status_update(job_id, status_update)
    
    def get_connection_count(self) -> int:
        """
        현재 연결된 WebSocket 수를 반환합니다.
        
        Returns:
            int: 연결된 WebSocket 수
        """
        total_connections = 0
        for connections in self.user_connections.values():
            total_connections += len(connections)
        return total_connections
    
    def get_subscription_count(self) -> int:
        """
        현재 구독 중인 작업 수를 반환합니다.
        
        Returns:
            int: 구독 중인 작업 수
        """
        return len(self.job_subscriptions)

# 전역 연결 관리자 인스턴스
connection_manager = ConnectionManager()
