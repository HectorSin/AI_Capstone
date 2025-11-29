"""
팟캐스트 스크립트 평가 클래스

Gemini API를 사용하여 난이도별 팟캐스트 스크립트를 평가합니다.
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from .evaluation_criteria import EvaluationCriteria

# config.settings를 import하려면 상대 경로 또는 절대 경로 사용
try:
    from config.settings import AISettings
except ImportError:
    # 상대 경로로 시도
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.settings import AISettings


class ScriptEvaluator:
    """팟캐스트 스크립트 평가 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        """
        ScriptEvaluator 초기화
        
        Args:
            api_key: Google API 키 (None이면 환경변수에서 가져옴)
            model_name: 사용할 Gemini 모델명
        """
        self.api_key = api_key or AISettings.GOOGLE_API_KEY
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("Google API 키가 필요합니다. 환경변수 GOOGLE_API_KEY를 설정하거나 api_key 파라미터를 제공해주세요.")
        
        # Gemini 모델 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.3,  # 평가는 일관성이 중요하므로 낮은 temperature
            google_api_key=self.api_key
        )
        
        # JSON 파서 초기화
        self.json_parser = JsonOutputParser()
        
        # 평가 기준 초기화
        self.criteria = EvaluationCriteria()
    
    def evaluate_single_difficulty(
        self, 
        script_data: Dict[str, Any], 
        difficulty: str
    ) -> Dict[str, Any]:
        """
        단일 난이도 스크립트 평가
        
        Args:
            script_data: 평가할 스크립트 데이터 (intro, turns, outro 포함)
            difficulty: 평가할 난이도 (beginner, intermediate, advanced)
        
        Returns:
            Dict[str, Any]: 평가 결과
        """
        try:
            # 평가 프롬프트 생성
            prompt_text = self.criteria.get_evaluation_prompt(script_data, difficulty)
            
            # 프롬프트 템플릿 생성
            prompt = PromptTemplate(
                template="{prompt}",
                input_variables=["prompt"]
            )
            
            # LLM 체인 생성
            chain = prompt | self.llm
            
            # 평가 실행
            response = chain.invoke({"prompt": prompt_text})
            
            # 응답 파싱
            response_text = response.content if hasattr(response, "content") else str(response)
            
            # JSON 추출 시도
            try:
                # JSON 부분만 추출 (마크다운 코드 블록 제거)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                evaluation_result = json.loads(response_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트로 반환
                evaluation_result = {
                    "error": "JSON 파싱 실패",
                    "raw_response": response_text
                }
            
            # 메타데이터 추가
            evaluation_result["evaluated_at"] = datetime.now().isoformat()
            evaluation_result["difficulty"] = difficulty
            evaluation_result["model"] = self.model_name
            
            return {
                "status": "success",
                "data": evaluation_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "difficulty": difficulty
            }
    
    def evaluate_all_difficulties(
        self, 
        script_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        세 가지 난이도 모두 평가
        
        Args:
            script_data: 세 가지 난이도가 모두 포함된 스크립트 데이터
                {
                    "beginner": {...},
                    "intermediate": {...},
                    "advanced": {...}
                }
        
        Returns:
            Dict[str, Any]: 각 난이도별 평가 결과
        """
        results = {}
        
        # 각 난이도별로 평가
        for difficulty in ["beginner", "intermediate", "advanced"]:
            if difficulty in script_data:
                print(f"📊 {difficulty} 난이도 평가 중...")
                results[difficulty] = self.evaluate_single_difficulty(
                    script_data[difficulty], 
                    difficulty
                )
            else:
                results[difficulty] = {
                    "status": "error",
                    "error": f"{difficulty} 난이도 스크립트가 없습니다."
                }
        
        return results
    
    def compare_difficulties(
        self, 
        script_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        세 가지 난이도를 비교 평가
        
        Args:
            script_data: 세 가지 난이도가 모두 포함된 스크립트 데이터
        
        Returns:
            Dict[str, Any]: 비교 평가 결과
        """
        try:
            # 비교 평가 프롬프트 생성
            prompt_text = self.criteria.get_comparison_prompt(script_data)
            
            # 프롬프트 템플릿 생성
            prompt = PromptTemplate(
                template="{prompt}",
                input_variables=["prompt"]
            )
            
            # LLM 체인 생성
            chain = prompt | self.llm
            
            # 평가 실행
            response = chain.invoke({"prompt": prompt_text})
            
            # 응답 파싱
            response_text = response.content if hasattr(response, "content") else str(response)
            
            # JSON 추출 시도
            try:
                # JSON 부분만 추출
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                comparison_result = json.loads(response_text)
            except json.JSONDecodeError:
                comparison_result = {
                    "error": "JSON 파싱 실패",
                    "raw_response": response_text
                }
            
            # 메타데이터 추가
            comparison_result["evaluated_at"] = datetime.now().isoformat()
            comparison_result["model"] = self.model_name
            
            return {
                "status": "success",
                "data": comparison_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def find_script_files(
        self, 
        base_path: str = "/app/podcasts",
        podcast_id: Optional[str] = None
    ) -> List[str]:
        """
        스크립트 파일을 찾는 메서드
        
        Args:
            base_path: 팟캐스트 저장 기본 경로 (Back 서비스: /app/podcasts, 로컬: 상대 경로)
            podcast_id: 특정 팟캐스트 ID (None이면 모든 팟캐스트 검색)
        
        Returns:
            List[str]: 찾은 스크립트 파일 경로 리스트
        """
        script_files = []
        
        try:
            if podcast_id:
                # 특정 팟캐스트 ID의 스크립트만 찾기
                scripts_dir = os.path.join(base_path, podcast_id, "04_scripts")
                if os.path.exists(scripts_dir):
                    for filename in os.listdir(scripts_dir):
                        if filename.startswith("script_") and filename.endswith(".json"):
                            script_files.append(os.path.join(scripts_dir, filename))
            else:
                # 모든 팟캐스트의 스크립트 찾기
                if os.path.exists(base_path):
                    for podcast_dir in os.listdir(base_path):
                        podcast_path = os.path.join(base_path, podcast_dir)
                        if os.path.isdir(podcast_path):
                            scripts_dir = os.path.join(podcast_path, "04_scripts")
                            if os.path.exists(scripts_dir):
                                for filename in os.listdir(scripts_dir):
                                    if filename.startswith("script_") and filename.endswith(".json"):
                                        script_files.append(os.path.join(scripts_dir, filename))
            
            # 경로 정렬 (최신 파일 먼저)
            script_files.sort(reverse=True)
            
        except Exception as e:
            print(f"⚠️ 스크립트 파일 검색 중 오류: {e}")
        
        return script_files
    
    def evaluate_from_file(
        self, 
        file_path: str, 
        compare: bool = True
    ) -> Dict[str, Any]:
        """
        JSON 파일에서 스크립트를 읽어서 평가
        
        Args:
            file_path: JSON 파일 경로
            compare: True면 비교 평가도 수행
        
        Returns:
            Dict[str, Any]: 평가 결과
        """
        try:
            # JSON 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # 개별 평가
            individual_results = self.evaluate_all_difficulties(script_data)
            
            result = {
                "file_path": file_path,
                "individual_evaluations": individual_results
            }
            
            # 비교 평가
            if compare:
                print("📊 난이도 간 비교 평가 중...")
                comparison_result = self.compare_difficulties(script_data)
                result["comparison"] = comparison_result
            
            return {
                "status": "success",
                "data": result
            }
            
        except FileNotFoundError:
            return {
                "status": "error",
                "error": f"파일을 찾을 수 없습니다: {file_path}"
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"JSON 파싱 오류: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def evaluate_from_podcast_service(
        self,
        base_path: str = "/app/podcasts",
        podcast_id: Optional[str] = None,
        script_index: Optional[int] = None,
        compare: bool = True
    ) -> Dict[str, Any]:
        """
        Back 서비스에서 생성된 스크립트 파일을 찾아서 평가
        
        Args:
            base_path: 팟캐스트 저장 기본 경로
            podcast_id: 특정 팟캐스트 ID (None이면 최신 팟캐스트 사용)
            script_index: 특정 스크립트 인덱스 (None이면 첫 번째 스크립트 사용)
            compare: True면 비교 평가도 수행
        
        Returns:
            Dict[str, Any]: 평가 결과
        """
        try:
            # 스크립트 파일 찾기
            if podcast_id and script_index is not None:
                # 특정 파일 경로 구성
                file_path = os.path.join(base_path, podcast_id, "04_scripts", f"script_{script_index}.json")
                if not os.path.exists(file_path):
                    return {
                        "status": "error",
                        "error": f"파일을 찾을 수 없습니다: {file_path}"
                    }
                script_files = [file_path]
            else:
                # 자동으로 파일 찾기
                script_files = self.find_script_files(base_path, podcast_id)
                if not script_files:
                    return {
                        "status": "error",
                        "error": f"스크립트 파일을 찾을 수 없습니다. 경로: {base_path}"
                    }
            
            # 첫 번째 스크립트 파일 사용
            file_path = script_files[0]
            print(f"📂 평가할 파일: {file_path}")
            
            # 파일에서 평가
            return self.evaluate_from_file(file_path, compare)
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def save_evaluation_result(
        self, 
        evaluation_result: Dict[str, Any], 
        output_dir: str = "data/output/evaluations"
    ) -> Optional[str]:
        """
        평가 결과를 파일로 저장
        
        Args:
            evaluation_result: 평가 결과
            output_dir: 출력 디렉토리
        
        Returns:
            Optional[str]: 저장된 파일 경로
        """
        try:
            # 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 평가 결과가 저장되었습니다: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 평가 결과 저장 중 오류 발생: {e}")
            return None
    
    def print_evaluation_summary(self, evaluation_result: Dict[str, Any]):
        """
        평가 결과 요약 출력
        
        Args:
            evaluation_result: 평가 결과
        """
        if evaluation_result.get("status") != "success":
            print(f"❌ 평가 실패: {evaluation_result.get('error', '알 수 없는 오류')}")
            return
        
        data = evaluation_result.get("data", {})
        individual = data.get("individual_evaluations", {})
        
        print("\n" + "="*60)
        print("📊 팟캐스트 스크립트 평가 결과")
        print("="*60)
        
        # 각 난이도별 평가 결과
        for difficulty in ["beginner", "intermediate", "advanced"]:
            if difficulty in individual:
                result = individual[difficulty]
                if result.get("status") == "success":
                    eval_data = result.get("data", {})
                    score = eval_data.get("overall_score", "N/A")
                    is_appropriate = eval_data.get("is_appropriate", False)
                    status_icon = "✅" if is_appropriate else "⚠️"
                    
                    print(f"\n{difficulty.upper()} 난이도:")
                    print(f"  {status_icon} 종합 점수: {score}/10")
                    print(f"  적합성: {'적합' if is_appropriate else '부적합'}")
                    
                    scores = eval_data.get("scores", {})
                    if scores:
                        print(f"  - 난이도 적합성: {scores.get('difficulty_appropriateness', 'N/A')}/10")
                        print(f"  - 용어 사용: {scores.get('terminology_usage', 'N/A')}/10")
                        print(f"  - 설명 명확성: {scores.get('clarity_of_explanation', 'N/A')}/10")
                        print(f"  - 톤과 스타일: {scores.get('tone_and_style', 'N/A')}/10")
                        print(f"  - 구조와 흐름: {scores.get('structure_and_flow', 'N/A')}/10")
                else:
                    print(f"\n{difficulty.upper()} 난이도: ❌ 평가 실패 - {result.get('error', '알 수 없는 오류')}")
        
        # 비교 평가 결과
        comparison = data.get("comparison", {})
        if comparison.get("status") == "success":
            comp_data = comparison.get("data", {})
            print(f"\n📈 난이도 간 비교:")
            print(f"  - 난이도 구분: {comp_data.get('comparison', {}).get('difficulty_distinction', 'N/A')}/10")
            print(f"  - 전체 균형: {comp_data.get('comparison', {}).get('overall_balance', 'N/A')}/10")
        
        print("\n" + "="*60)

