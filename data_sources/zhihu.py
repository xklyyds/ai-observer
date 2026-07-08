import urllib.request
import json
import ssl
from typing import List

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class ZhihuDataSource(DataSource):
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self.logger = setup_logger("Zhihu")
        self.use_mock = False
    
    @property
    def name(self) -> str:
        return "知乎热榜"
    
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取热门话题...")
        if self.use_mock:
            self.logger.info("使用模拟数据")
            return self._get_mock_data()
        
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
            
            ctx = ssl.create_default_context()
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            news_items = []
            for item in data.get("data", [])[:self.max_items]:
                target = item.get("target", {})
                title = target.get("title", "") or target.get("question", {}).get("title", "")
                
                if not title:
                    continue
                
                question_id = target.get('question', {}).get('id') or target.get('id', '')
                url = f"https://www.zhihu.com/question/{question_id}"
                excerpt = target.get("excerpt", "") or target.get("question", {}).get("excerpt", "")
                author = target.get("author", {}).get("name", "")
                
                if "AI" in title or "人工智能" in title or "机器学习" in title or "大模型" in title:
                    news_items.append(NewsItem(
                        title=title,
                        url=url,
                        description=f"摘要: {excerpt[:100]}..." if excerpt else "知乎热门话题",
                        source="知乎",
                        category="AI讨论",
                        author=author
                    ))
            
            self.logger.info(f"成功获取到 {len(news_items)} 条AI相关热门话题")
            return news_items
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.logger.warning("知乎API需要认证，使用模拟数据")
            else:
                self.logger.error(f"获取热门话题失败: HTTP Error {e.code}")
            return self._get_mock_data()
        except Exception as e:
            self.logger.error(f"获取热门话题失败: {str(e)}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(
                title="如何评价OpenAI最新发布的GPT-5模型？",
                url="https://www.zhihu.com/question/123456789",
                description="讨论OpenAI最新模型的性能提升和技术突破",
                source="知乎",
                category="AI讨论",
                tags=["GPT", "OpenAI", "讨论"]
            ),
            NewsItem(
                title="2024年AI行业发展趋势是什么？",
                url="https://www.zhihu.com/question/123456790",
                description="行业专家分享对AI未来发展的看法和预测",
                source="知乎",
                category="AI讨论",
                tags=["趋势", "行业分析"]
            ),
            NewsItem(
                title="AI大模型会取代程序员吗？",
                url="https://www.zhihu.com/question/123456791",
                description="探讨AI对编程行业的影响和未来职业发展",
                source="知乎",
                category="AI讨论",
                tags=["职业", "程序员", "AI"]
            )
        
            NewsItem(title="国产算力芯片百花齐放：寒武纪、地平线、燧原最新进展",
                     url="https://www.zhihu.com/question/chinese-ai-chips",
                     description="国内AI芯片企业在推理芯片、自动驾驶芯片、训练芯片三个赛道全面发力。",
                     source="知乎", category="芯片", tags=["AI芯片", "国产"]),
            NewsItem(title="如何评价Neuralink第二例人类植入手术的效果？",
                     url="https://www.zhihu.com/question/neuralink-2nd-implant",
                     description="从技术细节和临床应用前景分析脑机接口的最新进展和面临的伦理挑战。",
                     source="知乎", category="生物", tags=["脑机接口", "医疗"]),
            NewsItem(title="假如给你50万预算，你会做什么方向的AI创业？",
                     url="https://www.zhihu.com/question/ai-startup-budget",
                     description="知友热烈讨论AI应用层的创业机会，聚焦垂直行业解决方案和AI+科学方向。",
                     source="知乎", category="AI", tags=["AI创业", "投资"]),
]

