from typing import List, Dict
from collections import Counter

from data_sources.base import NewsItem
from utils.logger import setup_logger
from .base import Processor


class TrendAnalyzer(Processor):
    def __init__(self):
        self.logger = setup_logger("TrendAnalyzer")
        self.trends = {}
    
    @property
    def name(self) -> str:
        return "TrendAnalyzer"
    
    def process(self, news_items: List[NewsItem]) -> List[NewsItem]:
        self.logger.info("开始分析趋势...")
        
        category_counts = Counter()
        tag_counts = Counter()
        source_counts = Counter()
        
        for item in news_items:
            if item.category:
                category_counts[item.category] += 1
            if item.tags:
                for tag in item.tags:
                    tag_counts[tag] += 1
            if item.source:
                source_counts[item.source] += 1
        
        self.trends = {
            "top_categories": category_counts.most_common(5),
            "top_tags": tag_counts.most_common(5),
            "top_sources": source_counts.most_common(3),
            "total_items": len(news_items)
        }
        
        self.logger.info(f"趋势分析完成: {self.trends}")
        return news_items
    
    def get_trends(self) -> Dict:
        return self.trends
    
    def generate_trend_summary(self) -> str:
        summary = "【今日趋势分析】\n"
        summary += "-" * 40 + "\n\n"
        
        summary += "📊 热门类别:\n"
        for category, count in self.trends.get("top_categories", []):
            percentage = round(count / max(self.trends.get("total_items", 1), 1) * 100, 1)
            summary += f"   • {category}: {count}条 ({percentage}%)\n"
        
        summary += "\n🏷️ 热门标签:\n"
        for tag, count in self.trends.get("top_tags", []):
            summary += f"   • #{tag}: {count}条\n"
        
        summary += "\n📰 主要来源:\n"
        for source, count in self.trends.get("top_sources", []):
            summary += f"   • {source}: {count}条\n"
        
        return summary