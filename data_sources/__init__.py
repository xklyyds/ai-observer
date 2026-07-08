from .base import DataSource, NewsItem
from .bing_news import BingNewsDataSource
from .arxiv import ArXivDataSource
from .github_trending import GitHubTrendingDataSource
from .hackernews import HackerNewsDataSource
from .rss_feed import RSSFeedDataSource
from .zhihu import ZhihuDataSource
from .tech_media import TechMediaDataSource
from .nature import NatureDataSource
from config import DATA_SOURCES_CONFIG


DATA_SOURCE_REGISTRY = {
    "bing": BingNewsDataSource,
    "arxiv": ArXivDataSource,
    "github": GitHubTrendingDataSource,
    "hackernews": HackerNewsDataSource,
    "rss": RSSFeedDataSource,
    "zhihu": ZhihuDataSource,
    "techmedia": TechMediaDataSource,
    "nature": NatureDataSource,
}


def get_all_data_sources() -> list:
    sources = []
    
    if DATA_SOURCES_CONFIG.get("bing", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["bing"]
        sources.append(BingNewsDataSource(query=config.get("query"), count=config.get("count", 10)))
    
    if DATA_SOURCES_CONFIG.get("arxiv", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["arxiv"]
        source = ArXivDataSource(
            categories=config.get("categories"),
            max_results=config.get("max_results", 10)
        )
        source.use_mock = config.get("use_mock", False)
        sources.append(source)
    
    if DATA_SOURCES_CONFIG.get("github", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["github"]
        source = GitHubTrendingDataSource(
            language=config.get("language"),
            since=config.get("since")
        )
        source.use_mock = config.get("use_mock", False)
        sources.append(source)
    
    if DATA_SOURCES_CONFIG.get("hackernews", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["hackernews"]
        source = HackerNewsDataSource(max_items=config.get("max_items", 10))
        source.use_mock = config.get("use_mock", False)
        sources.append(source)
    
    if DATA_SOURCES_CONFIG.get("rss", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["rss"]
        sources.append(RSSFeedDataSource(
            feeds=config.get("feeds"),
            max_per_feed=config.get("max_per_feed", 5)
        ))
    
    if DATA_SOURCES_CONFIG.get("zhihu", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["zhihu"]
        source = ZhihuDataSource(max_items=config.get("max_items", 10))
        source.use_mock = config.get("use_mock", False)
        sources.append(source)
    
    if DATA_SOURCES_CONFIG.get("techmedia", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["techmedia"]
        sources.append(TechMediaDataSource(max_items=config.get("max_items", 10)))
    
    if DATA_SOURCES_CONFIG.get("nature", {}).get("enabled", True):
        config = DATA_SOURCES_CONFIG["nature"]
        source = NatureDataSource(max_items=config.get("max_items", 15))
        source.use_mock = config.get("use_mock", False)
        sources.append(source)
    
    return sources


def get_data_source(name: str, **kwargs) -> DataSource:
    if name in DATA_SOURCE_REGISTRY:
        return DATA_SOURCE_REGISTRY[name](**kwargs)
    raise ValueError(f"Unknown data source: {name}")
