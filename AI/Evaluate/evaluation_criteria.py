"""
평가 기준 정의 모듈

팟캐스트 스크립트 평가를 위한 기준과 프롬프트를 정의합니다.
"""

from typing import Dict, Any


class EvaluationCriteria:
    """팟캐스트 스크립트 평가 기준 클래스"""
    
    # 난이도별 평가 기준
    DIFFICULTY_CRITERIA = {
        "beginner": {
            "name": "초급",
            "description": "일반인도 쉽게 이해할 수 있는 수준",
            "characteristics": [
                "간단하고 명확한 용어 사용",
                "전문 용어 최소화 또는 쉬운 설명 포함",
                "일상적인 비유와 예시 활용",
                "짧고 명확한 문장 구조",
                "친근하고 접근하기 쉬운 톤"
            ]
        },
        "intermediate": {
            "name": "중급",
            "description": "기본 지식이 있는 사람을 대상으로 한 수준",
            "characteristics": [
                "일부 전문 용어 사용 가능",
                "기술적 개념에 대한 설명 포함",
                "적절한 배경 지식 가정",
                "균형잡힌 설명과 분석",
                "전문적이면서도 이해하기 쉬운 톤"
            ]
        },
        "advanced": {
            "name": "고급",
            "description": "전문가 수준의 깊이 있는 내용",
            "characteristics": [
                "전문 용어와 기술적 개념 자유롭게 사용",
                "심층적인 분석과 인사이트",
                "고급 기술 개념에 대한 상세 설명",
                "복잡한 문장 구조와 논리적 전개",
                "전문가 수준의 톤과 표현"
            ]
        }
    }
    
    @classmethod
    def get_evaluation_prompt(cls, script_data: Dict[str, Any], difficulty: str) -> str:
        """
        평가를 위한 프롬프트 생성
        
        Args:
            script_data: 평가할 스크립트 데이터 (intro, turns, outro 포함)
            difficulty: 평가할 난이도 (beginner, intermediate, advanced)
        
        Returns:
            str: 평가 프롬프트
        """
        criteria = cls.DIFFICULTY_CRITERIA.get(difficulty, {})
        criteria_name = criteria.get("name", difficulty)
        criteria_desc = criteria.get("description", "")
        characteristics = criteria.get("characteristics", [])
        
        # 스크립트 내용 추출
        intro = script_data.get("intro", "")
        turns = script_data.get("turns", [])
        outro = script_data.get("outro", "")
        
        # 대화 내용 정리
        dialogue_text = ""
        for turn in turns:
            speaker = turn.get("speaker", "unknown")
            text = turn.get("text", "")
            dialogue_text += f"{speaker}: {text}\n\n"
        
        prompt = f"""다음은 {criteria_name} 난이도로 작성된 팟캐스트 스크립트입니다. 
이 스크립트가 {criteria_name} 난이도에 적합한지 평가해주세요.

## 평가 기준
**난이도**: {criteria_name} ({criteria_desc})

**특징**:
{chr(10).join(f"- {char}" for char in characteristics)}

## 평가할 스크립트

**인트로**:
{intro}

**대화 내용**:
{dialogue_text}

**아웃트로**:
{outro}

## 평가 요청사항

다음 항목들을 평가하고 JSON 형식으로 응답해주세요:

1. **난이도 적합성** (1-10점): 이 스크립트가 {criteria_name} 난이도에 얼마나 적합한가요?
2. **용어 사용**: 전문 용어 사용이 난이도에 적절한가요?
3. **설명의 명확성**: 개념 설명이 해당 난이도 수준의 청자에게 이해하기 쉬운가요?
4. **톤과 스타일**: 톤이 난이도에 맞는가요?
5. **구조와 흐름**: 스크립트의 구조와 논리적 흐름이 적절한가요?
6. **전체 평가**: 종합적으로 이 스크립트가 {criteria_name} 난이도에 적합한가요?

다음 JSON 형식으로 응답해주세요:
{{
    "difficulty_level": "{difficulty}",
    "scores": {{
        "difficulty_appropriateness": <1-10점>,
        "terminology_usage": <1-10점>,
        "clarity_of_explanation": <1-10점>,
        "tone_and_style": <1-10점>,
        "structure_and_flow": <1-10점>
    }},
    "overall_score": <1-10점>,
    "evaluation": {{
        "strengths": ["강점1", "강점2", ...],
        "weaknesses": ["약점1", "약점2", ...],
        "recommendations": ["개선사항1", "개선사항2", ...]
    }},
    "is_appropriate": <true/false>,
    "detailed_feedback": "상세한 평가 의견"
}}
"""
        return prompt
    
    @classmethod
    def get_comparison_prompt(cls, script_data: Dict[str, Any]) -> str:
        """
        세 가지 난이도를 비교 평가하는 프롬프트 생성
        
        Args:
            script_data: 세 가지 난이도가 모두 포함된 스크립트 데이터
        
        Returns:
            str: 비교 평가 프롬프트
        """
        beginner = script_data.get("beginner", {})
        intermediate = script_data.get("intermediate", {})
        advanced = script_data.get("advanced", {})
        
        prompt = f"""다음은 세 가지 난이도(초급, 중급, 고급)로 작성된 팟캐스트 스크립트입니다.
각 난이도별 스크립트가 해당 난이도에 적합한지 평가하고, 세 난이도 간의 차이와 적절성을 비교 평가해주세요.

## 초급 난이도 스크립트

**인트로**:
{beginner.get("intro", "")}

**대화 내용**:
{chr(10).join(f"{turn.get('speaker', '')}: {turn.get('text', '')}" for turn in beginner.get("turns", []))}

**아웃트로**:
{beginner.get("outro", "")}

---

## 중급 난이도 스크립트

**인트로**:
{intermediate.get("intro", "")}

**대화 내용**:
{chr(10).join(f"{turn.get('speaker', '')}: {turn.get('text', '')}" for turn in intermediate.get("turns", []))}

**아웃트로**:
{intermediate.get("outro", "")}

---

## 고급 난이도 스크립트

**인트로**:
{advanced.get("intro", "")}

**대화 내용**:
{chr(10).join(f"{turn.get('speaker', '')}: {turn.get('text', '')}" for turn in advanced.get("turns", []))}

**아웃트로**:
{advanced.get("outro", "")}

---

## 평가 요청사항

각 난이도별로 다음을 평가하고, 세 난이도 간의 차이와 적절성을 비교 평가해주세요:

1. **각 난이도의 적합성**: 각 스크립트가 해당 난이도에 얼마나 적합한가요?
2. **난이도 간 차이**: 세 난이도 간에 명확한 차이가 있나요?
3. **용어 사용의 적절성**: 각 난이도에서 사용된 용어가 적절한가요?
4. **전체적인 균형**: 세 난이도가 적절하게 구분되어 있나요?

다음 JSON 형식으로 응답해주세요:
{{
    "evaluations": {{
        "beginner": {{
            "score": <1-10점>,
            "is_appropriate": <true/false>,
            "feedback": "평가 의견"
        }},
        "intermediate": {{
            "score": <1-10점>,
            "is_appropriate": <true/false>,
            "feedback": "평가 의견"
        }},
        "advanced": {{
            "score": <1-10점>,
            "is_appropriate": <true/false>,
            "feedback": "평가 의견"
        }}
    }},
    "comparison": {{
        "difficulty_distinction": <1-10점>,
        "overall_balance": <1-10점>,
        "recommendations": ["개선사항1", "개선사항2", ...]
    }},
    "overall_assessment": "종합 평가 의견"
}}
"""
        return prompt

