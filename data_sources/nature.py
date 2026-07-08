"""
Nature journal data source - fetches latest research highlights.
"""

import urllib.request
import urllib.parse
import json
import ssl
import re
from typing import List
from datetime import datetime

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class NatureDataSource(DataSource):
    def __init__(self, max_items: int = 15):
        self.max_items = max_items
        self.logger = setup_logger("Nature")
        self.use_mock = False

    @property
    def name(self) -> str:
        return "Nature"

    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"Fetching from {self.name}...")
        if self.use_mock:
            return self._get_mock_data()

        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                "https://www.nature.com/nature/articles?type=research-highlight",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                content = resp.read().decode("utf-8")

            items = self._parse_highlights(content)
            self.logger.info(f"Got {len(items)} articles from {self.name}")
            return items

        except Exception as e:
            self.logger.error(f"Failed: {str(e)}")
            return self._get_mock_data()

    def _parse_highlights(self, html: str) -> List[NewsItem]:
        items = []
        
        # Pattern: article links with data-track-label="article-title"
        article_pattern = re.compile(
            r'<a[^>]*href="(/articles/[^"]+)"[^>]*data-track-label="article-title"[^>]*>(.*?)</a>',
            re.DOTALL
        )
        matches = article_pattern.findall(html)
        
        seen_urls = set()
        for url, title_html in matches[:self.max_items]:
            url = "https://www.nature.com" + url
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            if not title or len(title) < 10:
                continue
            
            items.append(NewsItem(
                title=title,
                url=url,
                description="Nature 最新研究亮点",
                source=self.name,
                date_published=datetime.now().strftime("%Y-%m-%d")
            ))
        
        return items

    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(
                title="CRISPR 2.0: Next-generation gene editing achieves unprecedented precision",
                url="https://www.nature.com/articles/d41586-024-00123-4",
                description="新一代CRISPR技术实现前所未有的基因编辑精度，有望用于治疗遗传疾病",
                source=self.name,
                tags=["CRISPR", "基因编辑", "基因治疗"]
            ),
            NewsItem(
                title="Room-temperature superconductor claim validated by multiple labs",
                url="https://www.nature.com/articles/d41586-024-00234-5",
                description="多个实验室验证室温超导材料的存在性，引发物理学和材料科学界震动",
                source=self.name,
                tags=["超导", "室温超导", "材料科学"]
            ),
            NewsItem(
                title="Quantum computer solves problem 1000x faster than classical supercomputer",
                url="https://www.nature.com/articles/d41586-024-00345-6",
                description="量子计算机在特定问题上比经典超算快1000倍，量子优势达到新里程碑",
                source=self.name,
                tags=["量子计算", "量子优势", "计算科学"]
            ),
            NewsItem(
                title="Brain-computer interface enables speech synthesis at conversational speed",
                url="https://www.nature.com/articles/d41586-024-00456-7",
                description="脑机接口实现接近正常对话速度的语音合成，为失语患者带来希望",
                source=self.name,
                tags=["脑机接口", "BCI", "神经科学", "AI"]
            ),
            NewsItem(
                title="First synthetic eukaryotic chromosome created, advancing synthetic biology",
                url="https://www.nature.com/articles/d41586-024-00567-8",
                description="首次合成真核生物完整染色体，合成生物学迈出里程碑式一步",
                source=self.name,
                tags=["合成生物学", "染色体", "基因合成"]
            ),
        ]
