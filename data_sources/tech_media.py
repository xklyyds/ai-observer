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
        
        if not items:
            self.logger.warning("所有科技媒体源获取失败，使用模拟数据")
            return self._get_mock_data()
        
        return items



    def _get_mock_data(self) -> List[NewsItem]:
        """Mock data covering all taxonomy categories."""
        return [
            NewsItem(title="马斯克宣布Neuralink第三例人体植入手术成功，意念操控精度达新高度",
                     url="https://neuralink.com/blog/third-implant",
                     description="Neuralink第三位受试者成功使用脑机接口操控外骨骼设备，信号采集通道超过1500个。",
                     source="TechMedia", tags=["脑机接口", "Neuralink"]),
            NewsItem(title="GPT-5正式发布：多模态推理能力全面超越人类专家水平",
                     url="https://techmedia.io/gpt5-launch",
                     description="OpenAI发布GPT-5，在数学推理、代码生成、科学理解等多项基准测试中达到或超越人类专家水平。",
                     source="TechMedia", tags=["LLM", "GPT", "AI"]),
            NewsItem(title="全球首款10米级可回收液体火箭成功发射",
                     url="https://techmedia.io/reusable-rocket-china",
                     description="中国商业航天公司成功发射10米级可回收液体火箭，标志着中国民营航天进入可回收时代。",
                     source="TechMedia", tags=["航天", "火箭"]),
            NewsItem(title="苹果Vision Pro 2发布：重量减半，价格降至1999美元",
                     url="https://techmedia.io/vision-pro-2",
                     description="Apple第二代空间计算设备大幅减重并降低售价，支持全天佩戴，生态应用突破1万个。",
                     source="TechMedia", tags=["AR/VR", "苹果"]),
            NewsItem(title="比亚迪发布固态电池：续航突破1500公里，充电10分钟",
                     url="https://techmedia.io/byd-solid-battery",
                     description="比亚迪全固态电池量产版发布，能量密度达500Wh/kg，2027年搭载量产车型。",
                     source="TechMedia", tags=["新能源", "电池"]),
            NewsItem(title="深度求索发布DeepSeek-R2：数学能力对标GPT-5，完全开源",
                     url="https://techmedia.io/deepseek-r2",
                     description="国产大模型DeepSeek-R2在数学和编程基准上达到国际领先水平，MIT开源协议发布。",
                     source="TechMedia", tags=["LLM", "开源", "DeepSeek"]),
            NewsItem(title="中国天眼FAST发现首个持续活跃的快速射电暴",
                     url="https://techmedia.io/fast-repeating-frb",
                     description="FAST射电望远镜发现首个持续活跃的快速射电暴，为理解宇宙极端物理过程提供关键线索。",
                     source="TechMedia", tags=["天文", "FAST"]),
            NewsItem(title="全球首个CRISPR基因编辑新冠疫苗进入三期临床试验",
                     url="https://techmedia.io/crispr-vaccine-phase3",
                     description="利用CRISPR技术开发的新冠疫苗具有无需冷链运输、一剂免疫的独特优势，三期结果即将公布。",
                     source="TechMedia", tags=["CRISPR", "疫苗"]),
        ]
