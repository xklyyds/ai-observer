import urllib.request
import urllib.parse
import json
import ssl
from typing import List
from datetime import datetime, timedelta

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class ArXivDataSource(DataSource):
    def __init__(self, categories: List[str] = None, max_results: int = 10):
        self.categories = categories or ["cs.AI", "cs.LG", "stat.ML"]
        self.max_results = max_results
        self.logger = setup_logger("arXiv")
        self.use_mock = False
    
    @property
    def name(self) -> str:
        return "arXiv"
    
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取预印本...")
        if self.use_mock:
            self.logger.info("使用模拟数据")
            return self._get_mock_data()
        
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            category_query = " OR ".join(f"cat:{c}" for c in self.categories)
            
            url = "http://export.arxiv.org/api/query"
            params = urllib.parse.urlencode({
                "search_query": f"({category_query})",
                "start": 0,
                "max_results": self.max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            })
            full_url = f"{url}?{params}"
            
            ctx = ssl.create_default_context()
            
            req = urllib.request.Request(full_url)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                xml_content = response.read().decode("utf-8")
            
            news_items = self._parse_arxiv_xml(xml_content)
            self.logger.info(f"成功获取到 {len(news_items)} 条预印本")
            return news_items
        except Exception as e:
            self.logger.error(f"获取预印本失败: {str(e)}")
            return self._get_mock_data()
    
    def _parse_arxiv_xml(self, xml_content: str) -> List[NewsItem]:
        import re
        
        items = []
        entry_pattern = re.compile(
            r'<entry>(.*?)</entry>',
            re.DOTALL
        )
        
        for entry in entry_pattern.finditer(xml_content):
            entry_content = entry.group(1)
            
            title = re.search(r'<title>(.*?)</title>', entry_content)
            title = title.group(1).strip() if title else ""
            
            url = re.search(r'<id>(.*?)</id>', entry_content)
            url = url.group(1).strip() if url else ""
            
            summary = re.search(r'<summary>(.*?)</summary>', entry_content)
            summary = summary.group(1).strip() if summary else ""
            
            authors = re.findall(r'<name>(.*?)</name>', entry_content)
            author = ", ".join(authors) if authors else ""
            
            category = re.search(r'<category term="(.*?)"/>', entry_content)
            category = category.group(1).strip() if category else "AI"
            
            published = re.search(r'<published>(.*?)</published>', entry_content)
            published = published.group(1).strip() if published else ""
            
            items.append(NewsItem(
                title=title,
                url=url,
                description=summary,
                source="arXiv",
                category=category,
                author=author,
                date_published=published
            ))
        
        return items
    
    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(
                title="LLM Agents: Autonomous Reasoning and Tool Use",
                url="https://arxiv.org/abs/2401.15995",
                description="提出了一种新的LLM代理框架，实现自主推理和工具使用，在复杂任务上表现优异",
                source="arXiv",
                category="cs.AI",
                author="Wang et al.",
                tags=["LLM", "Agent", "推理"]
            ),
            NewsItem(
                title="Diffusion Models with Attention Mechanism",
                url="https://arxiv.org/abs/2401.14567",
                description="将注意力机制引入扩散模型，显著提升图像生成质量和效率",
                source="arXiv",
                category="cs.LG",
                author="Chen et al.",
                tags=["扩散模型", "注意力机制", "图像生成"]
            ),
            NewsItem(
                title="Efficient Training of Foundation Models",
                url="https://arxiv.org/abs/2401.13456",
                description="提出高效训练基础模型的新方法，训练成本降低50%",
                source="arXiv",
                category="stat.ML",
                author="Li et al.",
                tags=["基础模型", "训练效率", "优化"]
            )
        ]


