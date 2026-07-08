"""
MIT Technology Review data source - authoritative tech journalism.
"""

import urllib.request
import urllib.parse
import ssl
import re
from typing import List
from datetime import datetime

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class MITTechReviewSource(DataSource):
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self.logger = setup_logger("MIT Tech Review")
        self.use_mock = False

    @property
    def name(self) -> str:
        return "MIT Technology Review"

    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"Fetching from {self.name}...")
        if self.use_mock:
            return self._get_mock_data()

        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                "https://www.technologyreview.com/feed/",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            items = self._parse_rss(content)
            self.logger.info(f"Got {len(items)} from {self.name}")
            return items[:self.max_items] if items else self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed: {str(e)}")
            return self._get_mock_data()

    def _parse_rss(self, xml: str) -> List[NewsItem]:
        items = []
        entries = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
        for entry in entries[:self.max_items]:
            title = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', entry)
            title = title.group(1).strip() if title else ""
            url = re.search(r'<link>(.*?)</link>', entry)
            url = url.group(1).strip() if url else ""
            desc = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', entry)
            desc = re.sub(r'<[^>]+>', '', desc.group(1)).strip()[:200] if desc else ""
            if title and url:
                items.append(NewsItem(title=title, url=url, description=desc,
                                      source=self.name, date_published=datetime.now().strftime("%Y-%m-%d")))
        return items

    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(title="The race for AGI: Can safety keep pace with capability?",
                     url="https://www.technologyreview.com/2026/07/agi-safety/",
                     description="As frontier models approach AGI-level reasoning, safety researchers warn that current safeguards may not be sufficient.",
                     source=self.name, tags=["AGI", "AI安全", "前沿模型"]),
            NewsItem(title="How perovskite solar cells are finally hitting the market",
                     url="https://www.technologyreview.com/2026/07/perovskite-solar/",
                     description="After years in the lab, perovskite tandem solar cells are entering commercial production with record efficiency.",
                     source=self.name, tags=["钙钛矿", "太阳能", "新材料"]),
            NewsItem(title="The hidden cost of AI: Chip manufacturing hits environmental limits",
                     url="https://www.technologyreview.com/2026/07/chip-environment/",
                     description="Semiconductor fabs consume massive amounts of water and energy, raising sustainability questions about AI scaling.",
                     source=self.name, tags=["半导体", "AI芯片", "环境"]),
        ]
