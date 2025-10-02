"""
콘텐츠 관리 모듈

보고서와 대본 생성 워크플로우를 관리하는 클래스
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .report_generator import ReportGenerator
from .script_generator import ScriptGenerator


class ContentManager:
    """콘텐츠 관리 클래스"""
    
    def __init__(self, llm=None):
        """
        ContentManager 초기화
        
        Args:
            llm: LangChain LLM 인스턴스 (선택사항)
        """
        self.llm = llm
        self.report_generator = ReportGenerator(llm)
        self.script_generator = ScriptGenerator(llm)
    
    def create_output_structure(self, category: str, date_str: Optional[str] = None) -> Dict[str, str]:
        """
        카테고리별 output 폴더 구조를 생성하는 메서드
        
        Args:
            category (str): 카테고리명
            date_str (Optional[str]): 날짜 문자열 (기본값: 오늘 날짜)
        
        Returns:
            Dict[str, str]: 생성된 폴더 경로들
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        
        # 카테고리명을 파일명에 적합하게 변환
        safe_category = category.replace("/", "_").replace(" ", "_")
        
        # 기본 경로 설정
        base_path = "data/output"
        category_path = os.path.join(base_path, f"{safe_category}_{date_str}")
        
        # 하위 폴더들 생성
        folders = {
            "base": base_path,
            "category": category_path,
            "reports": os.path.join(category_path, "reports"),
            "scripts": os.path.join(category_path, "scripts"),
            "audio": os.path.join(category_path, "audio"),
            "processed": os.path.join(category_path, "processed")
        }
        
        # 폴더들 생성
        for folder_name, folder_path in folders.items():
            os.makedirs(folder_path, exist_ok=True)
            print(f"{folder_name} 폴더 생성: {folder_path}")
        
        return folders
    
    def run_complete_workflow(self, json_file_path: str, category: str, 
                            host1_name: str = "김테크", host2_name: str = "박AI") -> Optional[Dict[str, Any]]:
        """
        JSON 파일부터 팟캐스트 대본까지 전체 워크플로우를 실행하는 메서드
        
        Args:
            json_file_path (str): JSON 파일 경로
            category (str): 카테고리명
            host1_name (str): 첫 번째 호스트 이름
            host2_name (str): 두 번째 호스트 이름
        
        Returns:
            Optional[Dict[str, Any]]: 생성된 파일 경로들과 결과 정보
        """
        print("통합 워크플로우 시작!")
        print(f"카테고리: {category}")
        print(f"진행자: {host1_name}, {host2_name}")
        print("-" * 50)
        
        # 폴더 구조 생성
        folders = self.create_output_structure(category)
        
        # 1단계: 종합 보고서 생성
        print("1단계: 종합 보고서 생성 중...")
        if self.llm:
            report_content = self.report_generator.generate_comprehensive_report_with_llm(json_file_path)
        else:
            report_content = self.report_generator.generate_comprehensive_report(json_file_path)
        
        if not report_content:
            print("보고서 생성에 실패했습니다.")
            return None
        
        # 보고서 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_category = category.replace("/", "_").replace(" ", "_")
        report_filename = f"{safe_category}_종합보고서_{timestamp}.md"
        report_file_path = os.path.join(folders['reports'], report_filename)
        
        with open(report_file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"보고서 생성 완료: {report_file_path}")
        
        # 2단계: 팟캐스트 대본 생성
        print("\n2단계: 팟캐스트 대본 생성 중...")
        script_content = self.script_generator.generate_podcast_script_from_md(
            report_file_path, host1_name, host2_name
        )
        
        if not script_content:
            print("대본 생성에 실패했습니다.")
            return None
        
        # 대본 저장
        script_filename = f"{safe_category}_팟캐스트_대본_{timestamp}.md"
        script_file_path = os.path.join(folders['scripts'], script_filename)
        
        with open(script_file_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"대본 생성 완료: {script_file_path}")
        
        print("\n워크플로우 완료!")
        print(f"보고서: {report_file_path}")
        print(f"대본: {script_file_path}")
        
        return {
            "category": category,
            "hosts": [host1_name, host2_name],
            "report_file": report_file_path,
            "script_file": script_file_path,
            "folders": folders,
            "timestamp": timestamp
        }
    
    def save_workflow_metadata(self, workflow_result: Dict[str, Any], output_dir: str = "data/output") -> Optional[str]:
        """
        워크플로우 실행 결과 메타데이터를 저장하는 메서드
        
        Args:
            workflow_result (Dict[str, Any]): 워크플로우 실행 결과
            output_dir (str): 출력 디렉토리
        
        Returns:
            Optional[str]: 저장된 메타데이터 파일 경로
        """
        try:
            metadata = {
                "workflow_info": {
                    "category": workflow_result["category"],
                    "hosts": workflow_result["hosts"],
                    "timestamp": workflow_result["timestamp"],
                    "created_at": datetime.now().isoformat()
                },
                "generated_files": {
                    "report_file": workflow_result["report_file"],
                    "script_file": workflow_result["script_file"]
                },
                "folder_structure": workflow_result["folders"]
            }
            
            # 메타데이터 파일 저장
            metadata_filename = f"{workflow_result['category'].replace('/', '_')}_metadata_{workflow_result['timestamp']}.json"
            metadata_filepath = os.path.join(output_dir, metadata_filename)
            
            with open(metadata_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"메타데이터가 저장되었습니다: {metadata_filepath}")
            return metadata_filepath
            
        except Exception as e:
            print(f"메타데이터 저장 중 오류 발생: {e}")
            return None
