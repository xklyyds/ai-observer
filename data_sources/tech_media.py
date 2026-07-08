import urllib.request
import json
import ssl
import re
from typing import List

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class TechMediaDataSource(DataSource):
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self.logger = setup_logger("TechMedia")
    
    @property
    def name(self) -> str:
        return "科技媒体"
    
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取新闻...")
        news_items = []
        
        news_items.extend(self._fetch_36kr())
        news_items.extend(self._fetch_juejin())
        
        self.logger.info(f"共获取到 {len(news_items)} 条科技媒体新闻")
        return news_items[:self.max_items]
    
    def _fetch_36kr(self) -> List[NewsItem]:
        items = []
        try:
            ctx = ssl.create_default_context()
            
            url = "https://36kr.com/api/search-column?searchKey=AI&type=web"
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://36kr.com/"
            })
            
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            data_items = data.get("data", {}).get("items", [])
            if isinstance(data_items, list):
                for item in data_items[:5]:
                    items.append(NewsItem(
                        title=item.get("title", ""),
                        url=f"https://36kr.com/p/{item.get('id', '')}",
                        description=item.get("summary", "")[:100] + "...",
                        source="36氪",
                        category="科技新闻"
                    ))
        except Exception as e:
            self.logger.error(f"从36氪获取新闻失败: {str(e)}")
        
        return items
    
    def _fetch_juejin(self) -> List[NewsItem]:
        items = []
        try:
            ctx = ssl.create_default_context()
            
            url = "https://api.juejin.cn/search_api/v1/search?keyword=AI&type=article&limit=5"
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://juejin.cn/"
            })
            
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            result_list = data.get("data", data)
            if isinstance(result_list, list):
                data_list = result_list
            elif isinstance(result_list, dict):
                data_list = result_list.get("list", result_list.get("data", []))
            else:
                data_list = []
            
            if isinstance(data_list, list):
                for item in data_list[:5]:
                    items.append(NewsItem(
                        title=item.get("title", ""),
                        url=f"https://juejin.cn/post/{item.get('article_id', item.get('id', ''))}",
                        description=item.get("summary", item.get("content", ""))[:100] + "...",
                        source="掘金",
                        category="技术文章"
                    ))
        except Exception as e:
            self.logger.error(f"从掘金获取新闻失败: {str(e)}")
        
        return items


