"""
팟캐스트 스크립트 평가 사용 예제

이 파일은 ScriptEvaluator를 사용하는 방법을 보여줍니다.
"""

import json
from script_evaluator import ScriptEvaluator


def example_evaluate_from_dict():
    """딕셔너리로 직접 스크립트를 평가하는 예제"""
    
    # 평가할 스크립트 데이터 (예시)
    script_data = {
        "beginner": {
            "intro": "안녕하세요! IT 기술을 알기 쉽게 설명해드리는 '테크 수다'입니다.",
            "turns": [
                {"speaker": "man", "text": "오늘은 AI에 대해 이야기해볼게요."},
                {"speaker": "woman", "text": "네, AI는 인공지능을 의미합니다."}
            ],
            "outro": "다음 시간에 더 재미있는 소식으로 돌아오겠습니다!"
        },
        "intermediate": {
            "intro": "안녕하세요, 개발자를 위한 IT 팟캐스트입니다.",
            "turns": [
                {"speaker": "man", "text": "오늘은 머신러닝과 딥러닝의 차이에 대해 논의해보겠습니다."},
                {"speaker": "woman", "text": "머신러닝은 데이터로부터 학습하는 알고리즘이고, 딥러닝은 신경망을 사용하는 머신러닝의 한 분야입니다."}
            ],
            "outro": "지금까지 코드 브레이크였습니다."
        },
        "advanced": {
            "intro": "안녕하십니까. 클라우드 네이티브 기술의 최전선을 다루는 팟캐스트입니다.",
            "turns": [
                {"speaker": "man", "text": "이번 발표의 핵심은 단연 '에이전틱 AI 워크로드'에 대한 기반 확장이라고 봅니다."},
                {"speaker": "woman", "text": "gVisor를 활용해 강력한 커널 레벨 격리 환경을 제공하고, 이를 기반으로 한 관리형 서비스는 sub-second latency를 달성했습니다."}
            ],
            "outro": "다음 시간에 더 깊이 있는 기술 분석으로 찾아뵙겠습니다."
        }
    }
    
    # 평가자 초기화
    evaluator = ScriptEvaluator()
    
    # 각 난이도별 평가
    print("="*60)
    print("📊 개별 난이도 평가")
    print("="*60)
    results = evaluator.evaluate_all_difficulties(script_data)
    
    # 비교 평가
    print("\n" + "="*60)
    print("📈 난이도 간 비교 평가")
    print("="*60)
    comparison = evaluator.compare_difficulties(script_data)
    
    # 결과 출력
    evaluator.print_evaluation_summary({
        "status": "success",
        "data": {
            "individual_evaluations": results,
            "comparison": comparison
        }
    })
    
    # 결과 저장
    evaluation_result = {
        "status": "success",
        "data": {
            "individual_evaluations": results,
            "comparison": comparison
        }
    }
    evaluator.save_evaluation_result(evaluation_result)


def example_evaluate_from_file():
    """JSON 파일에서 스크립트를 읽어서 평가하는 예제"""
    
    # JSON 파일 경로 (실제 파일 경로로 변경 필요)
    file_path = "path/to/your/script.json"
    
    # 평가자 초기화
    evaluator = ScriptEvaluator()
    
    # 파일에서 평가
    result = evaluator.evaluate_from_file(file_path, compare=True)
    
    if result.get("status") == "success":
        # 결과 출력
        evaluator.print_evaluation_summary(result)
        
        # 결과 저장
        evaluator.save_evaluation_result(result)
    else:
        print(f"❌ 평가 실패: {result.get('error')}")


def example_single_difficulty_evaluation():
    """단일 난이도만 평가하는 예제"""
    
    # 평가할 스크립트 데이터
    beginner_script = {
        "intro": "안녕하세요! IT 기술을 알기 쉽게 설명해드리는 '테크 수다'입니다.",
        "turns": [
            {"speaker": "man", "text": "오늘은 AI에 대해 이야기해볼게요."},
            {"speaker": "woman", "text": "네, AI는 인공지능을 의미합니다."}
        ],
        "outro": "다음 시간에 더 재미있는 소식으로 돌아오겠습니다!"
    }
    
    # 평가자 초기화
    evaluator = ScriptEvaluator()
    
    # 초급 난이도만 평가
    result = evaluator.evaluate_single_difficulty(beginner_script, "beginner")
    
    if result.get("status") == "success":
        eval_data = result.get("data", {})
        print(f"✅ 초급 난이도 평가 완료")
        print(f"종합 점수: {eval_data.get('overall_score', 'N/A')}/10")
        print(f"적합성: {'적합' if eval_data.get('is_appropriate') else '부적합'}")
        print(f"\n상세 피드백:")
        print(eval_data.get("detailed_feedback", ""))
    else:
        print(f"❌ 평가 실패: {result.get('error')}")


if __name__ == "__main__":
    print("팟캐스트 스크립트 평가 예제")
    print("="*60)
    
    # 예제 1: 딕셔너리로 직접 평가
    print("\n[예제 1] 딕셔너리로 직접 평가")
    example_evaluate_from_dict()
    
    # 예제 2: 파일에서 평가 (파일 경로가 있을 때만 실행)
    # print("\n[예제 2] 파일에서 평가")
    # example_evaluate_from_file()
    
    # 예제 3: 단일 난이도 평가
    # print("\n[예제 3] 단일 난이도 평가")
    # example_single_difficulty_evaluation()

