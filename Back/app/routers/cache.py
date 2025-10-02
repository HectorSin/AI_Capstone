from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from app.utils.redis_utils import CacheManager, SessionManager, RateLimiter, AnalysisCache
from app.database.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/cache/status")
async def get_cache_status():
    """Redis 캐시 상태 확인"""
    return {
        "redis_connected": redis_client.is_connected(),
        "status": "healthy" if redis_client.is_connected() else "unhealthy"
    }

@router.post("/cache/set")
async def set_cache_data(key: str, data: Dict[str, Any], ttl: Optional[int] = None):
    """캐시 데이터 저장"""
    try:
        success = CacheManager.set_cache(key, data, ttl)
        if success:
            return {"message": "캐시 저장 성공", "key": key}
        else:
            raise HTTPException(status_code=500, detail="캐시 저장 실패")
    except Exception as e:
        logger.error(f"캐시 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/get/{key}")
async def get_cache_data(key: str):
    """캐시 데이터 조회"""
    try:
        data = CacheManager.get_cache(key)
        if data is None:
            raise HTTPException(status_code=404, detail="캐시 데이터를 찾을 수 없습니다")
        return {"key": key, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캐시 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/delete/{key}")
async def delete_cache_data(key: str):
    """캐시 데이터 삭제"""
    try:
        success = CacheManager.delete_cache(key)
        if success:
            return {"message": "캐시 삭제 성공", "key": key}
        else:
            return {"message": "캐시 데이터를 찾을 수 없습니다", "key": key}
    except Exception as e:
        logger.error(f"캐시 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/set/{user_id}")
async def set_user_session(user_id: int, session_data: Dict[str, Any]):
    """사용자 세션 저장"""
    try:
        success = SessionManager.set_session(user_id, session_data)
        if success:
            return {"message": "세션 저장 성공", "user_id": user_id}
        else:
            raise HTTPException(status_code=500, detail="세션 저장 실패")
    except Exception as e:
        logger.error(f"세션 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/get/{user_id}")
async def get_user_session(user_id: int):
    """사용자 세션 조회"""
    try:
        session_data = SessionManager.get_session(user_id)
        if session_data is None:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        return {"user_id": user_id, "session": session_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/delete/{user_id}")
async def delete_user_session(user_id: int):
    """사용자 세션 삭제"""
    try:
        success = SessionManager.delete_session(user_id)
        if success:
            return {"message": "세션 삭제 성공", "user_id": user_id}
        else:
            return {"message": "세션을 찾을 수 없습니다", "user_id": user_id}
    except Exception as e:
        logger.error(f"세션 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rate-limit/check/{user_id}/{endpoint}")
async def check_rate_limit(user_id: int, endpoint: str, limit: int = 10, window: int = 60):
    """레이트 리미트 확인"""
    try:
        allowed = RateLimiter.check_rate_limit(user_id, endpoint, limit, window)
        remaining = RateLimiter.get_remaining_requests(user_id, endpoint, limit)
        
        return {
            "allowed": allowed,
            "remaining_requests": remaining,
            "limit": limit,
            "window_seconds": window
        }
    except Exception as e:
        logger.error(f"레이트 리미트 확인 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/cache/{topic_id}")
async def cache_analysis_result(topic_id: int, result: Dict[str, Any]):
    """분석 결과 캐시 저장"""
    try:
        success = AnalysisCache.cache_analysis_result(topic_id, result)
        if success:
            return {"message": "분석 결과 캐시 저장 성공", "topic_id": topic_id}
        else:
            raise HTTPException(status_code=500, detail="분석 결과 캐시 저장 실패")
    except Exception as e:
        logger.error(f"분석 결과 캐시 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/cache/{topic_id}")
async def get_analysis_result(topic_id: int):
    """분석 결과 캐시 조회"""
    try:
        result = AnalysisCache.get_analysis_result(topic_id)
        if result is None:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
        return {"topic_id": topic_id, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 결과 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/analysis/cache/{topic_id}")
async def invalidate_analysis_result(topic_id: int):
    """분석 결과 캐시 무효화"""
    try:
        success = AnalysisCache.invalidate_analysis(topic_id)
        if success:
            return {"message": "분석 결과 캐시 무효화 성공", "topic_id": topic_id}
        else:
            return {"message": "분석 결과를 찾을 수 없습니다", "topic_id": topic_id}
    except Exception as e:
        logger.error(f"분석 결과 캐시 무효화 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))