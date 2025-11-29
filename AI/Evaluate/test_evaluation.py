"""
팟캐스트 스크립트 평가 테스트 스크립트

실제 스크립트 데이터를 사용하여 평가 시스템을 테스트합니다.
"""

import json
import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Evaluate.script_evaluator import ScriptEvaluator


# 테스트용 스크립트 데이터 (사용자가 제공한 형식)
TEST_SCRIPT = {
    "beginner": {
        "intro": "안녕하세요! IT 기술을 알기 쉽게 설명해드리는 '테크 수다'입니다. 오늘은 요즘 화제인 인공지능, AI에 대한 흥미로운 소식을 가져왔어요. 구글이 AI를 더 안전하고 강력하게 만들어 줄 새로운 기술을 발표했다고 하네요!",
        "turns": [
            {
                "speaker": "man",
                "text": "네, 맞아요. 우리가 쓰는 컴퓨터 프로그램들을 관리해주는 '쿠버네티스'라는 똑똑한 관리자 시스템이 있는데, 구글이 이걸 대대적으로 업그레이드했다고 해요. 특히 스스로 생각하고 코드를 만드는 'AI 에이전트'들을 위한 업데이트라고 하던데요?"
            },
            {
                "speaker": "woman",
                "text": "정확해요! 이번 발표의 핵심은 크게 두 가지예요. 첫 번째는 'AI를 위한 안전한 놀이터'를 만들었다는 거예요. 이걸 '에이전트 샌드박스'라고 부르는데요."
            },
            {
                "speaker": "man",
                "text": "안전한 놀이터요? AI가 노는 곳인가요? (웃음)"
            },
            {
                "speaker": "woman",
                "text": "비슷해요! (웃음) AI 에이전트가 자유롭게 일하면서도, 실수로 다른 중요한 컴퓨터 시스템을 망가뜨리지 않도록 완벽하게 분리된 공간을 만들어주는 거예요. 덕분에 기업들은 AI가 만든 코드를 마음 놓고 테스트해볼 수 있게 됐죠."
            },
            {
                "speaker": "man",
                "text": "와, 정말 안심이 되겠네요. 그럼 두 번째 핵심은 뭔가요?"
            },
            {
                "speaker": "woman",
                "text": "두 번째는 바로 '상상을 초월하는 컴퓨터 파워'예요. 거대한 AI를 학습시키려면 컴퓨터가 정말 많이 필요한데, 구글이 무려 13만 대의 컴퓨터를 마치 한 대처럼 묶어서 관리하는 데 성공했대요."
            },
            {
                "speaker": "man",
                "text": "13만 대요? 정말 엄청나네요! 그 정도면 아무리 큰 AI 작업이라도 문제없겠어요."
            },
            {
                "speaker": "woman",
                "text": "네, 그렇죠. 쉽게 말해 구글이 더 똑똑해진 AI를 더 안전하게, 그리고 훨씬 더 큰 규모로 다룰 수 있는 강력한 기반을 마련한 셈이에요."
            }
        ],
        "outro": "오늘은 구글의 새로운 AI 기술에 대해 알아봤습니다. AI가 우리 삶을 더 편리하게 만들어주는 만큼, 이렇게 안전하고 강력하게 발전하는 모습이 기대되네요. '테크 수다' 다음 시간에 더 재미있는 소식으로 돌아오겠습니다!"
    },
    "intermediate": {
        "intro": "안녕하세요, 개발자와 엔지니어를 위한 IT 팟캐스트 '코드 브레이크'입니다. 최근 KubeCon 2025에서 구글이 GKE 출시 10주년을 맞아 AI 시대를 겨냥한 중요한 업데이트를 발표했습니다. 오늘은 그 핵심 내용을 짚어보겠습니다.",
        "turns": [
            {
                "speaker": "man",
                "text": "네, 이번 구글의 발표는 크게 세 가지 방향으로 요약할 수 있을 것 같습니다. 첫 번째는 역시 핵심 쿠버네티스, 즉 오픈소스(OSS) 자체를 강화하는 움직임이겠죠?"
            },
            {
                "speaker": "woman",
                "text": "맞습니다. 특히 AI 에이전트 워크로드의 보안과 격리 문제가 화두였는데, 이를 위해 쿠버네티스 네이티브 'AgentSandbox API'를 새롭게 공개했어요. 추론(inference) 성능 향상을 위한 'Inference Gateway API'도 추가하면서 오픈소스 생태계에 직접 기여하려는 의지를 보여줬습니다."
            },
            {
                "speaker": "man",
                "text": "오픈소스 기여도 중요하지만, 결국 구글 클라우드 사용자들이 체감할 수 있는 GKE의 발전이 더 궁금한데요. 관리형 쿠버네티스로서 GKE는 어떤 표준을 제시하고 있나요?"
            },
            {
                "speaker": "woman",
                "text": "좋은 질문입니다. 두 번째 전략이 바로 GKE를 통한 표준 제시인데요. 대표적으로 gVisor 기반의 'GKE 에이전트 샌드박스'를 프리뷰로 출시했습니다. LLM이 생성한 코드를 안전하게 실행하면서도, 콜드 스타트 시간을 90%나 개선해서 성능까지 잡았죠."
            },
            {
                "speaker": "man",
                "text": "성능 개선 폭이 상당하네요. 스케일 측면에서도 인상적인 발표가 있었죠?"
            },
            {
                "speaker": "woman",
                "text": "네, 실험적으로 13만 개 노드로 구성된 단일 클러스터 구축에 성공했다고 밝혔습니다. AI 학습에 필요한 압도적인 확장성을 증명한 셈이죠. 여기에 CNCF의 '쿠버네티스 AI 적합성 프로그램' 인증까지 획득하며 신뢰도를 높였습니다."
            },
            {
                "speaker": "man",
                "text": "마지막으로 생태계 지원은 어떻게 이루어지고 있나요? Ray나 Slurm 같은 최신 AI 프레임워크를 쿠버네티스에서 사용하는 게 아직은 좀 번거로운데요."
            },
            {
                "speaker": "woman",
                "text": "그 부분을 해결하는 것이 세 번째 전략입니다. Anyscale 같은 파트너사와 협력해서 Ray를 GKE에서 더 쉽게 사용하도록 지원하고 있고요. 특히 대규모 LLM 추론을 위한 분산형 컨트롤 플레인 오픈소스 프로젝트 'llm-d'에 창립 멤버로 기여하며 생태계 확장을 주도하고 있습니다."
            }
        ],
        "outro": "정리하자면, 구글은 핵심 OSS 강화, GKE를 통한 관리형 서비스 표준 제시, 그리고 AI 프레임워크 생태계 지원이라는 세 가지 축을 통해 쿠버네티스를 명실상부한 AI 시대의 표준 플랫폼으로 만들고 있습니다. 지금까지 '코드 브레이크'였습니다."
    },
    "advanced": {
        "intro": "안녕하십니까. 클라우드 네이티브 기술의 최전선을 다루는 팟캐스트, 'The Control Plane'입니다. 이번 KubeCon 2025에서 구글은 GKE와 쿠버네티스의 로드맵을 발표하며, 단순한 컨테이너 오케스트레이터를 넘어 에이전틱 AI와 같은 차세대 워크로드를 위한 통합 플랫폼으로의 진화를 선언했습니다. 오늘 그 기술적 진전을 심도 있게 분석해 보겠습니다.",
        "turns": [
            {
                "speaker": "man",
                "text": "이번 발표의 핵심은 단연 '에이전틱 AI 워크로드'에 대한 기반 확장이라고 봅니다. 비결정적(non-deterministic) 특성을 가진 에이전트의 보안과 격리 문제를 어떻게 해결하려 하는지가 관건이었죠."
            },
            {
                "speaker": "woman",
                "text": "그렇습니다. 구글은 쿠버네티스 네이티브 'AgentSandbox API'를 공개하며 해답을 제시했습니다. gVisor를 활용해 강력한 커널 레벨 격리 환경을 제공하고, 이를 기반으로 한 관리형 서비스 'GKE Agent Sandbox'는 한발 더 나아갔죠. 통합 스냅샷, 컨테이너 최적화 컴퓨팅 등을 통해 완전 격리된 워크로드의 콜드 스타트 지연 시간을 90% 단축시켜 sub-second latency를 달성했습니다."
            },
            {
                "speaker": "man",
                "text": "Sub-second latency는 에이전트의 응답성 측면에서 매우 중요한 지표죠. 격리뿐만 아니라, 파운데이션 모델 학습에 필요한 초거대 스케일(Hyperscale)에 대한 대응도 인상적이었습니다."
            },
            {
                "speaker": "woman",
                "text": "네, GKE를 사용해 130,000개 노드로 구성된 단일 클러스터를 성공적으로 구축한 것은 GKE 컨트롤 플레인의 확장성을 명확히 입증한 사례입니다. 여기서 그치지 않고 MultiKueue와 같은 멀티 클러스터 오케스트레이션 기능을 통해 잡 샤딩(job sharding)을 지원하며 스케일업과 스케일아웃, 양면에서의 발전을 동시에 꾀하고 있습니다."
            },
            {
                "speaker": "man",
                "text": "결국 플랫폼의 성능과 확장성도 중요하지만, 실제 AI/ML 프레임워크와의 통합 및 생태계 전략 없이는 공허한 외침이 될 수 있습니다. 이 부분은 어떻게 주도하고 있습니까?"
            },
            {
                "speaker": "woman",
                "text": "구글은 그 점을 명확히 인지하고 있습니다. Anyscale과의 협력을 통해 GKE에 최적화된 오픈소스 Ray를 제공하고, 대규모 LLM 추론을 위한 분산형 쿠버네티스 네이티브 컨트롤 플레인인 'llm-d' 프로젝트에 창립 멤버로 참여했죠. 이는 특정 워크로드에 대한 운영 마찰을 줄이고 표준화된 아키텍처를 제시하려는 전략의 일환으로 보입니다."
            },
            {
                "speaker": "man",
                "text": "CNCF의 'Kubernetes AI Conformance' 인증 획득도 같은 맥락이겠군요. AI/ML 워크로드의 이식성과 상호운용성을 보장함으로써 GKE를 사실상의 표준으로 만들려는 의도라고 해석됩니다."
            },
            {
                "speaker": "woman",
                "text": "정확합니다. 결국 구글은 기술적 깊이와 생태계 리더십을 모두 가져가며, 쿠버네티스를 차세대 AI 워크로드를 위한 가장 신뢰할 수 있는 플랫폼으로 포지셔닝하고 있습니다."
            }
        ],
        "outro": "오늘 우리는 KubeCon 2025에서 발표된 구글의 전략을 통해 쿠버네티스의 미래를 엿보았습니다. 에이전틱 AI를 위한 강력한 격리, 입증된 하이퍼스케일, 그리고 생태계 주도를 통해 GKE는 새로운 시대를 준비하고 있습니다. 'The Control Plane', 다음 시간에 더 깊이 있는 기술 분석으로 찾아뵙겠습니다."
    }
}


