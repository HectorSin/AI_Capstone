import json
import logging
from typing import Dict, Any
import jinja2
from xhtml2pdf import pisa
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.schemas import InfographicData
from app.config import settings

logger = logging.getLogger(__name__)

class InfographicService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.google_api_key,
            temperature=0.3
        )
        self.parser = PydanticOutputParser(pydantic_object=InfographicData)
        
        # 프롬프트 템플릿 로드
        self.prompt_config = self._load_prompt_config()
        # 아이콘 매핑 로드
        self.icon_map = self._load_icon_map()

    def _load_prompt_config(self) -> Dict[str, Any]:
        """프롬프트 설정 파일을 로드합니다."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "ai/configs/prompt_templates.json")
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {e}")
            # 실패 시 빈 딕셔너리 반환
            return {}

    def _load_icon_map(self) -> Dict[str, str]:
        """아이콘 매핑 설정 파일을 로드합니다."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "ai/configs/icon_mappings.json")
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("icon_map", {})
        except Exception as e:
            logger.error(f"Failed to load icon mappings: {e}")
            return {}

    async def generate_infographic_json(self, script: str) -> InfographicData:
        """
        대본을 분석하여 인포그래픽용 구조화된 JSON 데이터를 생성합니다.
        """
        config = self.prompt_config.get("infographic_prompt", {})
        system_role = config.get("system_role", "")
        instruction = config.get("instruction", "")
        requirements = "\n".join([f"{i+1}. {req}" for i, req in enumerate(config.get("requirements", []))])
        
        template_str = f"""
            {system_role}
            {instruction}
            
            대본:
            {{script}}
            
            요구사항:
            {requirements}
            
            {{format_instructions}}
            """

        prompt = PromptTemplate(
            template=template_str,
            input_variables=["script"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        chain = prompt | self.llm | self.parser
        
        try:
            result = await chain.ainvoke({"script": script})
            return result
        except Exception as e:
            logger.error(f"LLM JSON generation failed: {e}")
            raise

    def generate_html(self, data: InfographicData) -> str:
        """
        InfographicData를 HTML로 변환합니다.
        """
        # 아이콘 매핑 사용
        icon_map = self.icon_map

        # 간단한 인포그래픽 HTML 템플릿
        template_str = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <style>
                @font-face {
                    font-family: 'NanumGothic';
                    src: url('/app/fonts/NanumGothic.ttf');
                }
                @font-face {
                    font-family: 'NanumGothic';
                    src: url('/app/fonts/NanumGothic-Bold.ttf');
                    font-weight: bold;
                }
                body {
                    font-family: 'NanumGothic', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid {{ data.colors[0] if data.colors else '#333' }};
                }
                h1 {
                    color: {{ data.colors[0] if data.colors else '#333' }};
                    font-size: 36px;
                    margin-bottom: 10px;
                }
                .subtitle {
                    font-size: 18px;
                    color: #666;
                }
                .summary {
                    background-color: {{ data.colors[1] if data.colors|length > 1 else '#eee' }}33;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    font-size: 16px;
                    line-height: 1.6;
                }
                .section {
                    margin-bottom: 25px;
                    padding: 15px;
                    border-left: 5px solid {{ data.colors[2] if data.colors|length > 2 else '#999' }};
                    background-color: #fff;
                }
                .section-title {
                    font-size: 20px;
                    font-weight: bold;
                    color: {{ data.colors[0] if data.colors else '#333' }};
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                }
                .section-icon {
                    margin-right: 10px;
                    font-size: 24px;
                }
                .section-content {
                    font-size: 15px;
                    line-height: 1.5;
                }
                .conclusion {
                    margin-top: 40px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 18px;
                    padding: 20px;
                    background-color: {{ data.colors[0] if data.colors else '#333' }};
                    color: white;
                    border-radius: 8px;
                }
                .footer {
                    margin-top: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #999;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ data.title }}</h1>
                    {% if data.subtitle %}
                    <div class="subtitle">{{ data.subtitle }}</div>
                    {% endif %}
                </div>

                <div class="summary">
                    <strong>요약:</strong> {{ data.summary }}
                </div>

                {% for section in data.sections %}
                <div class="section">
                    <div class="section-title">
                        {% if section.icon %}
                        <span class="section-icon">{{ icon_map.get(section.icon.lower(), '📌') }}</span>
                        {% else %}
                        <span class="section-icon">📌</span>
                        {% endif %}
                        {{ section.title }}
                    </div>
                    <div class="section-content">
                        {{ section.content }}
                    </div>
                </div>
                {% endfor %}

                {% if data.conclusion %}
                <div class="conclusion">
                    {{ data.conclusion }}
                </div>
                {% endif %}
                
                <div class="footer">
                    Generated by AI Infographic Service
                </div>
            </div>
        </body>
        </html>
        """
        
        template = jinja2.Template(template_str)
        return template.render(data=data, icon_map=icon_map)

    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """
        HTML을 PDF로 변환하여 저장합니다.
        """
        try:
            with open(output_path, "w+b") as result_file:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=result_file,
                    encoding='utf-8'
                )
            
            if pisa_status.err:
                logger.error(f"PDF generation error: {pisa_status.err}")
                return False
            return True
        except Exception as e:
            logger.error(f"PDF generation exception: {e}")
            return False

infographic_service = InfographicService()
