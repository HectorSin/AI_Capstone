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
        InfographicData를 PDF 생성을 위한 HTML로 변환합니다.
        (Corporate Report Style - xhtml2pdf Optimized)
        """
        
        # 색상 팔레트 안전 처리
        # 전문적인 느낌을 위해 채도가 너무 높은 원색보다는 톤다운된 컬러가 좋으므로
        # 데이터가 없을 경우를 대비한 기본값을 '신뢰감 있는 네이비/골드/그레이' 톤으로 설정
        primary_color = data.colors[0] if data.colors and len(data.colors) > 0 else '#1a237e'  # Deep Navy
        secondary_color = data.colors[1] if data.colors and len(data.colors) > 1 else '#ff6f00' # Amber/Gold
        accent_color = data.colors[2] if data.colors and len(data.colors) > 2 else '#455a64'   # Blue Grey
        
        # HTML 템플릿
        template_str = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <style>
                /* [폰트 설정] */
                @font-face {
                    font-family: 'NanumGothic';
                    src: url('/app/fonts/NanumGothic.ttf');
                }
                @font-face {
                    font-family: 'NanumGothic';
                    src: url('/app/fonts/NanumGothic-Bold.ttf');
                    font-weight: bold;
                }

                /* [페이지 설정] - A4 여백 지정 */
                @page {
                    size: A4;
                    margin: 1.5cm;
                    @frame footer_frame {
                        -pdf-frame-content: footerContent;
                        bottom: 1cm;
                        margin-left: 1.5cm;
                        margin-right: 1.5cm;
                        height: 1cm;
                    }
                }

                body {
                    font-family: 'NanumGothic', sans-serif;
                    font-size: 10pt;
                    line-height: 1.6;
                    color: #2c3e50;
                    background-color: #ffffff;
                }

                /* [헤더 영역] - 전체 너비 배경색 */
                .header-wrapper {
                    background-color: {{ primary_color }};
                    color: #ffffff;
                    padding: 20px 30px;
                    margin-bottom: 30px;
                    border-radius: 4px;
                }

                .report-label {
                    font-size: 8pt;
                    opacity: 0.8;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    margin-bottom: 5px;
                }

                h1 {
                    font-family: 'NanumGothic', sans-serif;
                    font-size: 24pt;
                    font-weight: bold;
                    margin: 0;
                    padding: 0;
                    line-height: 1.2;
                }

                .subtitle {
                    font-size: 11pt;
                    opacity: 0.9;
                    margin-top: 8px;
                    font-weight: normal;
                }

                .summary-container {
                    margin-bottom: 40px;
                    padding: 0 10px;
                }
                
                .summary-table {
                    width: 100%;
                    border-top: 2px solid {{ secondary_color }};
                    border-bottom: 1px solid #eeeeee;
                    background-color: #fbfbfb;
                }

                .summary-title-cell {
                    width: 15%;
                    vertical-align: top;
                    padding: 20px 0;
                    font-weight: bold;
                    color: {{ secondary_color }};
                    font-size: 9pt;
                    text-transform: uppercase;
                }

                .summary-content-cell {
                    vertical-align: top;
                    padding: 20px 10px;
                    font-size: 11pt;
                    font-weight: bold;
                    color: #444;
                    line-height: 1.8;
                    text-align: justify;
                }

                /* [본문 섹션] - 클린한 리스트 스타일 */
                .section-wrapper {
                    width: 100%;
                }

                .section-table {
                    width: 100%;
                    margin-bottom: 15px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #e0e0e0;
                }

                /* 마지막 테이블은 선 없애기 */
                .section-table.last {
                    border-bottom: none;
                }

                .icon-cell {
                    width: 40px;
                    vertical-align: top;
                    padding-top: 5px;
                }

                .icon-box {
                    font-size: 20px;
                    color: {{ primary_color }};
                }

                .content-cell {
                    vertical-align: top;
                    padding-left: 15px;
                }

                .section-title {
                    font-size: 13pt;
                    font-weight: bold;
                    color: {{ primary_color }};
                    margin-bottom: 6px;
                }

                .section-text {
                    font-size: 10pt;
                    color: #555;
                    text-align: justify;
                }

                /* [결론 영역] - 하단 강조 박스 */
                .conclusion-box {
                    margin-top: 30px;
                    padding: 25px;
                    background-color: #f0f2f5;
                    border-left: 5px solid {{ primary_color }};
                    border-radius: 0 4px 4px 0;
                }

                .conclusion-text {
                    font-size: 11pt;
                    font-weight: bold;
                    color: {{ primary_color }};
                    text-align: center;
                    line-height: 1.6;
                }

                /* [푸터] */
                #footerContent {
                    text-align: right;
                    color: #999;
                    font-size: 8pt;
                    border-top: 1px solid #eee;
                    padding-top: 5px;
                }
            </style>
        </head>
        <body>
            <!-- 헤더 (Top Banner Style) -->
            <div class="header-wrapper">
                <div class="report-label">ISSUE REPORT</div>
                <h1>{{ data.title }}</h1>
                {% if data.subtitle %}
                <div class="subtitle">{{ data.subtitle }}</div>
                {% endif %}
            </div>

            <!-- 요약 (Executive Summary) -->
            <div class="summary-container">
                <table class="summary-table" cellspacing="0" cellpadding="0">
                    <tr>
                        <td class="summary-title-cell">KEY<br>SUMMARY</td>
                        <td class="summary-content-cell">
                            {{ data.summary }}
                        </td>
                    </tr>
                </table>
            </div>

            <!-- 본문 섹션 -->
            <div class="section-wrapper">
                {% for section in data.sections %}
                <table class="section-table" cellspacing="0" cellpadding="0">
                    <tr>
                        <!-- 아이콘 -->
                        <td class="icon-cell">
                            <div class="icon-box">
                                {% if section.icon %}
                                    {{ icon_map.get(section.icon.lower(), '■') }}
                                {% else %}
                                    ■
                                {% endif %}
                            </div>
                        </td>
                        <!-- 내용 -->
                        <td class="content-cell">
                            <div class="section-title">{{ section.title }}</div>
                            <div class="section-text">{{ section.content }}</div>
                        </td>
                    </tr>
                </table>
                {% endfor %}
            </div>

            <!-- 결론 (Insight) -->
            {% if data.conclusion %}
            <div class="conclusion-box">
                <div class="conclusion-text">
                    "{{ data.conclusion }}"
                </div>
            </div>
            {% endif %}

            <!-- 푸터 -->
            <div id="footerContent">
                Generated by Snack Cast | Page <pdf:pagenumber>
            </div>
        </body>
        </html>
        """
        
        template = jinja2.Template(template_str)
        return template.render(
            data=data, 
            icon_map=self.icon_map,
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=accent_color
        )

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
