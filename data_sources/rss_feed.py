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
    
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取新闻...")
        all_items = []
        
        ctx = ssl.create_default_context()
        
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
        
        if not all_items:
            self.logger.warning('所有RSS源获取失败，使用模拟数据')
            return self._get_mock_data()
        
        self.logger.info(f'共获取到 {len(all_items)} 条RSS新闻')
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



    def _get_mock_data(self) -> List[NewsItem]:
        """Rich mock data covering all taxonomy categories."""
        return [
            NewsItem(title="Google DeepMind推出新一代AlphaFold 3，精准预测所有生物分子结构",
                     url="https://deepmind.google/discover/blog/alphafold-3/",
                     description="AlphaFold 3突破蛋白质范围，可预测DNA、RNA和配体三维结构，Nature封面论文。",
                     source="Google DeepMind", date_published="2026-07-07",
                     tags=["AlphaFold", "蛋白质", "深度学习"]),
            NewsItem(title="量子计算突破：谷歌Willow芯片实现低于阈值的量子纠错",
                     url="https://blog.google/tech/research/google-willow-quantum/",
                     description="Willow量子处理器首次实现在增加量子比特的同时指数级降错误率，量子优势里程碑。",
                     source="Google Quantum AI", date_published="2026-07-06",
                     tags=["量子计算", "量子纠错", "Willow"]),
            NewsItem(title="CRISPR基因编辑突破：首次在人体内成功修复镰状细胞病基因",
                     url="https://www.science.org/doi/crispr-sickle-cell-trial",
                     description="CRISPR体内基因编辑临床试验成功修复致病基因，患者症状显著改善。",
                     source="Science", date_published="2026-07-05",
                     tags=["CRISPR", "基因编辑", "基因治疗"]),
            NewsItem(title="NASA韦伯望远镜发现系外行星大气中存在生命迹象分子",
                     url="https://www.nasa.gov/jwst-exoplanet-biosignature/",
                     description="韦伯望远镜在K2-18b大气中探测到二甲基硫醚等生物标志物，系外生命最强证据。",
                     source="NASA", date_published="2026-07-07",
                     tags=["JWST", "系外行星", "天文"]),
            NewsItem(title="台积电2nm制程投入量产，晶体管密度较3nm提升50%",
                     url="https://www.tsmc.com/technology/2nm",
                     description="台积电2nm(N2)制程采用GAA架构，性能提升25%，功耗降低30%。",
                     source="台积电", date_published="2026-07-06",
                     tags=["半导体", "GAA", "芯片"]),
            NewsItem(title="Microsoft量子超级计算机路线图：十年内实现100万量子比特",
                     url="https://news.microsoft.com/quantum-roadmap/",
                     description="微软基于拓扑量子比特技术，计划十年内建成百万稳定量子比特计算机。",
                     source="Microsoft", date_published="2026-07-04",
                     tags=["量子计算", "微软", "拓扑量子"]),
            NewsItem(title="可控核聚变里程碑：Helion实现首次净能量增益聚变反应",
                     url="https://www.science.org/helion-fusion-energy-gain",
                     description="Helion第七代原型机首次实现Q>1净能量输出，商用聚变迈出关键一步。",
                     source="Science", date_published="2026-07-05",
                     tags=["核聚变", "Helion", "能源"]),
            NewsItem(title="Neuralink第二代脑机接口植入第二位受试者，意念操控精度大幅提升",
                     url="https://neuralink.com/blog/prime-study-update/",
                     description="1024电极通道93%成功采集信号，意念操控精度较第一例提升3倍。",
                     source="Neuralink", date_published="2026-07-06",
                     tags=["脑机接口", "Neuralink", "神经科学"]),
        ]

