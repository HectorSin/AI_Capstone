"""
팟캐스트 대본 생성 모듈

보고서를 바탕으로 2인 대화형 팟캐스트 대본을 생성하는 클래스
"""

import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ScriptGenerator:
    """팟캐스트 대본 생성 클래스"""
    
    def __init__(self, llm=None):
        """
        ScriptGenerator 초기화
        
        Args:
            llm: LangChain LLM 인스턴스 (선택사항)
        """
        self.llm = llm
    
    def generate_podcast_script_from_md(self, md_file_path: str, host1_name: str = "김테크", host2_name: str = "박AI") -> Optional[str]:
        """
        MD 보고서 파일을 읽어서 2인 대화형 팟캐스트 대본을 생성하는 메서드
        
        Args:
            md_file_path (str): MD 보고서 파일 경로
            host1_name (str): 첫 번째 호스트 이름
            host2_name (str): 두 번째 호스트 이름
        
        Returns:
            Optional[str]: 생성된 2인 대화형 팟캐스트 대본
        """
        if not self.llm:
            print("LLM이 설정되지 않았습니다.")
            return None
        
        try:
            # MD 파일 읽기
            with open(md_file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
            
            # 전체 팟캐스트 대본 생성 프롬프트
            full_script_prompt = PromptTemplate(
                input_variables=["md_content", "host1_name", "host2_name"],
                template="""
다음 뉴스 보고서를 바탕으로 2인 대화형 팟캐스트 대본을 생성해주세요.

**보고서 내용**:
{md_content}

**요구사항**:
1. 진행자: {host1_name}, {host2_name}
2. 자연스러운 대화 형식
3. 각 뉴스에 대한 흥미로운 의견과 분석 포함
4. 약 15분 분량
5. 인트로, 메인 콘텐츠, 심화 분석, 마무리 구조

**대본 형식**:
{host1_name}: (대사)
{host2_name}: (대사)

자연스럽고 흥미로운 팟캐스트 대본을 작성해주세요.
"""
            )
            
            # LLM 체인 생성
            chain = full_script_prompt | self.llm | StrOutputParser()
            
            # LLM으로 대본 생성
            script_content = chain.invoke({
                "md_content": md_content,
                "host1_name": host1_name,
                "host2_name": host2_name
            })
            
            # 에피소드 정보 추가
            episode_info = f"""# AI 생성 팟캐스트 대본 (2인 대화형)

## 📻 에피소드 정보
- **제목**: IT/기술 분야 최신 동향 - {datetime.now().strftime('%m월 %d일')} 뉴스
- **날짜**: {datetime.now().strftime('%Y년 %m월 %d일')}
- **주제**: IT/기술 분야 최신 동향
- **진행자**: {host1_name}, {host2_name}
- **소요 시간**: 약 15분
- **생성 방식**: AI 모델 (Gemini-1.5-flash)

---

{script_content}

---

## 방송 노트
**생성 정보**:
- 생성일: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- AI 모델: Gemini-1.5-flash
- 진행자: {host1_name}, {host2_name}
- 원본 보고서: {md_file_path}
"""
            
            return episode_info
            
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            print("API 키를 확인하거나 네트워크 연결을 확인해주세요.")
            return None
    
    def parse_podcast_script(self, script_content: str) -> List[Dict[str, str]]:
        """
        팟캐스트 대본을 파싱하여 대화별로 분리하는 메서드
        
        Args:
            script_content (str): 팟캐스트 대본 내용
        
        Returns:
            List[Dict[str, str]]: 대화 리스트 [{"speaker": "김테크", "text": "대사 내용"}, ...]
        """
        
        # 대본에서 실제 대화 부분만 추출
        lines = script_content.split('\n')
        dialogues = []
        
        # 대화 패턴 찾기 (진행자: 대사)
        dialogue_pattern = r'^(김테크|박AI):\s*(.+)$'
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('**') and not line.startswith('---'):
                match = re.match(dialogue_pattern, line)
                if match:
                    speaker = match.group(1)
                    text = match.group(2).strip()
                    if text:
                        dialogues.append({
                            "speaker": speaker,
                            "text": text
                        })
        
        print(f"총 {len(dialogues)}개의 대화를 찾았습니다.")
        return dialogues
    
    def save_script(self, script_content: str, category: str, output_dir: str = "data/output") -> Optional[str]:
        """
        팟캐스트 대본을 파일로 저장하는 메서드
        
        Args:
            script_content (str): 대본 내용
            category (str): 카테고리명
            output_dir (str): 출력 디렉토리
        
        Returns:
            Optional[str]: 저장된 파일 경로
        """
        try:
            # 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_category = category.replace("/", "_").replace(" ", "_")
            filename = f"{safe_category}_팟캐스트_대본_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"팟캐스트 대본이 저장되었습니다: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"대본 저장 중 오류 발생: {e}")
            return None
