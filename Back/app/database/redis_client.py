import redis
import os
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        self.connect()
    
    def connect(self):
        """Redis 서버에 연결"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 연결 테스트
            self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[str]:
        """키로 값 조회"""
        if not self.is_connected():
            return None
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis GET 오류: {e}")
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """키-값 저장 (ex: 만료시간 초)"""
        if not self.is_connected():
            return False
        try:
            return self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET 오류: {e}")
            return False
    
    def set_json(self, key: str, data: dict, ex: Optional[int] = None) -> bool:
        """JSON 데이터 저장"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            return self.set(key, json_data, ex)
        except Exception as e:
            logger.error(f"Redis JSON SET 오류: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[dict]:
        """JSON 데이터 조회"""
        try:
            data = self.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis JSON GET 오류: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """키 삭제"""
        if not self.is_connected():
            return False
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE 오류: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        if not self.is_connected():
            return False
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS 오류: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """키 만료시간 설정"""
        if not self.is_connected():
            return False
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE 오류: {e}")
            return False
    
    def incr(self, key: str) -> Optional[int]:
        """카운터 증가"""
        if not self.is_connected():
            return None
        try:
            return self.redis_client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR 오류: {e}")
            return None
    
    def lpush(self, key: str, *values) -> Optional[int]:
        """리스트 왼쪽에 값 추가"""
        if not self.is_connected():
            return None
        try:
            return self.redis_client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH 오류: {e}")
            return None
    
    def rpop(self, key: str) -> Optional[str]:
        """리스트 오른쪽에서 값 제거"""
        if not self.is_connected():
            return None
        try:
            return self.redis_client.rpop(key)
        except Exception as e:
            logger.error(f"Redis RPOP 오류: {e}")
            return None
    
    def publish(self, channel: str, message: str) -> Optional[int]:
        """채널에 메시지 발행"""
        if not self.is_connected():
            return None
        try:
            return self.redis_client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis PUBLISH 오류: {e}")
            return None

# 전역 Redis 클라이언트 인스턴스
redis_client = RedisClient()