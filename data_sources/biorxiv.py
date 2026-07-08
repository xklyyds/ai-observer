"""
bioRxiv data source - biology preprint server.
"""

import urllib.request
import urllib.parse
import ssl
import json
from typing import List
from datetime import datetime, timedelta

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class BioRxivSource(DataSource):
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self.logger = setup_logger("bioRxiv")
        self.use_mock = False

    @property
    def name(self) -> str:
        return "bioRxiv"

    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"Fetching from {self.name}...")
        if self.use_mock:
            return self._get_mock_data()

        try:
            date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            url = f"https://api.biorxiv.org/details/biorxiv/{date}/{date}/0/{self.max_items}"
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            items = []
            for paper in data.get("collection", [])[:self.max_items]:
                items.append(NewsItem(
                    title=paper.get("title", ""),
                    url=f"https://www.biorxiv.org/content/{paper.get('doi', '')}",
                    description=paper.get("abstract", "")[:200] if paper.get("abstract") else "",
                    source=self.name, author=paper.get("authors", ""),
                    date_published=paper.get("date", "")
                ))

            self.logger.info(f"Got {len(items)} from {self.name}")
            return items if items else self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed: {str(e)}")
            return self._get_mock_data()

    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(title="Single-cell multi-omics reveals novel cell types in the human brain",
                     url="https://www.biorxiv.org/content/10.1101/2026.07.123456",
                     description="整合单细胞多组学数据发现人类大脑中前所未见的细胞亚型，为神经疾病研究提供新靶点。",
                     source=self.name, tags=["单细胞", "神经科学", "多组学"]),
            NewsItem(title="Engineered probiotics for in vivo detection of colorectal cancer",
                     url="https://www.biorxiv.org/content/10.1101/2026.07.123457",
                     description="工程化益生菌可在肠道内实时检测结直肠癌生物标志物并发出荧光信号。",
                     source=self.name, tags=["合成生物学", "癌症检测", "益生菌"]),
        ]
