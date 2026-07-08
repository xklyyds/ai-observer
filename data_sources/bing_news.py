import os
import urllib.request
import urllib.parse
import json
from typing import List

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class BingNewsDataSource(DataSource):
    def __init__(self, query: str = "AI技术突破", count: int = 10):
        self.query = query
        self.count = count
        self.logger = setup_logger("BingNews")
        self.api_key = os.environ.get("BING_API_KEY", "")
    
    @property
    def name(self) -> str:
        return "Bing News"
    
    @property
    def priority(self) -> int:
        return 10
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取新闻...")
        if not self.api_key:
            self.logger.warning("未配置BING_API_KEY环境变量，将使用模拟数据")
            return self._get_mock_data()
        
        try:
            url = "https://api.bing.microsoft.com/v7.0/news/search"
            params = urllib.parse.urlencode({
                "q": self.query,
                "count": self.count,
                "mkt": "zh-CN",
                "sortBy": "date"
            })
            full_url = f"{url}?{params}"
            
            req = urllib.request.Request(full_url)
            req.add_header("Ocp-Apim-Subscription-Key", self.api_key)
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                articles = data.get("value", [])
            
            news_items = []
            for article in articles:
                news_items.append(NewsItem(
                    title=article.get("name", ""),
                    url=article.get("url", ""),
                    description=article.get("description", ""),
                    source=article.get("provider", [{}])[0].get("name", ""),
                    date_published=article.get("datePublished", ""),
                    category=article.get("category", "")
                ))
            
            self.logger.info(f"成功获取到 {len(news_items)} 条新闻")
            return news_items
        except Exception as e:
            self.logger.error(f"获取新闻失败: {str(e)}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(
                title="GPT-5 模型性能大幅提升，推理速度提高300%",
                url="https://openai.com/blog/gpt-5-update",
                description="OpenAI今日发布GPT-5模型更新，在保持高精度的同时，推理速度相比GPT-4提升了300%",
                source="OpenAI",
                category="LLM"
            ),
            NewsItem(
                title="DeepMind推出新一代AlphaFold，蛋白质结构预测准确率突破99%",
                url="https://deepmind.google/discover/blog/alphafold-update/",
                description="AlphaFold最新版本在CASP16竞赛中取得突破性成果，预测准确率达到99.2%",
                source="Google DeepMind",
                category="生物AI"
            ),
            NewsItem(
                title="Anthropic发布Claude 3.5，支持百万token上下文窗口",
                url="https://www.anthropic.com/index/claude-3-5",
                description="Claude 3.5正式发布，支持1M token上下文，在长文本处理任务中表现优异",
                source="Anthropic",
                category="LLM"
            ),
            NewsItem(
                title="Stable Diffusion 4发布，图像生成质量再创新高",
                url="https://stability.ai/news/stable-diffusion-4",
                description="Stability AI推出Stable Diffusion 4，在图像细节和一致性方面有显著提升",
                source="Stability AI",
                category="图像生成"
            ),
            NewsItem(
                title="AI芯片市场竞争加剧，多家厂商推出新一代产品",
                url="https://techcrunch.com/2024/01/15/ai-chip-market-heats-up/",
                description="NVIDIA、AMD、Intel等厂商纷纷发布新一代AI芯片，性能提升显著",
                source="TechCrunch",
                category="AI硬件"
            )
        ]