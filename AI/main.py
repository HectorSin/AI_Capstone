#!/usr/bin/env python3
"""
AI 팟캐스트 생성 시스템 메인 실행 파일

이 파일은 AI 팟캐스트 생성 워크플로우를 실행하는 메인 엔트리포인트입니다.
"""

import os
import sys
import argparse
import json
from typing import List, Optional
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.ai_workflow import AIWorkflow
from config.settings import AISettings


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="AI 팟캐스트 생성 시스템")
    
    # 기본 인수
    parser.add_argument("--category", "-c", type=str, required=True,
                       help="뉴스 카테고리 (예: GOOGLE, META, OPENAI)")
    parser.add_argument("--host1", type=str, default="김테크",
                       help="첫 번째 호스트 이름 (기본값: 김테크)")
    parser.add_argument("--host2", type=str, default="박AI",
                       help="두 번째 호스트 이름 (기본값: 박AI)")
    parser.add_argument("--search-recency", "-r", type=str, default="week",
                       choices=["day", "week", "month"],
                       help="검색 기간 필터 (기본값: week)")
    parser.add_argument("--no-audio", action="store_true",
                       help="오디오 생성 제외")
    parser.add_argument("--output-dir", "-o", type=str, default="data/output",
                       help="출력 디렉토리 (기본값: data/output)")
    
    # 다중 카테고리 처리
    parser.add_argument("--categories", type=str, nargs="+",
                       help="여러 카테고리 처리")
    
    # 시스템 정보
    parser.add_argument("--status", action="store_true",
                       help="시스템 상태 확인")
    parser.add_argument("--test", action="store_true",
                       help="테스트 실행")
    
    args = parser.parse_args()
    
    # 시스템 상태 확인
    if args.status:
        show_system_status()
        return
    
    # 테스트 실행
    if args.test:
        run_tests()
        return
    
    # 설정 검증
    validation = AISettings.validate_settings()
    if not validation["valid"]:
        print("설정 오류:")
        for error in validation["errors"]:
            print(f"  - {error}")
        print("\n환경변수를 설정하거나 .env 파일을 확인해주세요.")
        return
    
    # 경고 출력
    if validation["warnings"]:
        print("경고:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
        print()
    
    # AI 워크플로우 초기화
    try:
        workflow = AIWorkflow(
            perplexity_api_key=AISettings.PERPLEXITY_API_KEY,
            google_api_key=AISettings.GOOGLE_API_KEY,
            naver_clova_client_id=AISettings.NAVER_CLOVA_CLIENT_ID,
            naver_clova_client_secret=AISettings.NAVER_CLOVA_CLIENT_SECRET,
            config_path=AISettings.CONFIG_PATH
        )
        print("AI 워크플로우 초기화 완료")
    except Exception as e:
        print(f"AI 워크플로우 초기화 실패: {e}")
        return
    
    # 다중 카테고리 처리
    if args.categories:
        print(f"다중 카테고리 팟캐스트 생성 시작: {', '.join(args.categories)}")
        
        results = workflow.run_multiple_categories(
            categories=args.categories,
            host1_name=args.host1,
            host2_name=args.host2,
            search_recency=args.search_recency,
            include_audio=not args.no_audio,
            output_dir=args.output_dir
        )
        
        # 결과 요약
        successful = sum(1 for r in results.values() if r is not None)
        print(f"\n전체 결과: {successful}/{len(args.categories)}개 카테고리 성공")
        
        for category, result in results.items():
            if result:
                print(f"{category}: 성공")
            else:
                print(f"{category}: 실패")
    
    # 단일 카테고리 처리
    else:
        print(f"단일 카테고리 팟캐스트 생성 시작: {args.category}")
        
        result = workflow.run_complete_workflow(
            category=args.category,
            host1_name=args.host1,
            host2_name=args.host2,
            search_recency=args.search_recency,
            include_audio=not args.no_audio,
            output_dir=args.output_dir
        )
        
        if result:
            print("팟캐스트 생성 완료!")
        else:
            print("팟캐스트 생성 실패")


def show_system_status():
    """시스템 상태 출력"""
    print("AI 팟캐스트 생성 시스템 상태")
    print("=" * 50)
    
    # 설정 상태
    print("설정 상태:")
    validation = AISettings.validate_settings()
    if validation["valid"]:
        print("설정 완료")
    else:
        print("설정 오류")
        for error in validation["errors"]:
            print(f"    - {error}")
    
    # 경고 출력
    if validation["warnings"]:
        print("경고:")
        for warning in validation["warnings"]:
            print(f"    - {warning}")
    
    print()
    
    # 시스템 정보
    print("시스템 정보:")
    print(f"  - Python 버전: {sys.version}")
    print(f"  - 작업 디렉토리: {os.getcwd()}")
    print(f"  - 설정 파일: {AISettings.CONFIG_PATH}")
    print(f"  - 출력 디렉토리: {AISettings.OUTPUT_DIR}")
    
    # AI 워크플로우 상태 (가능한 경우)
    try:
        workflow = AIWorkflow(AISettings.PERPLEXITY_API_KEY)
        system_status = workflow.get_system_status()
        
        print("\nAI 모듈 상태:")
        for module, status in system_status["modules"].items():
            print(f"  - {module}: {status}")
        
        print(f"\nAPI 상태:")
        print(f"  - Perplexity API: {system_status['perplexity_api']}")
        print(f"  - Google LLM: {system_status['google_llm']}")
        print(f"  - TTS 시스템: {system_status['tts_system']['tts_available']}")
        
    except Exception as e:
        print(f"\nAI 워크플로우 상태 확인 실패: {e}")


def run_tests():
    """테스트 실행"""
    print("AI 시스템 테스트 실행")
    print("=" * 50)
    
    try:
        import unittest
        
        # 테스트 디스커버리
        loader = unittest.TestLoader()
        start_dir = os.path.join(os.path.dirname(__file__), 'tests')
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        # 테스트 실행
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # 결과 출력
        if result.wasSuccessful():
            print("\n모든 테스트 통과!")
        else:
            print(f"\n{len(result.failures)}개 테스트 실패, {len(result.errors)}개 오류")
            
    except ImportError:
        print("unittest 모듈을 찾을 수 없습니다.")
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")


def show_usage_examples():
    """사용 예제 출력"""
    print("사용 예제:")
    print()
    print("1. 단일 카테고리 팟캐스트 생성:")
    print("   python main.py --category GOOGLE")
    print()
    print("2. 사용자 정의 호스트로 팟캐스트 생성:")
    print("   python main.py --category META --host1 '이테크' --host2 '김AI'")
    print()
    print("3. 오디오 없이 대본만 생성:")
    print("   python main.py --category OPENAI --no-audio")
    print()
    print("4. 여러 카테고리 일괄 처리:")
    print("   python main.py --categories GOOGLE META OPENAI")
    print()
    print("5. 시스템 상태 확인:")
    print("   python main.py --status")
    print()
    print("6. 테스트 실행:")
    print("   python main.py --test")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류 발생: {e}")
        print("\n도움이 필요하면 --help 옵션을 사용하세요.")
