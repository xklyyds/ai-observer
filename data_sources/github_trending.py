import urllib.request
import json
import ssl
from typing import List

from .base import DataSource, NewsItem
from utils.logger import setup_logger


class GitHubTrendingDataSource(DataSource):
    def __init__(self, language: str = "python", since: str = "daily"):
        self.language = language
        self.since = since
        self.logger = setup_logger("GitHubTrending")
        self.use_mock = False
    
    @property
    def name(self) -> str:
        return "GitHub Trending"
    
    
    def fetch(self) -> List[NewsItem]:
        self.logger.info(f"开始从 {self.name} 获取趋势项目...")
        if self.use_mock:
            self.logger.info("使用模拟数据")
            return self._get_mock_data()
        
        try:
            url = f"https://github-trending-api.now.sh/repositories?language={self.language}&since={self.since}"
            
            ctx = ssl.create_default_context()
            
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0")
            
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            news_items = []
            for repo in data[:10]:
                description = repo.get("description", "") or "No description"
                news_items.append(NewsItem(
                    title=f"{repo.get('name', '')}: {description[:50]}...",
                    url=repo.get("url", ""),
                    description=f"{description}\n⭐ Stars: {repo.get('stars', 0)} | 🔼 Trending: {repo.get('currentPeriodStars', 0)} stars today",
                    source="GitHub",
                    category="开源项目",
                    author=repo.get("author", "")
                ))
            
            self.logger.info(f"成功获取到 {len(news_items)} 个趋势项目")
            return news_items
        except urllib.error.HTTPError as e:
            if e.code == 451:
                self.logger.warning("GitHub Trending访问受限，使用模拟数据")
            else:
                self.logger.error(f"获取趋势项目失败: HTTP Error {e.code}")
            return self._get_mock_data()
        except Exception as e:
            self.logger.error(f"获取趋势项目失败: {str(e)}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> List[NewsItem]:
        return [
            NewsItem(
                title="LlamaIndex: 数据增强的LLM应用框架",
                url="https://github.com/run-llama/llama_index",
                description="为LLM应用提供数据连接和增强功能的开源框架，支持多种数据源",
                source="GitHub",
                category="开源项目",
                tags=["LLM", "数据框架", "RAG"]
            ),
            NewsItem(
                title="LangChain: 构建LLM应用的工具包",
                url="https://github.com/langchain-ai/langchain",
                description="用于开发由语言模型驱动的应用程序的框架，支持链、代理等模式",
                source="GitHub",
                category="开源项目",
                tags=["LLM", "框架", "代理"]
            ),
            NewsItem(
                title="Stable Diffusion WebUI: 图像生成工具",
                url="https://github.com/AUTOMATIC1111/stable-diffusion-webui",
                description="基于Stable Diffusion的Web界面，提供丰富的图像生成功能",
                source="GitHub",
                category="开源项目",
                tags=["图像生成", "WebUI", "Stable Diffusion"]
            )
        
            NewsItem(title="llama.cpp: 纯C/C++实现的LLM推理框架，支持边缘设备部署",
                     url="https://github.com/ggerganov/llama.cpp",
                     description="月星标增长15k，已支持数十种量化格式和架构，成为端侧AI推理的事实标准。",
                     source="GitHub", tags=["LLM", "推理"]),
            NewsItem(title="ComfyUI: 最受欢迎的AI图像生成工作流平台",
                     url="https://github.com/comfyanonymous/ComfyUI",
                     description="节点式Stable Diffusion工作流编辑器，插件生态繁荣，星标突破50k。",
                     source="GitHub", tags=["AI图像", "工作流"]),
            NewsItem(title="Ruff: 极速Python代码检查器，性能超越Flake8百倍",
                     url="https://github.com/astral-sh/ruff",
                     description="用Rust重写的Python代码检查工具，集成格式化功能，被主流编辑器广泛采用。",
                     source="GitHub", tags=["开发工具", "Python"]),
            NewsItem(title="ClickHouse: 开源实时分析数据库，性能全球领先",
                     url="https://github.com/ClickHouse/ClickHouse",
                     description="列式数据库在PB级数据分析场景持续领先，被Cloudflare、Uber等广泛使用。",
                     source="GitHub", tags=["数据库", "大数据"]),
            NewsItem(title="Kubernetes 2.0 规划发布，重构核心架构",
                     url="https://github.com/kubernetes/kubernetes",
                     description="K8s社区发布2.0版路线图，计划重构调度器、增强安全性和边缘场景支持。",
                     source="GitHub", tags=["云原生", "容器"]),
            NewsItem(title="Tauri 2.0: 跨平台桌面应用框架正式版发布",
                     url="https://github.com/tauri-apps/tauri",
                     description="用Rust+Web技术构建桌面应用，体积较Electron减少90%，性能更优。",
                     source="GitHub", tags=["桌面开发", "Rust"]),
            NewsItem(title="OpenTofu: Terraform开源替代品进入GA阶段",
                     url="https://github.com/opentofu/opentofu",
                     description="Linux基金会托管的开源Terraform分支，兼容现有代码库并新增安全特性。",
                     source="GitHub", tags=["基础设施", "DevOps"]),
]


