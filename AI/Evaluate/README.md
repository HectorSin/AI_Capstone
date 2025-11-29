# 팟캐스트 스크립트 평가 시스템

난이도별 팟캐스트 대본을 Gemini API를 사용하여 평가하는 시스템입니다.

## 기능

- **개별 난이도 평가**: 초급(beginner), 중급(intermediate), 고급(advanced) 각 난이도별 적합성 평가
- **비교 평가**: 세 가지 난이도 간의 차이와 균형 평가
- **상세 피드백**: 각 항목별 점수 및 개선 사항 제공
- **결과 저장**: 평가 결과를 JSON 형식으로 저장

## 설치

필요한 패키지는 프로젝트 루트의 `requirements.txt`에 포함되어 있습니다.

```bash
pip install langchain-google-genai langchain-core
```

## 환경 변수 설정

`.env` 파일에 Google API 키를 설정하세요:

```
GOOGLE_API_KEY=your_google_api_key_here
```

## 사용 방법

### 1. 기본 사용법

```python
from Evaluate.script_evaluator import ScriptEvaluator

# 평가자 초기화
evaluator = ScriptEvaluator()

# JSON 파일에서 스크립트 읽어서 평가
result = evaluator.evaluate_from_file("path/to/script.json", compare=True)

# 결과 출력
evaluator.print_evaluation_summary(result)

# 결과 저장
evaluator.save_evaluation_result(result)
```

### 2. 딕셔너리로 직접 평가

```python
from Evaluate.script_evaluator import ScriptEvaluator

# 평가할 스크립트 데이터
script_data = {
    "beginner": {
        "intro": "...",
        "turns": [
            {"speaker": "man", "text": "..."},
            {"speaker": "woman", "text": "..."}
        ],
        "outro": "..."
    },
    "intermediate": {...},
    "advanced": {...}
}

# 평가자 초기화
evaluator = ScriptEvaluator()

# 각 난이도별 평가
results = evaluator.evaluate_all_difficulties(script_data)

# 비교 평가
comparison = evaluator.compare_difficulties(script_data)
```

### 3. 단일 난이도만 평가

```python
from Evaluate.script_evaluator import ScriptEvaluator

# 초급 난이도 스크립트
beginner_script = {
    "intro": "...",
    "turns": [...],
    "outro": "..."
}

# 평가자 초기화
evaluator = ScriptEvaluator()

# 초급 난이도만 평가
result = evaluator.evaluate_single_difficulty(beginner_script, "beginner")
```

## 스크립트 데이터 형식

평가할 스크립트는 다음 JSON 형식을 따라야 합니다:

```json
{
  "beginner": {
    "intro": "인트로 텍스트",
    "turns": [
      {
        "speaker": "man",
        "text": "대화 내용"
      },
      {
        "speaker": "woman",
        "text": "대화 내용"
      }
    ],
    "outro": "아웃트로 텍스트"
  },
  "intermediate": {
    "intro": "...",
    "turns": [...],
    "outro": "..."
  },
  "advanced": {
    "intro": "...",
    "turns": [...],
    "outro": "..."
  }
}
```

## 평가 기준

### 초급 (Beginner)
- 간단하고 명확한 용어 사용
- 전문 용어 최소화 또는 쉬운 설명 포함
- 일상적인 비유와 예시 활용
- 짧고 명확한 문장 구조
- 친근하고 접근하기 쉬운 톤

### 중급 (Intermediate)
- 일부 전문 용어 사용 가능
- 기술적 개념에 대한 설명 포함
- 적절한 배경 지식 가정
- 균형잡힌 설명과 분석
- 전문적이면서도 이해하기 쉬운 톤

### 고급 (Advanced)
- 전문 용어와 기술적 개념 자유롭게 사용
- 심층적인 분석과 인사이트
- 고급 기술 개념에 대한 상세 설명
- 복잡한 문장 구조와 논리적 전개
- 전문가 수준의 톤과 표현

## 평가 결과 형식

평가 결과는 다음 형식으로 반환됩니다:

```json
{
  "status": "success",
  "data": {
    "individual_evaluations": {
      "beginner": {
        "status": "success",
        "data": {
          "difficulty_level": "beginner",
          "scores": {
            "difficulty_appropriateness": 8,
            "terminology_usage": 7,
            "clarity_of_explanation": 9,
            "tone_and_style": 8,
            "structure_and_flow": 8
          },
          "overall_score": 8,
          "is_appropriate": true,
          "evaluation": {
            "strengths": ["강점1", "강점2"],
            "weaknesses": ["약점1", "약점2"],
            "recommendations": ["개선사항1", "개선사항2"]
          },
          "detailed_feedback": "상세한 평가 의견"
        }
      },
      "intermediate": {...},
      "advanced": {...}
    },
    "comparison": {
      "status": "success",
      "data": {
        "evaluations": {
          "beginner": {...},
          "intermediate": {...},
          "advanced": {...}
        },
        "comparison": {
          "difficulty_distinction": 8,
          "overall_balance": 7,
          "recommendations": [...]
        },
        "overall_assessment": "종합 평가 의견"
      }
    }
  }
}
```

## 예제

자세한 사용 예제는 `example_usage.py` 파일을 참고하세요.

## 파일 구조

```
Evaluate/
├── __init__.py              # 모듈 초기화
├── script_evaluator.py      # 메인 평가 클래스
├── evaluation_criteria.py   # 평가 기준 정의
├── example_usage.py          # 사용 예제
└── README.md                # 이 파일
```

