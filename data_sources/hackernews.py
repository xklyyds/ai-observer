import urllib.request
import json
import ssl
from typing import List

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class HackerNewsDataSource(DataSource):
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self.logger = setup_logger("HackerNews")
        self.use_mock = False
    
    @property
    def name(self) -> str:
        return "Hacker News"
    
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取热门话题...")
        if self.use_mock:
            self.logger.info("使用模拟数据")
            return self._get_mock_data()
        
        try:
            ctx = ssl.create_default_context()
            
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            req = urllib.request.Request(top_stories_url)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
                top_stories = json.loads(response.read().decode("utf-8"))
            
            news_items = []
            for story_id in top_stories[:self.max_items]:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                with urllib.request.urlopen(story_url, context=ctx, timeout=5) as response:
                    story = json.loads(response.read().decode("utf-8"))
                
                if story.get("type") == "story" and story.get("url"):
                    news_items.append(NewsItem(
                        title=story.get("title", ""),
                        url=story.get("url", ""),
                        description=f"Score: {story.get('score', 0)} | Comments: {story.get('descendants', 0)}",
                        source="Hacker News",
                        category="技术新闻",
                        author=story.get("by", "")
                    ))
            
            self.logger.info(f"成功获取到 {len(news_items)} 条热门话题")
            return news_items
        except Exception as e:
            self.logger.error(f"获取热门话题失败: {str(e)}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(
                title="Show HN: An AI-powered search engine for research papers",
                url="https://news.ycombinator.com/item?id=39001234",
                description="一个专注于研究论文的AI搜索引擎，支持语义搜索",
                source="Hacker News",
                category="技术新闻",
                tags=["AI搜索", "研究论文", "语义搜索"]
            ),
            NewsItem(
                title="OpenAI releases new model with improved reasoning",
                url="https://news.ycombinator.com/item?id=39001123",
                description="OpenAI发布新模型，推理能力显著提升",
                source="Hacker News",
                category="技术新闻",
                tags=["OpenAI", "推理", "模型"]
            ),
            NewsItem(
                title="Building AI agents that can browse the web autonomously",
                url="https://news.ycombinator.com/item?id=39001098",
                description="构建能够自主浏览网页的AI代理系统",
                source="Hacker News",
                category="技术新闻",
                tags=["AI代理", "网页浏览", "自主"]
            )
        ]


