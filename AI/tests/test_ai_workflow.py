"""
AI 워크플로우 테스트

AI 팟캐스트 생성 시스템의 주요 기능을 테스트하는 모듈
"""

import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 테스트를 위한 모듈 임포트
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ai_workflow import AIWorkflow
from modules.data_collection import NewsCollector
from modules.content_generation import ContentManager
from modules.audio_processing import AudioManager
from config.settings import AISettings


class TestAIWorkflow(unittest.TestCase):
    """AI 워크플로우 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_api_key = "test_perplexity_api_key"
        self.test_google_key = "test_google_api_key"
        
        # 테스트용 모의 데이터
        self.mock_news_data = {
            "category": "GOOGLE",
            "articles": [
                {
                    "news_url": "https://example.com/news1",
                    "title": "구글 AI 뉴스 1",
                    "text": "구글이 새로운 AI 모델을 발표했습니다. 이 모델은 기존 모델보다 성능이 향상되었습니다.",
                    "date": "2024-01-15"
                },
                {
                    "news_url": "https://example.com/news2", 
                    "title": "구글 AI 뉴스 2",
                    "text": "구글이 차세대 AI 기술에 대한 연구 결과를 공개했습니다. 이 기술은 미래 AI 발전에 큰 영향을 줄 것으로 예상됩니다.",
                    "date": "2024-01-15"
                }
            ]
        }
    
    def test_ai_workflow_initialization(self):
        """AI 워크플로우 초기화 테스트"""
        workflow = AIWorkflow(self.test_api_key)
        
        self.assertIsNotNone(workflow.news_collector)
        self.assertIsNotNone(workflow.content_manager)
        self.assertIsNotNone(workflow.audio_manager)
        self.assertIsNone(workflow.llm)  # Google API 키 없이 초기화
    
    def test_ai_workflow_with_google_api(self):
        """Google API 키와 함께 AI 워크플로우 초기화 테스트"""
        with patch('modules.ai_workflow.ChatGoogleGenerativeAI') as mock_llm:
            mock_llm.return_value = Mock()
            
            workflow = AIWorkflow(self.test_api_key, self.test_google_key)
            
            self.assertIsNotNone(workflow.news_collector)
            self.assertIsNotNone(workflow.content_manager)
            self.assertIsNotNone(workflow.audio_manager)
    
    @patch('modules.data_collection.NewsCollector.collect_news_by_category')
    def test_news_collection(self, mock_collect):
        """뉴스 수집 테스트"""
        mock_collect.return_value = self.mock_news_data
        
        workflow = AIWorkflow(self.test_api_key)
        result = workflow.news_collector.collect_news_by_category("GOOGLE")
        
        self.assertEqual(result["category"], "GOOGLE")
        self.assertEqual(len(result["articles"]), 2)
        mock_collect.assert_called_once_with("GOOGLE", "week")
    
    def test_content_generation_workflow(self):
        """콘텐츠 생성 워크플로우 테스트"""
        # 임시 JSON 파일 생성
        test_file = "temp_test_news.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(self.mock_news_data, f, ensure_ascii=False)
        
        try:
            workflow = AIWorkflow(self.test_api_key)
            
            # 콘텐츠 생성 테스트
            result = workflow.content_manager.run_complete_workflow(
                test_file, "GOOGLE", "김테크", "박AI"
            )
            
            # 결과 검증
            self.assertIsNotNone(result)
            self.assertEqual(result["category"], "GOOGLE")
            self.assertIn("report_file", result)
            self.assertIn("script_file", result)
            
        finally:
            # 임시 파일 정리
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_audio_processing_status(self):
        """오디오 처리 상태 테스트"""
        workflow = AIWorkflow(self.test_api_key)
        
        status = workflow.audio_manager.get_tts_status()
        
        self.assertIn("tts_available", status)
        self.assertIn("google_tts_available", status)
        self.assertIn("libraries_installed", status)
    
    def test_system_status(self):
        """시스템 상태 테스트"""
        workflow = AIWorkflow(self.test_api_key)
        
        status = workflow.get_system_status()
        
        self.assertIn("perplexity_api", status)
        self.assertIn("google_llm", status)
        self.assertIn("tts_system", status)
        self.assertIn("modules", status)
    
    def test_settings_validation(self):
        """설정 검증 테스트"""
        # 원래 설정 백업
        original_key = AISettings.PERPLEXITY_API_KEY
        
        try:
            # API 키 제거하여 검증 테스트
            AISettings.PERPLEXITY_API_KEY = ""
            
            validation = AISettings.validate_settings()
            
            self.assertFalse(validation["valid"])
            self.assertTrue(len(validation["errors"]) > 0)
            
        finally:
            # 원래 설정 복원
            AISettings.PERPLEXITY_API_KEY = original_key


class TestNewsCollector(unittest.TestCase):
    """뉴스 수집기 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_api_key = "test_api_key"
    
    @patch('modules.data_collection.requests.post')
    def test_collect_news_success(self, mock_post):
        """뉴스 수집 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps(self.mock_news_data)
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        collector = NewsCollector(self.test_api_key, "config/company_config.json")
        result = collector.collect_news_by_category("GOOGLE")
        
        self.assertEqual(result["category"], "GOOGLE")
        self.assertEqual(len(result["articles"]), 2)
    
    def test_collect_news_no_api_key(self):
        """API 키 없이 뉴스 수집 테스트"""
        with self.assertRaises(ValueError):
            NewsCollector("", "config/company_config.json")


class TestContentGeneration(unittest.TestCase):
    """콘텐츠 생성 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.mock_news_data = {
            "category": "GOOGLE",
            "articles": [
                {
                    "news_url": "https://example.com/news1",
                    "title": "구글 AI 뉴스",
                    "text": "구글의 새로운 AI 기술에 대한 내용입니다.",
                    "date": "2024-01-15"
                }
            ]
        }
    
    def test_report_generation(self):
        """보고서 생성 테스트"""
        from modules.content_generation import ReportGenerator
        
        generator = ReportGenerator()
        
        # 임시 파일 생성
        test_file = "temp_test_report.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(self.mock_news_data, f, ensure_ascii=False)
        
        try:
            report = generator.generate_comprehensive_report(test_file)
            
            self.assertIsNotNone(report)
            self.assertIn("GOOGLE", report)
            self.assertIn("종합 보고서", report)
            
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main()
