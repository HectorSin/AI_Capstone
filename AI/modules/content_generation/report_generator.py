"""
보고서 생성 모듈

뉴스 데이터를 종합 보고서로 변환하는 클래스
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ReportGenerator:
    """보고서 생성 클래스"""
    
    def __init__(self, llm=None):
        """
        ReportGenerator 초기화
        
        Args:
            llm: LangChain LLM 인스턴스 (선택사항)
        """
        self.llm = llm
        
        # 보고서 템플릿 정의
        self.comprehensive_report_template = """# {category} 종합 보고서

## 요약
{summary}

## 주요 뉴스 내용
{detailed_content}

## 관련 뉴스 링크
{news_links}

---
**보고서 생성일**: {report_date}
**분석 기사 수**: {total_articles}개
"""

        self.summary_template = """{category} 분야에서 총 {total_articles}개의 주요 뉴스가 발표되었습니다. 주요 키워드는 {key_points} 등입니다."""

        self.detailed_content_template = """
### {title}
**발표일**: {date}
{content}

---
"""
    
    def generate_comprehensive_report(self, json_file_path: str) -> Optional[str]:
        """
        JSON 파일을 읽어서 종합 보고서를 생성하는 메서드 (템플릿 기반)
        
        Args:
            json_file_path (str): JSON 파일 경로
        
        Returns:
            Optional[str]: 생성된 종합 보고서 텍스트
        """
        try:
            # JSON 파일 읽기
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # 키 포인트 추출 (제목들로부터)
            key_points = ", ".join([article['title'] for article in data['articles'][:2]])
            if len(data['articles']) > 2:
                key_points += " 등"
            
            # 요약 생성
            summary = self.summary_template.format(
                category=data['category'],
                total_articles=len(data['articles']),
                key_points=key_points
            )
            
            # 상세 내용 생성 (모든 기사 내용을 하나로)
            detailed_content = ""
            for article in data['articles']:
                detailed_content += self.detailed_content_template.format(
                    title=article['title'],
                    date=article['date'],
                    content=article['text']
                )
            
            # 뉴스 링크 생성
            news_links = ""
            for i, article in enumerate(data['articles'], 1):
                news_links += f"{i}. [{article['title'][:50]}...]({article['news_url']})\\n"
            
            # 최종 종합 보고서 생성
            final_report = self.comprehensive_report_template.format(
                category=data['category'],
                summary=summary,
                detailed_content=detailed_content,
                news_links=news_links,
                report_date=datetime.now().strftime("%Y-%m-%d"),
                total_articles=len(data['articles'])
            )
            
            return final_report
            
        except Exception as e:
            print(f"보고서 생성 중 오류 발생: {e}")
            return None
    
    def generate_comprehensive_report_with_llm(self, json_file_path: str) -> Optional[str]:
        """
        LLM을 사용하여 종합 보고서를 생성하는 메서드
        
        Args:
            json_file_path (str): JSON 파일 경로
        
        Returns:
            Optional[str]: 생성된 종합 보고서 텍스트
        """
        if not self.llm:
            print("LLM이 설정되지 않았습니다. 템플릿 기반 보고서를 생성합니다.")
            return self.generate_comprehensive_report(json_file_path)
        
        try:
            # JSON 파일 읽기
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # 보고서 생성 프롬프트
            report_prompt = PromptTemplate(
                input_variables=["category", "articles_data"],
                template="""
다음 뉴스 기사들을 바탕으로 전문적이고 체계적인 종합 보고서를 작성해주세요.

**카테고리**: {category}

**뉴스 기사들**:
{articles_data}

**보고서 요구사항**:
1. 마크다운 형식으로 작성
2. 요약, 주요 내용, 분석 섹션 포함
3. 각 뉴스의 핵심 내용과 시사점 정리
4. 전문적이면서도 이해하기 쉬운 문체
5. 구조화된 형태로 정리

다음 형식을 따라 작성해주세요:

# [카테고리] 종합 보고서

## 요약
[전체적인 요약]

## 주요 뉴스 내용
### [뉴스 제목 1]
**발표일**: [날짜]
[내용 요약]

### [뉴스 제목 2]
**발표일**: [날짜]
[내용 요약]

## 종합 분석
[전체적인 분석과 시사점]

---
**보고서 생성일**: {report_date}
**분석 기사 수**: {total_articles}개
"""
            )
            
            # 기사 데이터를 문자열로 변환
            articles_text = ""
            for i, article in enumerate(data['articles'], 1):
                articles_text += f"""
{i}. 제목: {article['title']}
   날짜: {article['date']}
   내용: {article['text'][:500]}...
   URL: {article['news_url']}

"""
            
            # LLM 체인 생성
            chain = report_prompt | self.llm | StrOutputParser()
            
            # LLM으로 보고서 생성
            report_content = chain.invoke({
                "category": data['category'],
                "articles_data": articles_text,
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "total_articles": len(data['articles'])
            })
            
            return report_content
            
        except Exception as e:
            print(f"LLM 보고서 생성 중 오류 발생: {e}")
            print("API 키를 확인하거나 네트워크 연결을 확인해주세요.")
            return None
    
    def save_report(self, report_content: str, category: str, output_dir: str = "data/output") -> Optional[str]:
        """
        보고서를 파일로 저장하는 메서드
        
        Args:
            report_content (str): 보고서 내용
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
            filename = f"{safe_category}_종합보고서_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"보고서가 저장되었습니다: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"보고서 저장 중 오류 발생: {e}")
            return None