def main():
    """메인 테스트 함수"""
    print("="*60)
    print("📊 팟캐스트 스크립트 평가 테스트")
    print("="*60)
    
    # 평가자 초기화
    try:
        evaluator = ScriptEvaluator()
        print("✅ 평가자 초기화 완료")
    except ValueError as e:
        print(f"❌ 평가자 초기화 실패: {e}")
        print("💡 .env 파일에 GOOGLE_API_KEY를 설정해주세요.")
        return
    
    # 방법 1: Back 서비스에서 생성된 파일 자동 찾기
    print("\n" + "="*60)
    print("🔍 Back 서비스 스크립트 파일 검색")
    print("="*60)
    
    # 로컬 경로와 Docker 경로 모두 시도
    possible_paths = [
        "/app/podcasts",  # Docker 내부 경로
        "../Back/podcasts",  # 로컬 개발 경로
        "podcasts",  # 현재 디렉토리 기준
    ]
    
    script_files = []
    for base_path in possible_paths:
        found_files = evaluator.find_script_files(base_path)
        if found_files:
            script_files.extend(found_files)
            print(f"✅ {base_path}에서 {len(found_files)}개 파일 발견")
            break
    
    if script_files:
        print(f"\n📋 발견된 스크립트 파일:")
        for i, file_path in enumerate(script_files[:5], 1):  # 최대 5개만 표시
            print(f"  {i}. {file_path}")
        
        # 첫 번째 파일로 평가
        print(f"\n📊 첫 번째 파일 평가 시작: {script_files[0]}")
        result = evaluator.evaluate_from_file(script_files[0], compare=True)
        
        if result.get("status") == "success":
            evaluator.print_evaluation_summary(result)
            evaluator.save_evaluation_result(result)
        else:
            print(f"❌ 평가 실패: {result.get('error')}")
            print("\n💡 하드코딩된 테스트 데이터로 평가를 진행합니다...")
    else:
        print("⚠️ Back 서비스에서 생성된 스크립트 파일을 찾을 수 없습니다.")
        print("💡 하드코딩된 테스트 데이터로 평가를 진행합니다...")
    
    # 방법 2: 하드코딩된 테스트 데이터로 평가 (파일을 찾지 못한 경우)
    if not script_files or result.get("status") != "success":
        print("\n" + "="*60)
        print("📊 하드코딩된 테스트 데이터로 평가")
        print("="*60)
        
        # 각 난이도별 평가
        print("\n📊 개별 난이도 평가 시작")
        individual_results = evaluator.evaluate_all_difficulties(TEST_SCRIPT)
        
        # 비교 평가
        print("\n📈 난이도 간 비교 평가 시작")
        comparison_result = evaluator.compare_difficulties(TEST_SCRIPT)
        
        # 결과 정리
        evaluation_result = {
            "status": "success",
            "data": {
                "individual_evaluations": individual_results,
                "comparison": comparison_result
            }
        }
        
        # 결과 출력
        print("\n" + "="*60)
        print("📋 평가 결과 요약")
        print("="*60)
        evaluator.print_evaluation_summary(evaluation_result)
        
        # 결과 저장
        print("\n" + "="*60)
        print("💾 평가 결과 저장")
        print("="*60)
        saved_path = evaluator.save_evaluation_result(evaluation_result)
        
        if saved_path:
            print(f"✅ 평가 결과가 저장되었습니다: {saved_path}")
    
    print("\n" + "="*60)
    print("✅ 평가 완료!")
    print("="*60)


if __name__ == "__main__":
    main()

