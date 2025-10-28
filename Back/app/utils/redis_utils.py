from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime, timedelta
from app.database.redis_client import redis_client
from app.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis 캐시 관리 클래스"""
    
    @staticmethod
    def cache_key(prefix: str, *args) -> str:
        """캐시 키 생성"""
        return f"{prefix}:{':'.join(map(str, args))}"
    
    @staticmethod
    def set_cache(key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """캐시 데이터 저장"""
        ttl = ttl or settings.cache_ttl
        return redis_client.set_json(key, data, ex=ttl)
    
    @staticmethod
    def get_cache(key: str) -> Optional[Any]:
        """캐시 데이터 조회"""
        return redis_client.get_json(key)
    
    @staticmethod
    def delete_cache(key: str) -> bool:
        """캐시 데이터 삭제"""
        return redis_client.delete(key)
    
    @staticmethod
    def exists_cache(key: str) -> bool:
        """캐시 존재 여부 확인"""
        return redis_client.exists(key)

class SessionManager:
    """사용자 세션 관리 클래스"""
    
    @staticmethod
    def session_key(user_id) -> str:
        """세션 키 생성"""
        return f"session:user:{user_id}"

    @staticmethod
    def set_session(user_id, session_data: Dict[str, Any]) -> bool:
        """사용자 세션 저장"""
        key = SessionManager.session_key(user_id)
        session_data["created_at"] = datetime.now().isoformat()
        return redis_client.set_json(key, session_data, ex=settings.session_ttl)

    @staticmethod
    def get_session(user_id) -> Optional[Dict[str, Any]]:
        """사용자 세션 조회"""
        key = SessionManager.session_key(user_id)
        return redis_client.get_json(key)

    @staticmethod
    def delete_session(user_id) -> bool:
        """사용자 세션 삭제"""
        key = SessionManager.session_key(user_id)
        return redis_client.delete(key)

    @staticmethod
    def refresh_session(user_id) -> bool:
        """세션 만료시간 연장"""
        key = SessionManager.session_key(user_id)
        return redis_client.expire(key, settings.session_ttl)

class RateLimiter:
    """API 레이트 리미팅 클래스"""
    
    @staticmethod
    def rate_limit_key(user_id, endpoint: str) -> str:
        """레이트 리미트 키 생성"""
        return f"rate_limit:user:{user_id}:{endpoint}"

    @staticmethod
    def check_rate_limit(user_id, endpoint: str, limit: int, window: int) -> bool:
        """레이트 리미트 확인"""
        key = RateLimiter.rate_limit_key(user_id, endpoint)

        # 현재 카운트 조회
        current_count = redis_client.incr(key)
        
        if current_count == 1:
            # 첫 요청인 경우 만료시간 설정
            redis_client.expire(key, window)
        
        return current_count <= limit
    
    @staticmethod
    def get_remaining_requests(user_id, endpoint: str, limit: int) -> int:
        """남은 요청 수 조회"""
        key = RateLimiter.rate_limit_key(user_id, endpoint)
        current_count = redis_client.get(key)
        
        if current_count is None:
            return limit
        
        return max(0, limit - int(current_count))

class AnalysisCache:
    """분석 결과 캐시 관리 클래스"""
    
    @staticmethod
    def analysis_key(topic_id) -> str:
        """분석 결과 키 생성"""
        return f"analysis:topic:{topic_id}"

    @staticmethod
    def cache_analysis_result(topic_id, result: Dict[str, Any]) -> bool:
        """분석 결과 캐시 저장"""
        key = AnalysisCache.analysis_key(topic_id)
        cache_data = {
            "result": result,
            "cached_at": datetime.now().isoformat(),
            "topic_id": topic_id
        }
        return redis_client.set_json(key, cache_data, ex=settings.cache_ttl)
    
    @staticmethod
    def get_analysis_result(topic_id) -> Optional[Dict[str, Any]]:
        """분석 결과 캐시 조회"""
        key = AnalysisCache.analysis_key(topic_id)
        return redis_client.get_json(key)

    @staticmethod
    def invalidate_analysis(topic_id) -> bool:
        """분석 결과 캐시 무효화"""
        key = AnalysisCache.analysis_key(topic_id)
        return redis_client.delete(key)

class QueueManager:
    """작업 큐 관리 클래스"""
    
    @staticmethod
    def queue_key(queue_name: str) -> str:
        """큐 키 생성"""
        return f"queue:{queue_name}"
    
    @staticmethod
    def enqueue(queue_name: str, data: Dict[str, Any]) -> bool:
        """큐에 작업 추가"""
        key = QueueManager.queue_key(queue_name)
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            redis_client.lpush(key, json_data)
            return True
        except Exception as e:
            logger.error(f"큐 추가 오류: {e}")
            return False
    
    @staticmethod
    def dequeue(queue_name: str) -> Optional[Dict[str, Any]]:
        """큐에서 작업 제거"""
        key = QueueManager.queue_key(queue_name)
        try:
            data = redis_client.rpop(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"큐 제거 오류: {e}")
            return None
    
    @staticmethod
    def queue_size(queue_name: str) -> int:
        """큐 크기 조회"""
        key = QueueManager.queue_key(queue_name)
        return redis_client.redis_client.llen(key) if redis_client.is_connected() else 0

class NotificationManager:
    """알림 관리 클래스"""
    
    @staticmethod
    def publish_notification(channel: str, message: Dict[str, Any]) -> bool:
        """알림 발행"""
        try:
            json_message = json.dumps(message, ensure_ascii=False)
            redis_client.publish(channel, json_message)
            return True
        except Exception as e:
            logger.error(f"알림 발행 오류: {e}")
            return False
    
    @staticmethod
    def notify_analysis_complete(topic_id, user_id, status: str) -> bool:
        """분석 완료 알림"""
        message = {
            "type": "analysis_complete",
            "topic_id": topic_id,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        return NotificationManager.publish_notification("analysis_updates", message)
    
    @staticmethod
    def notify_podcast_generated(topic_id: int, user_id: int, podcast_url: str) -> bool:
        """팟캐스트 생성 완료 알림"""
        message = {
            "type": "podcast_generated",
            "topic_id": topic_id,
            "user_id": user_id,
            "podcast_url": podcast_url,
            "timestamp": datetime.now().isoformat()
        }
        return NotificationManager.publish_notification("analysis_updates", message)
