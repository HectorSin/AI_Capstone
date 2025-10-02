"""
AI 워크플로우 메인 클래스

전체 AI 팟캐스트 생성 워크플로우를 관리하는 클래스
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .data_collection import NewsCollector
from .content_generation import ContentManager
from .audio_processing import AudioManager


class AIWorkflow:
    """AI 워크플로우 메인 클래스"""
    
    def __init__(self, 
                 perplexity_api_key: str,
                 google_api_key: Optional[str] = None,
                 naver_clova_client_id: Optional[str] = None,
                 naver_clova_client_secret: Optional[str] = None,
                 config_path: str = "config/company_config.json"):
        """
        AIWorkflow 초기화
        
        Args:
            perplexity_api_key (str): Perplexity API 키
            google_api_key (Optional[str]): Google API 키 (LLM용)
            naver_clova_client_id (Optional[str]): 네이버 클로바 TTS 클라이언트 ID
            naver_clova_client_secret (Optional[str]): 네이버 클로바 TTS 클라이언트 시크릿
            config_path (str): 회사 설정 파일 경로
        """
        # 데이터 수집 초기화
        self.news_collector = NewsCollector(perplexity_api_key, config_path)
        
        # LLM 초기화 (Google API 키가 있는 경우)
        self.llm = None
        if google_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.7,
                    google_api_key=google_api_key
                )
                print("Google LLM 초기화 완료")
            except ImportError:
                print("langchain_google_genai 라이브러리가 설치되지 않았습니다.")
            except Exception as e:
                print(f"Google LLM 초기화 실패: {e}")
        
        # 콘텐츠 생성 관리자 초기화
        self.content_manager = ContentManager(self.llm)
        
        # 오디오 관리자 초기화 (네이버 클로바 TTS)
        self.audio_manager = AudioManager(naver_clova_client_id, naver_clova_client_secret)
    
    def run_complete_workflow(self, 
                            category: str,
                            host1_name: str = "김테크",
                            host2_name: str = "박AI",
                            search_recency: str = "week",
                            include_audio: bool = True,
                            output_dir: str = "data/output") -> Optional[Dict[str, Any]]:
        """
        완전한 AI 팟캐스트 생성 워크플로우 실행
        
        Args:
            category (str): 뉴스 카테고리
            host1_name (str): 첫 번째 호스트 이름
            host2_name (str): 두 번째 호스트 이름
            search_recency (str): 검색 기간 필터
            include_audio (bool): 오디오 생성 포함 여부
            output_dir (str): 출력 디렉토리
        
        Returns:
            Optional[Dict[str, Any]]: 생성된 파일들과 결과 정보
        """
        print("AI 팟캐스트 생성 워크플로우 시작!")
        print(f"카테고리: {category}")
        print(f"진행자: {host1_name}, {host2_name}")
        print(f"검색 기간: {search_recency}")
        print(f"오디오 포함: {include_audio}")
        print("=" * 60)
        
        try:
            # 1단계: 뉴스 수집
            print("\n1단계: 뉴스 수집 중...")
            news_result = self.news_collector.collect_news_by_category(category, search_recency)
            
            if "error" in news_result:
                print(f"뉴스 수집 실패: {news_result['error']}")
                return None
            
            # 뉴스 데이터를 임시 파일로 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_category = category.replace("/", "_").replace(" ", "_")
            temp_news_file = os.path.join(output_dir, f"temp_{safe_category}_news_{timestamp}.json")
            
            os.makedirs(output_dir, exist_ok=True)
            with open(temp_news_file, 'w', encoding='utf-8') as f:
                json.dump(news_result, f, ensure_ascii=False, indent=2)
            
            print(f"뉴스 수집 완료: {len(news_result.get('articles', []))}개 기사")
            print(f"📄 임시 파일: {temp_news_file}")
            
            # 2단계: 콘텐츠 생성 (보고서 + 대본)
            print("\n2단계: 콘텐츠 생성 중...")
            content_result = self.content_manager.run_complete_workflow(
                temp_news_file, category, host1_name, host2_name
            )
            
            if not content_result:
                print("콘텐츠 생성 실패")
                return None
            
            print("콘텐츠 생성 완료")
            
            # 3단계: 오디오 생성 (선택사항)
            audio_result = None
            if include_audio and self.audio_manager.is_tts_available():
                print("\n3단계: 오디오 생성 중...")
                audio_result = self.audio_manager.create_audio_workflow(
                    content_result["script_file"], category
                )
                
                if audio_result:
                    print("오디오 생성 완료")
                else:
                    print("오디오 생성 실패")
            elif include_audio:
                print("\n3단계: 오디오 생성 건너뜀 (TTS 설정 필요)")
            
            # 임시 파일 정리
            if os.path.exists(temp_news_file):
                os.remove(temp_news_file)
            
            # 최종 결과 구성
            final_result = {
                "category": category,
                "hosts": [host1_name, host2_name],
                "search_recency": search_recency,
                "created_at": datetime.now().isoformat(),
                "files": {
                    "news_data": news_result,
                    "report_file": content_result["report_file"],
                    "script_file": content_result["script_file"]
                },
                "folders": content_result["folders"],
                "workflow_info": {
                    "total_articles": len(news_result.get('articles', [])),
                    "has_audio": audio_result is not None
                }
            }
            
            if audio_result:
                final_result["files"]["audio_file"] = audio_result["audio_file"]
                final_result["workflow_info"]["audio_size_mb"] = audio_result["file_size_mb"]
            
            # 메타데이터 저장
            self._save_workflow_metadata(final_result)
            
            print("\nAI 팟캐스트 생성 워크플로우 완료!")
            print("=" * 60)
            print("생성된 파일들:")
            print(f"  보고서: {content_result['report_file']}")
            print(f"  대본: {content_result['script_file']}")
            if audio_result:
                print(f"  음성: {audio_result['audio_file']}")
            print("=" * 60)
            
            return final_result
            
        except Exception as e:
            print(f"워크플로우 실행 중 오류 발생: {e}")
            return None
    
    def run_multiple_categories(self, 
                               categories: List[str],
                               host1_name: str = "김테크",
                               host2_name: str = "박AI",
                               search_recency: str = "week",
                               include_audio: bool = True,
                               output_dir: str = "data/output") -> Dict[str, Any]:
        """
        여러 카테고리의 팟캐스트를 일괄 생성하는 메서드
        
        Args:
            categories (List[str]): 카테고리 목록
            host1_name (str): 첫 번째 호스트 이름
            host2_name (str): 두 번째 호스트 이름
            search_recency (str): 검색 기간 필터
            include_audio (bool): 오디오 생성 포함 여부
            output_dir (str): 출력 디렉토리
        
        Returns:
            Dict[str, Any]: 카테고리별 생성 결과
        """
        print(f"다중 카테고리 팟캐스트 생성 시작!")
        print(f"카테고리: {', '.join(categories)}")
        print(f"진행자: {host1_name}, {host2_name}")
        print("=" * 60)
        
        results = {}
        
        for category in categories:
            print(f"\n{category} 처리 중...")
            result = self.run_complete_workflow(
                category, host1_name, host2_name, search_recency, include_audio, output_dir
            )
            results[category] = result
            
            if result:
                print(f"{category} 완료")
            else:
                print(f"{category} 실패")
        
        # 전체 결과 요약
        successful = sum(1 for r in results.values() if r is not None)
        print(f"\n전체 결과: {successful}/{len(categories)}개 카테고리 성공")
        
        return results
    
    def _save_workflow_metadata(self, workflow_result: Dict[str, Any]) -> Optional[str]:
        """
        워크플로우 실행 결과 메타데이터를 저장하는 메서드
        
        Args:
            workflow_result (Dict[str, Any]): 워크플로우 실행 결과
        
        Returns:
            Optional[str]: 저장된 메타데이터 파일 경로
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_category = workflow_result["category"].replace("/", "_").replace(" ", "_")
            metadata_filename = f"{safe_category}_workflow_metadata_{timestamp}.json"
            
            # 메타데이터를 상위 디렉토리에 저장
            output_dir = os.path.dirname(workflow_result["folders"]["category"])
            metadata_filepath = os.path.join(output_dir, metadata_filename)
            
            with open(metadata_filepath, 'w', encoding='utf-8') as f:
                json.dump(workflow_result, f, ensure_ascii=False, indent=2)
            
            print(f"워크플로우 메타데이터 저장: {metadata_filepath}")
            return metadata_filepath
            
        except Exception as e:
            print(f"메타데이터 저장 중 오류 발생: {e}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        시스템 상태 정보 반환
        
        Returns:
            Dict[str, Any]: 시스템 상태 정보
        """
        return {
            "perplexity_api": "설정됨",
            "google_llm": "설정됨" if self.llm else "미설정",
            "tts_system": self.audio_manager.get_tts_status(),
            "config_file": self.news_collector.config_path,
            "modules": {
                "news_collector": "활성화",
                "content_manager": "활성화",
                "audio_manager": "활성화" if self.audio_manager.is_tts_available() else "TTS 미설정"
            }
        }
