"""
Reddit data source - uses HTTP JSON API (works on PythonAnywhere free tier).
"""

import urllib.request
import json
import ssl
from typing import List
from datetime import datetime

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class RedditSource(DataSource):
    SUBREDDITS = ["technology", "programming", "Futurology", "science", "MachineLearning"]

    def __init__(self, max_items: int = 15):
        self.max_items = max_items
        self.logger = setup_logger("Reddit")
        self.use_mock = False

    @property
    def name(self) -> str:
        return "Reddit"

    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"Fetching from {self.name}...")
        if self.use_mock:
            return self._get_mock_data()

        all_items = []
        for subreddit in self.SUBREDDITS:
            try:
                url = f"http://old.reddit.com/r/{subreddit}/.json"  # HTTP, not HTTPS!
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                for post in data.get("data", {}).get("children", [])[:5]:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    url = post_data.get("url", "")
                    if title and url and not url.startswith("http"):
                        url = "https://www.reddit.com" + post_data.get("permalink", "")
                    all_items.append(NewsItem(
                        title=title, url=url,
                        description=post_data.get("selftext", "")[:200] or f"r/{subreddit} hot post",
                        source=f"Reddit r/{subreddit}",
                        date_published=datetime.fromtimestamp(post_data.get("created_utc", 0)).strftime("%Y-%m-%d")
                    ))
                self.logger.info(f"  r/{subreddit}: got posts")

            except Exception as e:
                self.logger.warning(f"  r/{subreddit} failed: {str(e)[:60]}")

        if not all_items:
            self.logger.warning("All subreddits failed, using mock")
            return self._get_mock_data()

        self.logger.info(f"Total: {len(all_items)} from Reddit")
        return all_items[:self.max_items]

    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(title="Reddit AMA: OpenAI CTO answers community questions about GPT-5 safety",
                     url="https://www.reddit.com/r/MachineLearning",
                     description="OpenAI CTO fields tough questions about alignment research and safety measures.",
                     source="Reddit r/MachineLearning", tags=["AI", "GPT"])] * 5
