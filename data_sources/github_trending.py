import urllib.request
import json
import ssl
from typing import List

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class GitHubTrendingDataSource(DataSource):
    def __init__(self, language: str = "python", since: str = "daily"):
        self.language = language
        self.since = since
        self.logger = setup_logger("GitHubTrending")
        self.use_mock = False
    
    @property
    def name(self) -> str:
        return "GitHub Trending"
    
    @property
    def priority(self) -> int:
        return 8
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取趋势项目...")
        if self.use_mock:
            self.logger.info("使用模拟数据")
            return self._get_mock_data()
        
        try:
            url = f"https://github-trending-api.now.sh/repositories?language={self.language}&since={self.since}"
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0")
            
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            news_items = []
            for repo in data[:10]:
                description = repo.get("description", "") or "No description"
                news_items.append(NewsItem(
                    title=f"{repo.get('name', '')}: {description[:50]}...",
                    url=repo.get("url", ""),
                    description=f"{description}\n⭐ Stars: {repo.get('stars', 0)} | 🔼 Trending: {repo.get('currentPeriodStars', 0)} stars today",
                    source="GitHub",
                    category="开源项目",
                    author=repo.get("author", "")
                ))
            
            self.logger.info(f"成功获取到 {len(news_items)} 个趋势项目")
            return news_items
        except urllib.error.HTTPError as e:
            if e.code == 451:
                self.logger.warning("GitHub Trending访问受限，使用模拟数据")
            else:
                self.logger.error(f"获取趋势项目失败: HTTP Error {e.code}")
            return self._get_mock_data()
        except Exception as e:
            self.logger.error(f"获取趋势项目失败: {str(e)}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(
                title="LlamaIndex: 数据增强的LLM应用框架",
                url="https://github.com/run-llama/llama_index",
                description="为LLM应用提供数据连接和增强功能的开源框架，支持多种数据源",
                source="GitHub",
                category="开源项目",
                tags=["LLM", "数据框架", "RAG"]
            ),
            NewsItem(
                title="LangChain: 构建LLM应用的工具包",
                url="https://github.com/langchain-ai/langchain",
                description="用于开发由语言模型驱动的应用程序的框架，支持链、代理等模式",
                source="GitHub",
                category="开源项目",
                tags=["LLM", "框架", "代理"]
            ),
            NewsItem(
                title="Stable Diffusion WebUI: 图像生成工具",
                url="https://github.com/AUTOMATIC1111/stable-diffusion-webui",
                description="基于Stable Diffusion的Web界面，提供丰富的图像生成功能",
                source="GitHub",
                category="开源项目",
                tags=["图像生成", "WebUI", "Stable Diffusion"]
            )
        ]