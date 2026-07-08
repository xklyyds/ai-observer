import urllib.request
import re
import ssl
from typing import List
from datetime import datetime

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class RSSFeedDataSource(DataSource):
    RSS_FEEDS = {
        "机器之心": "https://www.jiqizhixin.com/rss",
        "量子位": "https://www.qbitai.com/rss",
        "InfoQ": "https://www.infoq.cn/rss",
        "开源中国": "https://www.oschina.net/action/rss",
        "AI科技评论": "https://www.aitechtalk.com/rss",
        "CSDN": "https://www.csdn.net/rss",
    }
    
    def __init__(self, feeds: List[str] = None, max_per_feed: int = 5):
        self.feeds = feeds or list(self.RSS_FEEDS.keys())
        self.max_per_feed = max_per_feed
        self.logger = setup_logger("RSSFeed")
    
    @property
    def name(self) -> str:
        return "RSS订阅"
    
    @property
    def priority(self) -> int:
        return 9
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取新闻...")
        all_items = []
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        for feed_name in self.feeds:
            if feed_name not in self.RSS_FEEDS:
                continue
            
            url = self.RSS_FEEDS[feed_name]
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                    xml_content = response.read().decode("utf-8", errors="ignore")
                
                items = self._parse_rss(xml_content, feed_name)
                all_items.extend(items[:self.max_per_feed])
                self.logger.info(f"从 {feed_name} 获取到 {len(items)} 条新闻")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.logger.warning(f"{feed_name} RSS地址无效，跳过")
                else:
                    self.logger.error(f"从 {feed_name} 获取新闻失败: HTTP Error {e.code}")
            except Exception as e:
                self.logger.error(f"从 {feed_name} 获取新闻失败: {str(e)}")
        
        self.logger.info(f"共获取到 {len(all_items)} 条RSS新闻")
        return all_items
    
    def _parse_rss(self, xml_content: str, source: str) -> List[NewsItem]:
        items = []
        
        item_pattern = re.compile(r'<item>(.*?)</item>', re.DOTALL)
        for item in item_pattern.finditer(xml_content):
            item_content = item.group(1)
            
            title = re.search(r'<title>(.*?)</title>', item_content)
            title = title.group(1).strip() if title else ""
            
            url = re.search(r'<link>(.*?)</link>', item_content)
            url = url.group(1).strip() if url else ""
            
            description = re.search(r'<description>(.*?)</description>', item_content)
            description = description.group(1).strip() if description else ""
            
            pub_date = re.search(r'<pubDate>(.*?)</pubDate>', item_content)
            pub_date = pub_date.group(1).strip() if pub_date else ""
            
            if title and url:
                description = self._clean_html(description)
                items.append(NewsItem(
                    title=title,
                    url=url,
                    description=description[:150] + "..." if len(description) > 150 else description,
                    source=source,
                    date_published=pub_date
                ))
        
        return items
    
    def _clean_html(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()