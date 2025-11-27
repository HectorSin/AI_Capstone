"""
웹 페이지 크롤링 서비스

BeautifulSoup을 사용하여 기사 원문을 크롤링합니다.
"""

import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel, validator, ValidationError

logger = logging.getLogger(__name__)


class CrawledArticle(BaseModel):
    """크롤링된 기사 데이터 모델 (Pydantic 검증)"""
    success: bool
    url: str
    title: str
    content: str
    content_length: int
    error: Optional[str] = None

    @validator('url')
    def validate_url(cls, v):
        if not v.startswith('http'):
            raise ValueError('URL must start with http or https')
        return v

    @validator('content')
    def validate_content(cls, v, values):
        if values.get('success') and not v:
            raise ValueError('Successful crawl must have content')
        return v

    @validator('content_length')
    def validate_content_length(cls, v, values):
        if values.get('success') and v == 0:
            raise ValueError('Successful crawl must have content_length > 0')
        return v


class WebCrawlerService:
    """웹 페이지 크롤링 서비스"""

    def __init__(self, timeout: int = 10):
        """
        Args:
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.timeout = timeout

    async def crawl_article(self, url: str) -> Dict[str, Any]:
        """
        주어진 URL에서 기사 내용을 크롤링

        Args:
            url: 크롤링할 기사 URL

        Returns:
            {
                'success': bool,
                'url': str,
                'title': str,
                'content': str,
                'content_length': int,
                'error': Optional[str]
            }
        """
        try:
            # HTTP 요청
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                response.raise_for_status()

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # 제목 추출
            title = ''
            title_tag = soup.find('h1')
            if title_tag:
                title = title_tag.get_text(strip=True)
            elif soup.find('title'):
                title = soup.find('title').get_text(strip=True)

            # 본문 추출 (일반적인 뉴스 사이트 패턴)
            content = ''

            # 방법 1: article 태그
            article = soup.find('article')
            if article:
                # script, style 태그 제거
                for tag in article.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                content = article.get_text(separator='\n', strip=True)

            # 방법 2: main 태그
            if not content:
                main = soup.find('main')
                if main:
                    for tag in main.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    content = main.get_text(separator='\n', strip=True)

            # 방법 3: p 태그 모음
            if not content:
                paragraphs = soup.find_all('p')
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

            # 빈 줄 정리
            content = '\n'.join([line for line in content.split('\n') if line.strip()])

            if not content:
                error_data = {
                    'success': False,
                    'url': url,
                    'title': title,
                    'content': '',
                    'content_length': 0,
                    'error': '본문을 찾을 수 없습니다'
                }
                try:
                    validated = CrawledArticle(**error_data)
                    return validated.model_dump()
                except ValidationError:
                    return error_data

            # Pydantic 검증
            try:
                validated = CrawledArticle(
                    success=True,
                    url=url,
                    title=title or 'Untitled',
                    content=content,
                    content_length=len(content),
                    error=None
                )
                return validated.model_dump()
            except ValidationError as e:
                logger.error(f"크롤링 데이터 검증 실패: {e}")
                return {
                    'success': False,
                    'url': url,
                    'title': title or '',
                    'content': '',
                    'content_length': 0,
                    'error': f'Validation error: {str(e)}'
                }

        except httpx.TimeoutException:
            logger.error(f"크롤링 타임아웃: {url}")
            return {
                'success': False,
                'url': url,
                'title': '',
                'content': '',
                'content_length': 0,
                'error': f'타임아웃 ({self.timeout}초)'
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 에러 ({e.response.status_code}): {url}")
            return {
                'success': False,
                'url': url,
                'title': '',
                'content': '',
                'content_length': 0,
                'error': f'HTTP {e.response.status_code}'
            }

        except Exception as e:
            logger.error(f"크롤링 실패: {url}, 에러: {str(e)}")
            return {
                'success': False,
                'url': url,
                'title': '',
                'content': '',
                'content_length': 0,
                'error': str(e)
            }
