"""
FastAPI 내부에서 AI 작업을 직접 실행하기 위한 러너
"""

import logging
import os
import sys
import threading
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


def _run_workflow(job_id: int, job_type: str, input_data: Dict[str, Any]) -> None:
    try:
        logger.info(f"[INTERNAL RUNNER] start job_id={job_id}, job_type={job_type}")

        # AI 모듈 임포트 준비
        ai_path = "/app/ai_modules"
        if ai_path not in sys.path:
            sys.path.append(ai_path)

        from modules.ai_workflow import AIWorkflow  # type: ignore

        # 출력 디렉터리: /app/database/ai_podcast/<job_id>
        output_root = os.path.join(settings.upload_dir, "ai_podcast")
        job_output_dir = os.path.join(output_root, str(job_id))
        os.makedirs(job_output_dir, exist_ok=True)

        # 입력 파라미터 추출 (기본값 포함)
        category = (input_data or {}).get("category", "GOOGLE")
        host1 = (input_data or {}).get("host1_name", "김테크")
        host2 = (input_data or {}).get("host2_name", "박AI")
        recency = (input_data or {}).get("search_recency", "week")
        include_audio = bool((input_data or {}).get("include_audio", False))

        # AIWorkflow 실행
        workflow = AIWorkflow(
            perplexity_api_key=settings.perplexity_api_key,
            google_api_key=settings.google_api_key,
            naver_clova_client_id=settings.naver_clova_client_id,
            naver_clova_client_secret=settings.naver_clova_client_secret,
            config_path=os.path.join(ai_path, "config", "company_config.json"),
        )

        result = workflow.run_complete_workflow(
            category=category,
            host1_name=host1,
            host2_name=host2,
            search_recency=recency,
            include_audio=include_audio,
            output_dir=job_output_dir,
        )

        if result:
            logger.info(f"[INTERNAL RUNNER] job_id={job_id} 완료. 파일 생성됨: {list((result or {}).get('files', {}).keys())}")
        else:
            logger.warning(f"[INTERNAL RUNNER] job_id={job_id} 결과 없음(실패 가능)")

    except Exception as e:
        logger.exception(f"[INTERNAL RUNNER] 실행 실패: {e}")


def run_ai_job_internal(job_id: int, job_type: str, input_data: Dict[str, Any]) -> None:
    """백그라운드 스레드로 워크플로우 실행(비차단)"""
    thread = threading.Thread(target=_run_workflow, args=(job_id, job_type, input_data), daemon=True)
    thread.start()

